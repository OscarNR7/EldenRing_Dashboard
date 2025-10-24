from typing import List, Optional, Dict, Any, Generic, TypeVar, Type
from pymongo.collection import Collection
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId
from fastapi import HTTPException, status
import logging
import json
import ast

from app.database import MongoDB
from app.models.base import BaseDocument, PaginationParams

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseDocument)

class BaseService(Generic[T]):
    """
    Servicio base genérico con operaciones CRUD optimizadas.
    
    Características principales:
    - Normalización robusta de documentos MongoDB
    - Conversión segura de ObjectId a string
    - Parsing inteligente de campos anidados
    - Transformación de listas a diccionarios con mapeos
    - Manejo de errores con logging detallado
    - Soporte para Pydantic v2
    """
    
    def __init__(self, collection_name: str, model_class: Type[T]):
        """
        Args:
            collection_name: Nombre de la colección en MongoDB
            model_class: Clase del modelo Pydantic para validación
        """
        self.collection_name = collection_name
        self.model_class = model_class
        self._collection: Optional[Collection] = None
    
    @property
    def collection(self) -> Collection:
        """Lazy loading de la colección."""
        if self._collection is None:
            self._collection = MongoDB.get_collection(self.collection_name)
        return self._collection
    
    def _validate_object_id(self, item_id: str) -> ObjectId:
        """
        Valida y convierte string a ObjectId.
        
        Args:
            item_id: ID en formato string
            
        Returns:
            ObjectId válido
            
        Raises:
            HTTPException: Si el ID no es válido
        """
        if not ObjectId.is_valid(item_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ID inválido: {item_id}"
            )
        return ObjectId(item_id)
    
    def _clean_objectids(self, obj: Any) -> Any:
        """
        Recorre recursivamente dicts/lists y convierte cualquier ObjectId a str.
        
        Args:
            obj: Objeto a limpiar (dict, list, ObjectId, o primitivo)
            
        Returns:
            Objeto con ObjectIds convertidos a strings
        """
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: self._clean_objectids(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_objectids(i) for i in obj]
        else:
            return obj
    
    def _parse_json_field(self, value: Any) -> Any:
        """
        Parsea un campo que puede estar como JSON string.
        
        Intenta en orden:
        1. ast.literal_eval (comillas simples, más seguro)
        2. json.loads (comillas dobles)
        3. Retorna valor original si falla
        
        Args:
            value: Valor a parsear
            
        Returns:
            Valor parseado o original
        """
        if not isinstance(value, str):
            return value
        
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
    
    def _transform_list_to_dict(
        self, 
        items: List[Dict], 
        name_mapping: Dict[str, str],
        value_keys: List[str] = ['amount', 'scaling']
    ) -> Optional[Dict]:
        """
        Transforma lista de diccionarios con 'name' y 'amount'/'scaling' a diccionario plano.
        
        Ejemplo:
            Input: [{'name': 'Str', 'amount': 10}, {'name': 'Dex', 'amount': 15}]
            Output: {'strength': 10, 'dexterity': 15}
        
        Args:
            items: Lista de diccionarios
            name_mapping: Mapeo de nombres abreviados a completos
            value_keys: Claves posibles para el valor (en orden de prioridad)
            
        Returns:
            Diccionario normalizado o None si está vacío
        """
        if not items or not isinstance(items, list):
            return None
        
        result = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            
            # Obtener nombre
            name = item.get('name')
            if not name:
                continue
            
            # Obtener valor (intentar con cada clave en orden)
            value = None
            for key in value_keys:
                if key in item:
                    value = item[key]
                    break
            
            if value is not None:
                # Mapear nombre abreviado a completo
                mapped_name = name_mapping.get(name, name.lower())
                result[mapped_name] = value
        
        return result if result else None
    
    def _normalize_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza un documento de MongoDB antes de convertirlo a modelo Pydantic.
        
        Transformaciones aplicadas:
        - Convierte ObjectId a string
        - Parsea campos JSON guardados como strings
        - Transforma listas de diccionarios al formato esperado por los modelos
        - Aplica mapeos de abreviaturas
        
        Soporta:
        - Weapons: attack, defence, scalesWith, requiredAttributes
        - Armors: dmgNegation, resistance
        - Classes: stats (objeto anidado)
        - Bosses: drops (lista simple)
        - Spells: requires, cost, slots
        
        Args:
            document: Documento de MongoDB
            
        Returns:
            Documento normalizado
        """
        # ===========================
        # 1. CONVERTIR _id A STRING
        # ===========================
        if "_id" in document and isinstance(document["_id"], ObjectId):
            document["_id"] = str(document["_id"])
        
        # ===========================
        # 2. PARSEAR CAMPOS JSON
        # ===========================
        json_fields = [
            "attack", "defence", "scalesWith", "requiredAttributes",
            "dmgNegation", "resistance", "drops", "stats", "requires"
        ]
        
        for field in json_fields:
            if field in document and isinstance(document[field], str):
                document[field] = self._parse_json_field(document[field])
        
        # ===========================
        # 3. MAPEOS DE ABREVIATURAS
        # ===========================
        
        # Mapeo para stats de ataque/defensa
        attack_defense_mapping = {
            "Phy": "physical",
            "Mag": "magic",
            "Fire": "fire",
            "Ligt": "lightning",
            "Holy": "holy",
            "Crit": "critical",
            "Boost": "boost",
            "Strike": "strike",
            "Slash": "slash",
            "Pierce": "pierce"
        }
        
        # Mapeo para escalados y requerimientos
        scaling_requirement_mapping = {
            "Str": "strength",
            "Dex": "dexterity",
            "Int": "intelligence",
            "Fai": "faith",
            "Arc": "arcane",
            "Strength": "strength",
            "Dexterity": "dexterity",
            "Intelligence": "intelligence",
            "Faith": "faith",
            "Arcane": "arcane"
        }
        
        # Mapeo para resistencias
        resistance_mapping = {
            "Immunity": "immunity",
            "Robustness": "robustness",
            "Focus": "focus",
            "Vitality": "vitality",
            "Poise": "poise"
        }
        
        # ===========================
        # 4. TRANSFORMAR ATTACK (WEAPONS)
        # ===========================
        if "attack" in document and isinstance(document["attack"], list):
            document["attack"] = self._transform_list_to_dict(
                document["attack"], 
                attack_defense_mapping
            )
        
        # ===========================
        # 5. TRANSFORMAR DEFENCE (WEAPONS)
        # ===========================
        if "defence" in document and isinstance(document["defence"], list):
            document["defence"] = self._transform_list_to_dict(
                document["defence"], 
                attack_defense_mapping
            )
        
        # ===========================
        # 6. TRANSFORMAR SCALESWITH (WEAPONS)
        # ===========================
        if "scalesWith" in document and isinstance(document["scalesWith"], list):
            document["scalesWith"] = self._transform_list_to_dict(
                document["scalesWith"], 
                scaling_requirement_mapping,
                value_keys=['scaling', 'amount']  # Preferir 'scaling' primero
            )
        
        # ===========================
        # 7. TRANSFORMAR REQUIREDATTRIBUTES (WEAPONS)
        # ===========================
        if "requiredAttributes" in document and isinstance(document["requiredAttributes"], list):
            document["requiredAttributes"] = self._transform_list_to_dict(
                document["requiredAttributes"], 
                scaling_requirement_mapping
            )
        
        # ===========================
        # 8. TRANSFORMAR DMGNEGATION (ARMORS)
        # ===========================
        if "dmgNegation" in document and isinstance(document["dmgNegation"], list):
            document["dmgNegation"] = self._transform_list_to_dict(
                document["dmgNegation"], 
                attack_defense_mapping
            )
        
        # ===========================
        # 9. TRANSFORMAR RESISTANCE (ARMORS)
        # ===========================
        if "resistance" in document and isinstance(document["resistance"], list):
            document["resistance"] = self._transform_list_to_dict(
                document["resistance"], 
                resistance_mapping
            )
        
        # ===========================
        # 10. TRANSFORMAR REQUIRES (SPELLS)
        # ===========================
        if "requires" in document and isinstance(document["requires"], list):
            document["requires"] = self._transform_list_to_dict(
                document["requires"], 
                scaling_requirement_mapping
            )
        
        # ===========================
        # 11. CONVERTIR OBJECTIDS ANIDADOS
        # ===========================
        for key, value in document.items():
            if isinstance(value, ObjectId):
                document[key] = str(value)
            elif isinstance(value, list):
                document[key] = [
                    str(item) if isinstance(item, ObjectId) else item
                    for item in value
                ]
        
        return document
    
    def _document_to_model(self, document: Dict[str, Any]) -> T:
        """
        Convierte documento de MongoDB a modelo Pydantic.
        
        Incluye manejo robusto de errores con logging detallado.
        
        Args:
            document: Documento de MongoDB
            
        Returns:
            Instancia del modelo Pydantic
            
        Raises:
            Exception: Si la validación de Pydantic falla
        """
        try:
            document = self._normalize_document(document)
            return self.model_class(**document)
        except Exception as e:
            logger.error(f"Error convirtiendo documento a modelo {self.model_class.__name__}")
            logger.error(f"Documento: {document.get('name', document.get('_id', 'Sin identificador'))}")
            logger.error(f"Error específico: {str(e)}")
            
            # Log de campos problemáticos
            if hasattr(e, 'errors'):
                for error in e.errors():
                    logger.error(f"  Campo: {error.get('loc')}, Error: {error.get('msg')}")
            
            raise
    
    def _build_filter_query(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye query de MongoDB desde filtros.
        
        Maneja:
        - Búsqueda por nombre (regex case-insensitive)
        - Rangos numéricos (min_*, max_*)
        - Valores exactos
        
        Args:
            filters: Diccionario de filtros
            
        Returns:
            Query optimizada para MongoDB
        """
        query = {}
        
        for key, value in filters.items():
            if value is not None:
                if key == "name":
                    # Búsqueda case-insensitive
                    if isinstance(value, str):
                        query["name"] = {"$regex": value, "$options": "i"}
                    else:
                        query["name"] = value
                elif key.startswith("min_"):
                    # Rango mínimo
                    field = key.replace("min_", "")
                    query[field] = {"$gte": value}
                elif key.startswith("max_"):
                    # Rango máximo
                    field = key.replace("max_", "")
                    if field in query:
                        query[field]["$lte"] = value
                    else:
                        query[field] = {"$lte": value}
                else:
                    # Valor exacto
                    query[key] = value
        
        return query
    
    async def get_by_id(self, item_id: str) -> T:
        """
        Obtiene un documento por ID.
        
        Args:
            item_id: ID del documento
            
        Returns:
            Modelo Pydantic del documento
            
        Raises:
            HTTPException: Si no se encuentra o ID inválido
        """
        obj_id = self._validate_object_id(item_id)
        
        try:
            document = self.collection.find_one({"_id": obj_id})
            
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.collection_name} con ID {item_id} no encontrado"
                )
            
            return self._document_to_model(document)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo {self.collection_name} {item_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno: {str(e)}"
            )
    
    async def get_many(
        self,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
        projection: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Obtiene múltiples documentos con filtros y paginación.
        
        Args:
            filters: Filtros de búsqueda
            pagination: Parámetros de paginación
            projection: Campos a retornar (optimización)
            
        Returns:
            Dict con items, total, skip y limit
        """
        try:
            query = self._build_filter_query(filters or {})
            
            pagination = pagination or PaginationParams()
            
            sort_order = ASCENDING if pagination.sort_order == 1 else DESCENDING
            sort_by = pagination.sort_by or "_id"
            
            cursor = self.collection.find(query, projection)
            
            if sort_by:
                cursor = cursor.sort(sort_by, sort_order)
            
            cursor = cursor.skip(pagination.skip).limit(pagination.limit)
            
            documents = list(cursor)
            total = self.collection.count_documents(query)
            
            items = []
            for doc in documents:
                try:
                    items.append(self._document_to_model(doc))
                except Exception as e:
                    logger.warning(f"Omitiendo documento con error de validación: {e}")
                    continue
            
            return {
                "items": items,
                "total": total,
                "skip": pagination.skip,
                "limit": pagination.limit
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo lista de {self.collection_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener datos: {str(e)}"
            )
    
    async def create(self, item_data: T) -> T:
        """
        Crea un nuevo documento.
        
        Args:
            item_data: Modelo Pydantic con los datos
            
        Returns:
            Modelo con el ID asignado
        """
        try:
            document = item_data.model_dump(
                by_alias=True,
                exclude_none=False,
                exclude={"id"}
            )
            
            result = self.collection.insert_one(document)
            
            document["_id"] = str(result.inserted_id)
            
            return self._document_to_model(document)
            
        except Exception as e:
            logger.error(f"Error creando {self.collection_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear documento"
            )
    
    async def update(self, item_id: str, item_data: Dict[str, Any]) -> T:
        """
        Actualiza un documento existente (PATCH).
        
        Args:
            item_id: ID del documento
            item_data: Datos a actualizar
            
        Returns:
            Modelo actualizado
        """
        obj_id = self._validate_object_id(item_id)
        
        try:
            update_data = {k: v for k, v in item_data.items() if v is not None}
            
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No hay datos para actualizar"
                )
            
            result = self.collection.update_one(
                {"_id": obj_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.collection_name} con ID {item_id} no encontrado"
                )
            
            return await self.get_by_id(item_id)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error actualizando {self.collection_name} {item_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar documento"
            )
    
    async def delete(self, item_id: str) -> Dict[str, str]:
        """
        Elimina un documento.
        
        Args:
            item_id: ID del documento
            
        Returns:
            Mensaje de confirmación
        """
        obj_id = self._validate_object_id(item_id)
        
        try:
            result = self.collection.delete_one({"_id": obj_id})
            
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.collection_name} con ID {item_id} no encontrado"
                )
            
            return {"message": f"{self.collection_name} eliminado exitosamente"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error eliminando {self.collection_name} {item_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar documento"
            )
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Cuenta documentos que cumplen los filtros.
        
        Args:
            filters: Filtros de búsqueda
            
        Returns:
            Número de documentos
        """
        try:
            query = self._build_filter_query(filters or {})
            return self.collection.count_documents(query)
        except Exception as e:
            logger.error(f"Error contando {self.collection_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al contar documentos"
            )
    
    async def exists(self, item_id: str) -> bool:
        """
        Verifica si un documento existe.
        
        Args:
            item_id: ID del documento
            
        Returns:
            True si existe, False si no
        """
        obj_id = self._validate_object_id(item_id)
        
        try:
            count = self.collection.count_documents({"_id": obj_id}, limit=1)
            return count > 0
        except Exception as e:
            logger.error(f"Error verificando existencia de {item_id}: {e}")
            return False
    
    async def bulk_create(self, items: List[T]) -> Dict[str, Any]:
        """
        Crea múltiples documentos en una sola operación.
        
        Args:
            items: Lista de modelos a crear
            
        Returns:
            Estadísticas de la operación
        """
        if not items:
            return {"inserted": 0, "ids": []}
        
        try:
            documents = [
                item.model_dump(by_alias=True, exclude_none=False, exclude={"id"}) 
                for item in items
            ]
            
            result = self.collection.insert_many(documents, ordered=False)
            
            return {
                "inserted": len(result.inserted_ids),
                "ids": [str(id) for id in result.inserted_ids]
            }
            
        except Exception as e:
            logger.error(f"Error en bulk_create de {self.collection_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en creación masiva"
            )
    
    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ejecuta un pipeline de agregación de MongoDB.
        
        Args:
            pipeline: Pipeline de agregación de MongoDB
            
        Returns:
            Resultados de la agregación con ObjectIds limpiados
        """
        try:
            results = list(self.collection.aggregate(pipeline))
            cleaned_results = [self._clean_objectids(result) for result in results]
            return cleaned_results
        except Exception as e:
            logger.error(f"Error en agregación de {self.collection_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en agregación"
            )