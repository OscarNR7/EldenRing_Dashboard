from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import logging

from app.services.base_service import BaseService
from app.models.weapons import (
    WeaponResponse,
    WeaponCreate,
    WeaponUpdate,
    WeaponFilterParams,
    WeaponStatsComparison
)
from app.models.base import PaginationParams

logger = logging.getLogger(__name__)

class WeaponService(BaseService[WeaponResponse]):
    """
    Servicio especializado para armas con análisis y optimizaciones.
    """
    
    def __init__(self):
        super().__init__("weapons", WeaponResponse)
    
    def _build_weapon_filter_query(self, filters: WeaponFilterParams) -> Dict[str, Any]:
        """
        Construye query específica para armas con filtros avanzados.
        
        Args:
            filters: Parámetros de filtrado de armas
            
        Returns:
            Query de MongoDB optimizada
        """
        query = {}
        
        if filters.name:
            query["name"] = {"$regex": filters.name, "$options": "i"}
        
        if filters.category:
            query["category"] = filters.category
        
        if filters.min_weight is not None:
            query["weight"] = {"$gte": filters.min_weight}
        
        if filters.max_weight is not None:
            if "weight" in query:
                query["weight"]["$lte"] = filters.max_weight
            else:
                query["weight"] = {"$lte": filters.max_weight}
        
        if filters.min_damage is not None:
            query["attack.physical"] = {"$gte": filters.min_damage}
        
        if filters.max_damage is not None:
            if "attack.physical" in query:
                query["attack.physical"]["$lte"] = filters.max_damage
            else:
                query["attack.physical"] = {"$lte": filters.max_damage}
        
        if filters.min_strength is not None:
            query["requiredAttributes.strength"] = {"$gte": filters.min_strength}
        
        if filters.max_strength is not None:
            if "requiredAttributes.strength" in query:
                query["requiredAttributes.strength"]["$lte"] = filters.max_strength
            else:
                query["requiredAttributes.strength"] = {"$lte": filters.max_strength}
        
        if filters.min_dexterity is not None:
            query["requiredAttributes.dexterity"] = {"$gte": filters.min_dexterity}
        
        if filters.max_dexterity is not None:
            if "requiredAttributes.dexterity" in query:
                query["requiredAttributes.dexterity"]["$lte"] = filters.max_dexterity
            else:
                query["requiredAttributes.dexterity"] = {"$lte": filters.max_dexterity}
        
        if filters.scaling_grade:
            scaling_grades = ['E', 'D', 'C', 'B', 'A', 'S']
            min_index = scaling_grades.index(filters.scaling_grade)
            valid_grades = scaling_grades[min_index:]
            
            query["$or"] = [
                {"scalesWith.strength": {"$in": valid_grades}},
                {"scalesWith.dexterity": {"$in": valid_grades}},
                {"scalesWith.intelligence": {"$in": valid_grades}},
                {"scalesWith.faith": {"$in": valid_grades}},
                {"scalesWith.arcane": {"$in": valid_grades}}
            ]
        
        if filters.has_passive is not None:
            if filters.has_passive:
                query["passive"] = {"$exists": True, "$ne": None}
            else:
                query["$or"] = [
                    {"passive": {"$exists": False}},
                    {"passive": None}
                ]
        
        return query
    
    async def get_weapons(
        self,
        filters: Optional[WeaponFilterParams] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Dict[str, Any]:
        """
        Obtiene armas con filtros específicos.
        
        Args:
            filters: Filtros de armas
            pagination: Paginación
            
        Returns:
            Lista de armas con metadatos
        """
        try:
            filters = filters or WeaponFilterParams()
            pagination = pagination or PaginationParams()
            
            # Convertir filtros a dict para _build_weapon_filter_query
            query = self._build_weapon_filter_query(filters)
            
            # Pasar query como dict de filtros, no como query directa
            return await self.get_many(filters=query, pagination=pagination)
            
        except Exception as e:
            logger.error(f"Error obteniendo armas: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener armas"
            )
    
    async def get_by_category(self, category: str) -> List[WeaponResponse]:
        """
        Obtiene todas las armas de una categoría.
        Optimizado con índice en category.
        
        Args:
            category: Categoría de arma
            
        Returns:
            Lista de armas
        """
        try:
            query = {"category": category}
            
            documents = list(self.collection.find(query))
            
            return [self._document_to_model(doc) for doc in documents]
            
        except Exception as e:
            logger.error(f"Error obteniendo armas por categoría {category}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener armas por categoría"
            )
    
    async def get_best_damage_to_weight(
        self,
        limit: int = 10,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene armas con mejor relación daño/peso.
        Usa agregación de MongoDB para cálculos eficientes.
        
        Args:
            limit: Número de armas a retornar
            category: Filtrar por categoría (opcional)
            
        Returns:
            Lista de armas ordenadas por ratio daño/peso
        """
        try:
            match_stage = {
                "weight": {"$gt": 0, "$ne": None},
                "attack.physical": {"$gt": 0, "$ne": None}
            }
            
            if category:
                match_stage["category"] = category
            
            pipeline = [
                {"$match": match_stage},
                {
                    "$addFields": {
                        "damageToWeightRatio": {
                            "$divide": ["$attack.physical", "$weight"]
                        }
                    }
                },
                {"$sort": {"damageToWeightRatio": -1}},
                {"$limit": limit},
                {
                    "$project": {
                        "name": 1,
                        "category": 1,
                        "weight": 1,
                        "attack": 1,
                        "damageToWeightRatio": 1,
                        "image": 1
                    }
                }
            ]
            
            return await self.aggregate(pipeline)
            
        except Exception as e:
            logger.error(f"Error calculando mejor ratio daño/peso: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en análisis de armas"
            )
    
    async def compare_weapons(
        self,
        comparison: WeaponStatsComparison
    ) -> Dict[str, Any]:
        """
        Compara estadísticas entre múltiples armas.
        
        Args:
            comparison: Parámetros de comparación
            
        Returns:
            Análisis comparativo completo
        """
        try:
            from bson import ObjectId
            
            weapon_ids = [
                self._validate_object_id(wid) for wid in comparison.weapon_ids
            ]
            
            weapons = list(self.collection.find({"_id": {"$in": weapon_ids}}))
            
            if len(weapons) != len(weapon_ids):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Una o más armas no encontradas"
                )
            
            weapons_models = [self._document_to_model(w) for w in weapons]
            
            comparison_data = {
                "weapons": weapons_models,
                "stats_comparison": {
                    "damage": {
                        w.name: w.attack.physical if w.attack else 0 
                        for w in weapons_models
                    },
                    "weight": {w.name: w.weight for w in weapons_models},
                    "damage_to_weight_ratio": {
                        w.name: w.damage_to_weight_ratio 
                        for w in weapons_models
                    }
                },
                "winner_by_damage": max(
                    weapons_models,
                    key=lambda w: w.attack.physical if w.attack and w.attack.physical else 0
                ).name,
                "winner_by_ratio": max(
                    weapons_models,
                    key=lambda w: w.damage_to_weight_ratio or 0
                ).name,
                "lightest": min(
                    weapons_models,
                    key=lambda w: w.weight or float('inf')
                ).name
            }
            
            return comparison_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error comparando armas: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en comparación de armas"
            )
    
    async def get_by_build_type(self, build_type: str) -> List[WeaponResponse]:
        """
        Recomienda armas para un tipo de build específico.
        
        Args:
            build_type: Tipo de build (strength, dexterity, quality, int, faith)
            
        Returns:
            Armas recomendadas
        """
        try:
            build_type = build_type.lower()
            
            scaling_map = {
                "strength": ["A", "S"],
                "dexterity": ["A", "S"],
                "quality": ["B", "A", "S"],
                "intelligence": ["A", "S"],
                "faith": ["A", "S"],
                "arcane": ["A", "S"]
            }
            
            if build_type not in scaling_map:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Build type inválido. Opciones: {', '.join(scaling_map.keys())}"
                )
            
            grades = scaling_map[build_type]
            
            if build_type == "quality":
                query = {
                    "$or": [
                        {"scalesWith.strength": {"$in": grades}},
                        {"scalesWith.dexterity": {"$in": grades}}
                    ]
                }
            else:
                query = {f"scalesWith.{build_type}": {"$in": grades}}
            
            documents = list(self.collection.find(query).limit(20))
            
            return [self._document_to_model(doc) for doc in documents]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo armas para build {build_type}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener armas por build"
            )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de armas.
        Usa agregación para cálculos eficientes.
        
        Returns:
            Estadísticas agregadas
        """
        try:
            pipeline = [
                {
                    "$facet": {
                        "by_category": [
                            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                            {"$sort": {"count": -1}}
                        ],
                        "avg_stats": [
                            {
                                "$group": {
                                    "_id": None,
                                    "avg_weight": {"$avg": "$weight"},
                                    "avg_physical_damage": {"$avg": "$attack.physical"},
                                    "total_weapons": {"$sum": 1}
                                }
                            }
                        ],
                        "top_damage": [
                            {"$sort": {"attack.physical": -1}},
                            {"$limit": 5},
                            {
                                "$project": {
                                    "name": 1,
                                    "category": 1,
                                    "damage": "$attack.physical"
                                }
                            }
                        ]
                    }
                }
            ]
            
            results = await self.aggregate(pipeline)
            
            if results:
                return results[0]
            
            return {}
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de armas: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al calcular estadísticas"
            )

weapon_service = WeaponService()