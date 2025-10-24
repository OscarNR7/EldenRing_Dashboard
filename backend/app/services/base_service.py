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
    def _clean_objectids(self, obj):
        """
        Recorre recursivamente dicts/lists y convierte cualquier ObjectId a str.
        """
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: self._clean_objectids(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_objectids(i) for i in obj]
        else:
            return obj
    """
    Servicio base genérico con operaciones CRUD optimizadas.
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
        """
        if not ObjectId.is_valid(item_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ID inválido: {item_id}"
            )
        return ObjectId(item_id)
    
    def _parse_json_field(self, value: Any) -> Any:
        """
        Parsea un campo que puede estar como JSON string.
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
    
    def _transform_list_to_dict(self, items: List[Dict], name_mapping: Dict[str, str]) -> Dict:
        """
        Transforma lista de diccionarios con 'name' y 'amount'/'scaling' a diccionario plano.
        
        Args:
            items: Lista de diccionarios [{name: "Str", amount: 10}, ...]
            name_mapping: Mapeo de nombres abreviados a completos
        
        Returns:
            Diccionario normalizado {strength: 10, ...}
        """
        if not items:
            return {}
        
        result = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            
            # Obtener nombre y valor
            name = item.get("name")
            value = item.get("amount") or item.get("scaling")
            
            if name and value is not None:
                # Mapear nombre abreviado a completo
                mapped_name = name_mapping.get(name, name.lower())
                result[mapped_name] = value
        
        return result if result else None
    
    def _normalize_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza un documento de MongoDB antes de convertirlo a modelo Pydantic.
        
        Maneja:
        - Conversión de ObjectId a string
        - Parsing de campos JSON guardados como strings
        - Transformación de listas a diccionarios según formato esperado
        """
        # Convertir _id a string
        if "_id" in document and isinstance(document["_id"], ObjectId):
            document["_id"] = str(document["_id"])
        
        # Parsear campos que pueden estar como strings
        json_fields = ["attack", "defence", "scalesWith", "requiredAttributes", 
                      "dmgNegation", "resistance", "drops", "stats"]
        
        for field in json_fields:
            if field in document and isinstance(document[field], str):
                document[field] = self._parse_json_field(document[field])
        
        # Mapeos de nombres abreviados
        attack_mapping = {
            "Phy": "physical",
            "Mag": "magic",
            "Fire": "fire",
            "Ligt": "lightning",
            "Holy": "holy",
            "Crit": "critical"
        }
        
        defense_mapping = {
            "Phy": "physical",
            "Strike": "strike",
            "Slash": "slash",
            "Pierce": "pierce",
            "Mag": "magic",
            "Fire": "fire",
            "Ligt": "lightning",
            "Holy": "holy",
            "Boost": "boost"
        }
        
        scaling_mapping = {
            "Str": "strength",
            "Dex": "dexterity",
            "Int": "intelligence",
            "Fai": "faith",
            "Arc": "arcane"
        }
        
        resistance_mapping = {
            "Immunity": "immunity",
            "Robustness": "robustness",
            "Focus": "focus",
            "Vitality": "vitality",
            "Poise": "poise"
        }
        
        # Transformar 'attack' de lista a diccionario
        if "attack" in document and isinstance(document["attack"], list):
            document["attack"] = self._transform_list_to_dict(
                document["attack"], 
                attack_mapping
            )
        
        # Transformar 'defence' de lista a diccionario
        if "defence" in document and isinstance(document["defence"], list):
            document["defence"] = self._transform_list_to_dict(
                document["defence"], 
                defense_mapping
            )
        
        # Transformar 'scalesWith' de lista a diccionario
        if "scalesWith" in document and isinstance(document["scalesWith"], list):
            document["scalesWith"] = self._transform_list_to_dict(
                document["scalesWith"], 
                scaling_mapping
            )
        
        # Transformar 'requiredAttributes' de lista a diccionario
        if "requiredAttributes" in document and isinstance(document["requiredAttributes"], list):
            document["requiredAttributes"] = self._transform_list_to_dict(
                document["requiredAttributes"], 
                scaling_mapping
            )
        
        # Transformar 'dmgNegation' de lista a diccionario
        if "dmgNegation" in document and isinstance(document["dmgNegation"], list):
            document["dmgNegation"] = self._transform_list_to_dict(
                document["dmgNegation"], 
                defense_mapping
            )
        
        # Transformar 'resistance' de lista a diccionario
        if "resistance" in document and isinstance(document["resistance"], list):
            document["resistance"] = self._transform_list_to_dict(
                document["resistance"], 
                resistance_mapping
            )
        
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
        
        Incluye manejo robusto de errores con logging detallado.
        """
        try:
            document = self._normalize_document(document)
            return self.model_class(**document)
        except Exception as e:
            logger.error(f"Error convirtiendo documento a modelo: {e}")
            logger.error(f"Documento problemático: {document.get('name', 'Sin nombre')}")
            logger.error(f"Campos problemáticos: {e}")
            raise
    
    def _build_filter_query(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye query de MongoDB desde filtros.
        """
        query = {}
        
        for key, value in filters.items():
            if value is not None:
                if key == "name":
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
                    logger.warning(f"Omitiendo documento con error: {e}")
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
        Ejecuta un pipeline de agregación de MongoDB y normaliza todos los ObjectId y campos anidados.
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