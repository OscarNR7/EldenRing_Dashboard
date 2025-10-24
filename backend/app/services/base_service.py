from typing import List, Optional, Dict, Any, Generic, TypeVar, Type
from pymongo.collection import Collection
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId
from fastapi import HTTPException, status
import logging
from functools import lru_cache

from app.database import MongoDB
from app.models.base import BaseDocument, PaginationParams

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseDocument)

class BaseService(Generic[T]):
    """
    Servicio base genérico con operaciones CRUD optimizadas.
    Implementa patrones de rendimiento y cacheo cuando es apropiado.
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
    
    def _normalize_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza un documento de MongoDB antes de convertirlo a modelo Pydantic.
        - Convierte ObjectId a string
        - Parsea campos JSON guardados como strings
        - Transforma listas de diccionarios al formato esperado por los modelos
        
        Args:
            document: Documento de MongoDB
            
        Returns:
            Documento normalizado
        """
        import json
        import ast
        
        if "_id" in document and isinstance(document["_id"], ObjectId):
            document["_id"] = str(document["_id"])
        
        # Parsear campos que pueden estar como strings
        string_fields = ["attack", "defence", "scalesWith", "requiredAttributes", "dmgNegation", "resistance", "drops"]
        
        for field in string_fields:
            if field in document and isinstance(document[field], str):
                try:
                    # Intentar parsear como Python literal (para listas con comillas simples)
                    document[field] = ast.literal_eval(document[field])
                except (ValueError, SyntaxError):
                    try:
                        # Intentar parsear como JSON
                        document[field] = json.loads(document[field])
                    except (json.JSONDecodeError, TypeError):
                        pass
        
        # Transformar 'attack' de lista a objeto AttackStats
        if "attack" in document and isinstance(document["attack"], list):
            attack_dict = {}
            for item in document["attack"]:
                if isinstance(item, dict) and "name" in item and "amount" in item:
                    name_map = {
                        "Phy": "physical",
                        "Mag": "magic",
                        "Fire": "fire",
                        "Ligt": "lightning",
                        "Holy": "holy",
                        "Crit": "critical"
                    }
                    mapped_name = name_map.get(item["name"], item["name"].lower())
                    attack_dict[mapped_name] = item["amount"]
            document["attack"] = attack_dict if attack_dict else None
        
        # Transformar 'defence' de lista a diccionario simple
        if "defence" in document and isinstance(document["defence"], list):
            defence_dict = {}
            for item in document["defence"]:
                if isinstance(item, dict) and "name" in item and "amount" in item:
                    name_map = {
                        "Phy": "physical",
                        "Mag": "magic",
                        "Fire": "fire",
                        "Ligt": "lightning",
                        "Holy": "holy",
                        "Boost": "boost"
                    }
                    mapped_name = name_map.get(item["name"], item["name"].lower())
                    defence_dict[mapped_name] = item["amount"]
            document["defence"] = defence_dict if defence_dict else None
        
        # Transformar 'scalesWith' de lista a objeto ScalingStats
        if "scalesWith" in document and isinstance(document["scalesWith"], list):
            scaling_dict = {}
            for item in document["scalesWith"]:
                if isinstance(item, dict) and "name" in item and "scaling" in item:
                    name_map = {
                        "Str": "strength",
                        "Dex": "dexterity",
                        "Int": "intelligence",
                        "Fai": "faith",
                        "Arc": "arcane"
                    }
                    mapped_name = name_map.get(item["name"], item["name"].lower())
                    scaling_dict[mapped_name] = item["scaling"]
            document["scalesWith"] = scaling_dict if scaling_dict else None
        
        # Transformar 'requiredAttributes' de lista a objeto RequirementStats
        if "requiredAttributes" in document and isinstance(document["requiredAttributes"], list):
            req_dict = {}
            for item in document["requiredAttributes"]:
                if isinstance(item, dict) and "name" in item and "amount" in item:
                    name_map = {
                        "Str": "strength",
                        "Dex": "dexterity",
                        "Int": "intelligence",
                        "Fai": "faith",
                        "Arc": "arcane"
                    }
                    mapped_name = name_map.get(item["name"], item["name"].lower())
                    req_dict[mapped_name] = item["amount"]
            document["requiredAttributes"] = req_dict if req_dict else None
        
        # Transformar 'dmgNegation' de lista a objeto DefenseStats (para armaduras)
        if "dmgNegation" in document and isinstance(document["dmgNegation"], list):
            defense_dict = {}
            for item in document["dmgNegation"]:
                if isinstance(item, dict) and "name" in item and "amount" in item:
                    name_map = {
                        "Phy": "physical",
                        "Strike": "strike",
                        "Slash": "slash",
                        "Pierce": "pierce",
                        "Mag": "magic",
                        "Fire": "fire",
                        "Ligt": "lightning",
                        "Holy": "holy"
                    }
                    mapped_name = name_map.get(item["name"], item["name"].lower())
                    defense_dict[mapped_name] = item["amount"]
            document["dmgNegation"] = defense_dict if defense_dict else None
        
        # Transformar 'resistance' de lista a objeto ResistanceStats (para armaduras)
        if "resistance" in document and isinstance(document["resistance"], list):
            resistance_dict = {}
            for item in document["resistance"]:
                if isinstance(item, dict) and "name" in item and "amount" in item:
                    name_map = {
                        "Immunity": "immunity",
                        "Robustness": "robustness",
                        "Focus": "focus",
                        "Vitality": "vitality",
                        "Poise": "poise"
                    }
                    mapped_name = name_map.get(item["name"], item["name"].lower())
                    resistance_dict[mapped_name] = item["amount"]
            document["resistance"] = resistance_dict if resistance_dict else None
        
        # Convertir otros ObjectIds anidados
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
        
        Args:
            document: Documento de MongoDB
            
        Returns:
            Instancia del modelo Pydantic
        """
        document = self._normalize_document(document)
        return self.model_class(**document)
    
    def _build_filter_query(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye query de MongoDB desde filtros.
        Elimina valores None y prepara operadores.
        
        Args:
            filters: Diccionario de filtros
            
        Returns:
            Query optimizada para MongoDB
        """
        query = {}
        
        for key, value in filters.items():
            if value is not None:
                if key == "name":
                    # Asegurar que value es string para evitar error de $regex
                    if isinstance(value, str):
                        query["name"] = {"$regex": value, "$options": "i"}
                    else:
                        query["name"] = value
                elif key.startswith("min_"):
                    field = key.replace("min_", "")
                    query[field] = {"$gte": value}
                elif key.startswith("max_"):
                    field = key.replace("max_", "")
                    if field in query:
                        query[field]["$lte"] = value
                    else:
                        query[field] = {"$lte": value}
                else:
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
                detail="Error interno del servidor"
            )
    
    async def get_many(
        self,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
        projection: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Obtiene múltiples documentos con filtros y paginación.
        Optimizado con proyección para reducir datos transferidos.
        
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
            
            items = [self._document_to_model(doc) for doc in documents]
            
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
                detail="Error al obtener datos"
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
            document = item_data.model_dump_mongo(exclude={"id"})
            
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
        Más eficiente que get_by_id cuando solo necesitas saber si existe.
        
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
        Optimizado para inserciones masivas.
        
        Args:
            items: Lista de modelos a crear
            
        Returns:
            Estadísticas de la operación
        """
        if not items:
            return {"inserted": 0, "ids": []}
        
        try:
            documents = [item.model_dump_mongo(exclude={"id"}) for item in items]
            
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
        Para análisis y estadísticas complejas.
        
        Args:
            pipeline: Pipeline de agregación de MongoDB
            
        Returns:
            Resultados de la agregación
        """
        try:
            results = list(self.collection.aggregate(pipeline))
            
            for result in results:
                if "_id" in result and isinstance(result["_id"], ObjectId):
                    result["_id"] = str(result["_id"])
            
            return results
            
        except Exception as e:
            logger.error(f"Error en agregación de {self.collection_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en agregación"
            )