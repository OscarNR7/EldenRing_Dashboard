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
    
    def _document_to_model(self, document: Dict[str, Any]) -> T:
        """
        Convierte documento de MongoDB a modelo Pydantic.
        
        Args:
            document: Documento de MongoDB
            
        Returns:
            Instancia del modelo Pydantic
        """
        if "_id" in document:
            document["_id"] = str(document["_id"])
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
                    query["name"] = {"$regex": value, "$options": "i"}
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