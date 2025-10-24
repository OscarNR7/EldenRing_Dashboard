from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import logging

from app.services.base_service import BaseService
from app.models.armors import (
    ArmorResponse,
    ArmorCreate,
    ArmorUpdate,
    ArmorFilterParams,
    ArmorSetResponse,
    ArmorOptimizationRequest
)
from app.models.base import PaginationParams

logger = logging.getLogger(__name__)

class ArmorService(BaseService[ArmorResponse]):
    """
    Servicio especializado para armaduras con optimización de sets.
    """
    
    def __init__(self):
        super().__init__("armor", ArmorResponse)
    
    def _build_armor_filter_query(self, filters: ArmorFilterParams) -> Dict[str, Any]:
        """
        Construye query específica para armaduras, utilizando el filtro base
        y añadiendo lógica específica para armaduras.
        
        Args:
            filters: Filtros de armaduras
            
        Returns:
            Query de MongoDB
        """
        # Usar el constructor de filtros base para manejar 'name', 'min_weight', 'max_weight', etc.
        base_query = super()._build_filter_query(filters.model_dump(exclude_unset=True))
        query = base_query
        
        # Lógica específica para 'category' y 'armor_slot'
        # Si armor_slot está presente, tiene prioridad y se usa para filtrar la categoría
        if filters.armor_slot:
            query["category"] = {"$regex": filters.armor_slot, "$options": "i"}
        elif filters.category:
            query["category"] = {"$regex": filters.category, "$options": "i"}
        
        # Filtros de defensa
        if filters.min_physical_defense is not None:
            query["dmgNegation.physical"] = {"$gte": filters.min_physical_defense}
        if filters.max_physical_defense is not None:
            if "dmgNegation.physical" in query:
                query["dmgNegation.physical"]["$lte"] = filters.max_physical_defense
            else:
                query["dmgNegation.physical"] = {"$lte": filters.max_physical_defense}
        
        if filters.min_magic_defense is not None:
            query["dmgNegation.magic"] = {"$gte": filters.min_magic_defense}
        if filters.max_magic_defense is not None:
            if "dmgNegation.magic" in query:
                query["dmgNegation.magic"]["$lte"] = filters.max_magic_defense
            else:
                query["dmgNegation.magic"] = {"$lte": filters.max_magic_defense}
        
        # Filtros de resistencia
        if filters.min_poise is not None:
            query["resistance.poise"] = {"$gte": filters.min_poise}
        if filters.min_immunity is not None:
            query["resistance.immunity"] = {"$gte": filters.min_immunity}
        
        return query
    
    async def get_armors(
        self,
        filters: Optional[ArmorFilterParams] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Dict[str, Any]:
        """
        Obtiene armaduras con filtros específicos.
        
        Args:
            filters: Filtros de armaduras
            pagination: Paginación
            
        Returns:
            Lista de armaduras con metadatos
        """
        try:
            filters = filters or ArmorFilterParams()
            pagination = pagination or PaginationParams()
            
            query = self._build_armor_filter_query(filters)
            
            return await self.get_many(query, pagination)
            
        except Exception as e:
            logger.error(f"Error obteniendo armaduras: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener armaduras"
            )
    
    async def get_by_slot(self, slot: str) -> List[ArmorResponse]:
        """
        Obtiene armaduras por slot específico.
        
        Args:
            slot: Slot de armadura (Head, Chest, Arms, Legs)
            
        Returns:
            Lista de armaduras del slot
        """
        try:
            valid_slots = ["Head", "Chest", "Arms", "Legs", "Helm", "Armor", "Gauntlets", "Leg Armor"]
            
            if slot not in valid_slots:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Slot inválido. Opciones: {', '.join(valid_slots)}"
                )
            
            query = {"category": slot}
            documents = list(self.collection.find(query))
            
            return [self._document_to_model(doc) for doc in documents]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo armaduras por slot {slot}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener armaduras por slot"
            )
    
    async def get_best_defense_to_weight(
        self,
        limit: int = 10,
        slot: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene armaduras con mejor relación defensa/peso.
        
        Args:
            limit: Número de armaduras a retornar
            slot: Filtrar por slot (opcional)
            
        Returns:
            Lista ordenada por ratio defensa/peso
        """
        try:
            match_stage = {
                "weight": {"$gt": 0, "$ne": None},
                "dmgNegation.physical": {"$exists": True, "$ne": None}
            }
            
            if slot:
                match_stage["category"] = slot
            
            pipeline = [
                {"$match": match_stage},
                {
                    "$addFields": {
                        "defenseToWeightRatio": {
                            "$divide": ["$dmgNegation.physical", "$weight"]
                        }
                    }
                },
                {"$sort": {"defenseToWeightRatio": -1}},
                {"$limit": limit},
                {
                    "$project": {
                        "name": 1,
                        "category": 1,
                        "weight": 1,
                        "dmgNegation": 1,
                        "resistance": 1,
                        "defenseToWeightRatio": 1,
                        "image": 1
                    }
                }
            ]
            
            return await self.aggregate(pipeline)
            
        except Exception as e:
            logger.error(f"Error calculando mejor ratio defensa/peso: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en análisis de armaduras"
            )
    
    async def optimize_armor_set(
        self,
        optimization: ArmorOptimizationRequest
    ) -> Dict[str, Any]:
        """
        Optimiza un set completo de armadura según criterios.
        Algoritmo que maximiza la stat deseada dentro del peso límite.
        
        Args:
            optimization: Parámetros de optimización
            
        Returns:
            Set optimizado con estadísticas
        """
        try:
            slots = ["Head", "Chest", "Arms", "Legs", "Helm", "Armor", "Gauntlets", "Leg Armor"]
            
            slot_mapping = {
                "Head": ["Head", "Helm"],
                "Chest": ["Chest", "Armor"],
                "Arms": ["Arms", "Gauntlets"],
                "Legs": ["Legs", "Leg Armor"]
            }
            
            optimized_set = {}
            total_weight = 0
            
            stat_field_map = {
                "physical": "dmgNegation.physical",
                "magic": "dmgNegation.magic",
                "fire": "dmgNegation.fire",
                "lightning": "dmgNegation.lightning",
                "holy": "dmgNegation.holy",
                "poise": "resistance.poise"
            }
            
            prioritize_field = stat_field_map.get(optimization.prioritize, "dmgNegation.physical")
            
            for main_slot, alt_slots in slot_mapping.items():
                query = {
                    "category": {"$in": alt_slots},
                    "weight": {"$lte": optimization.max_weight - total_weight},
                    prioritize_field: {"$exists": True, "$ne": None}
                }
                
                if optimization.required_poise is not None and optimization.prioritize != "poise":
                    query["resistance.poise"] = {"$gte": optimization.required_poise / 4}
                
                pieces = list(
                    self.collection.find(query)
                    .sort(prioritize_field, -1)
                    .limit(5)
                )
                
                if pieces:
                    best_piece = pieces[0]
                    optimized_set[main_slot.lower()] = self._document_to_model(best_piece)
                    total_weight += best_piece.get("weight", 0)
            
            total_stats = {
                "physical_defense": 0,
                "magic_defense": 0,
                "fire_defense": 0,
                "lightning_defense": 0,
                "holy_defense": 0,
                "poise": 0,
                "immunity": 0,
                "robustness": 0,
                "focus": 0,
                "vitality": 0
            }
            
            for piece in optimized_set.values():
                if piece.dmgNegation:
                    total_stats["physical_defense"] += piece.dmgNegation.physical or 0
                    total_stats["magic_defense"] += piece.dmgNegation.magic or 0
                    total_stats["fire_defense"] += piece.dmgNegation.fire or 0
                    total_stats["lightning_defense"] += piece.dmgNegation.lightning or 0
                    total_stats["holy_defense"] += piece.dmgNegation.holy or 0
                
                if piece.resistance:
                    total_stats["poise"] += piece.resistance.poise or 0
                    total_stats["immunity"] += piece.resistance.immunity or 0
                    total_stats["robustness"] += piece.resistance.robustness or 0
                    total_stats["focus"] += piece.resistance.focus or 0
                    total_stats["vitality"] += piece.resistance.vitality or 0
            
            return {
                "optimized_set": optimized_set,
                "total_weight": round(total_weight, 2),
                "weight_percentage": round((total_weight / optimization.max_weight) * 100, 2),
                "total_stats": total_stats,
                "optimization_criteria": optimization.prioritize,
                "meets_poise_requirement": (
                    total_stats["poise"] >= optimization.required_poise
                    if optimization.required_poise
                    else None
                )
            }
            
        except Exception as e:
            logger.error(f"Error optimizando set de armadura: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al optimizar armadura"
            )
    
    async def find_armor_sets(self) -> List[ArmorSetResponse]:
        """
        Identifica sets completos de armadura basándose en nombres similares.
        
        Returns:
            Lista de sets identificados
        """
        try:
            pipeline = [
                {
                    "$project": {
                        "name": 1,
                        "category": 1,
                        "weight": 1,
                        "dmgNegation": 1,
                        "resistance": 1,
                        "set_name": {
                            "$arrayElemAt": [
                                {"$split": ["$name", " "]},
                                0
                            ]
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$set_name",
                        "pieces": {"$push": "$$ROOT"},
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$match": {
                        "count": {"$gte": 3}
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": 20}
            ]
            
            results = await self.aggregate(pipeline)
            
            sets = []
            for result in results:
                pieces = {p["category"]: self._document_to_model(p) for p in result["pieces"]}
                
                set_response = ArmorSetResponse(
                    set_name=result["_id"],
                    helm=pieces.get("Head") or pieces.get("Helm"),
                    chest=pieces.get("Chest") or pieces.get("Armor"),
                    gauntlets=pieces.get("Arms") or pieces.get("Gauntlets"),
                    legs=pieces.get("Legs") or pieces.get("Leg Armor")
                )
                
                sets.append(set_response)
            
            return sets
            
        except Exception as e:
            logger.error(f"Error identificando sets de armadura: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al identificar sets"
            )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de armaduras.
        
        Returns:
            Estadísticas agregadas
        """
        try:
            pipeline = [
                {
                    "$facet": {
                        "by_slot": [
                            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                            {"$sort": {"count": -1}}
                        ],
                        "avg_stats": [
                            {
                                "$group": {
                                    "_id": None,
                                    "avg_weight": {"$avg": "$weight"},
                                    "avg_physical_defense": {"$avg": "$dmgNegation.physical"},
                                    "avg_poise": {"$avg": "$resistance.poise"},
                                    "total_armors": {"$sum": 1}
                                }
                            }
                        ],
                        "heaviest": [
                            {"$sort": {"weight": -1}},
                            {"$limit": 5},
                            {"$project": {"name": 1, "category": 1, "weight": 1}}
                        ],
                        "lightest": [
                            {"$match": {"weight": {"$gt": 0}}},
                            {"$sort": {"weight": 1}},
                            {"$limit": 5},
                            {"$project": {"name": 1, "category": 1, "weight": 1}}
                        ]
                    }
                }
            ]
            
            results = await self.aggregate(pipeline)
            
            if results:
                return results[0]
            
            return {}
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de armaduras: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al calcular estadísticas"
            )

armor_service = ArmorService()