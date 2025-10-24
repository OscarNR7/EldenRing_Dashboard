from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import logging

from app.services.base_service import BaseService
from app.models.bosses import (
    BossResponse,
    BossCreate,
    BossUpdate,
    BossFilterParams,
    BossStatistics,
    BossByRegionResponse,
    BossDropAnalysis,
    BossByTierResponse,
    SharebearerAnalysis
)
from app.models.base import PaginationParams

logger = logging.getLogger(__name__)

class BossService(BaseService[BossResponse]):
    """
    Servicio especializado para jefes con análisis de drops y regiones.
    """
    
    def __init__(self):
        super().__init__("bosses", BossResponse)
    
    def _build_boss_filter_query(self, filters: BossFilterParams) -> Dict[str, Any]:
        """
        Construye query específica para jefes.
        
        Args:
            filters: Filtros de jefes
            
        Returns:
            Query de MongoDB
        """
        query = {}
        
        if filters.name:
            query["name"] = {"$regex": filters.name, "$options": "i"}
        
        if filters.region:
            query["region"] = filters.region
        
        if filters.location:
            query["location"] = {"$regex": filters.location, "$options": "i"}
        
        if filters.has_drops is not None:
            if filters.has_drops:
                query["drops"] = {"$exists": True, "$ne": None, "$ne": []}
            else:
                query["$or"] = [
                    {"drops": {"$exists": False}},
                    {"drops": None},
                    {"drops": []}
                ]
        
        if filters.drop_item:
            query["drops"] = {"$regex": filters.drop_item, "$options": "i"}
        
        if filters.has_remembrance is not None:
            if filters.has_remembrance:
                query["drops"] = {
                    "$elemMatch": {"$regex": "Remembrance", "$options": "i"}
                }
            else:
                query["drops"] = {
                    "$not": {"$elemMatch": {"$regex": "Remembrance", "$options": "i"}}
                }
        
        if filters.has_great_rune is not None:
            if filters.has_great_rune:
                query["drops"] = {
                    "$elemMatch": {"$regex": "Great Rune", "$options": "i"}
                }
        
        return query
    
    async def get_bosses(
        self,
        filters: Optional[BossFilterParams] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Dict[str, Any]:
        """
        Obtiene jefes con filtros específicos.
        
        Args:
            filters: Filtros de jefes
            pagination: Paginación
            
        Returns:
            Lista de jefes con metadatos
        """
        try:
            filters = filters or BossFilterParams()
            pagination = pagination or PaginationParams()
            
            query = self._build_boss_filter_query(filters)
            
            return await self.get_many(query, pagination)
            
        except Exception as e:
            logger.error(f"Error obteniendo jefes: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener jefes"
            )
    
    async def get_by_region(self, region: str) -> List[BossResponse]:
        """
        Obtiene todos los jefes de una región específica.
        
        Args:
            region: Nombre de la región
            
        Returns:
            Lista de jefes en la región
        """
        try:
            query = {"region": region}
            documents = list(self.collection.find(query))
            
            return [self._document_to_model(doc) for doc in documents]
            
        except Exception as e:
            logger.error(f"Error obteniendo jefes de región {region}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener jefes por región"
            )
    
    async def get_bosses_by_region_grouped(self) -> List[BossByRegionResponse]:
        """
        Agrupa jefes por región con conteo.
        Optimizado con agregación de MongoDB.
        
        Returns:
            Jefes agrupados por región
        """
        try:
            pipeline = [
                {
                    "$match": {
                        "region": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": "$region",
                        "bosses": {"$push": "$ROOT"},
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}}
            ]
            
            results = await self.aggregate(pipeline)
            
            grouped = []
            for result in results:
                bosses = [self._document_to_model(b) for b in result["bosses"]]
                grouped.append(
                    BossByRegionResponse(
                        region=result["_id"],
                        boss_count=result["count"],
                        bosses=bosses
                    )
                )
            
            return grouped
            
        except Exception as e:
            logger.error(f"Error agrupando jefes por región: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al agrupar jefes"
            )
    
    async def get_bosses_by_tier(self) -> List[BossByTierResponse]:
        """
        Agrupa jefes por tier (Legendary, Major, Minor).
        
        Returns:
            Jefes agrupados por tier
        """
        try:
            pipeline = [
                {
                    "$addFields": {
                        "has_great_rune": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$isArray": "$drops"},
                                        {
                                            "$gt": [
                                                {
                                                    "$size": {
                                                        "$filter": {
                                                            "input": "$drops",
                                                            "as": "drop",
                                                            "cond": {
                                                                "$regexMatch": {
                                                                    "input": "$drop",
                                                                    "regex": "Great Rune",
                                                                    "options": "i"
                                                                }
                                                            }
                                                        }
                                                    }
                                                },
                                                0
                                            ]
                                        }
                                    ]
                                },
                                True,
                                False
                            ]
                        },
                        "has_remembrance": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$isArray": "$drops"},
                                        {
                                            "$gt": [
                                                {
                                                    "$size": {
                                                        "$filter": {
                                                            "input": "$drops",
                                                            "as": "drop",
                                                            "cond": {
                                                                "$regexMatch": {
                                                                    "input": "$drop",
                                                                    "regex": "Remembrance",
                                                                    "options": "i"
                                                                }
                                                            }
                                                        }
                                                    }
                                                },
                                                0
                                            ]
                                        }
                                    ]
                                },
                                True,
                                False
                            ]
                        }
                    }
                },
                {
                    "$addFields": {
                        "tier": {
                            "$cond": [
                                "$has_great_rune",
                                "Legendary",
                                {
                                    "$cond": [
                                        "$has_remembrance",
                                        "Major",
                                        "Minor"
                                    ]
                                }
                            ]
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$tier",
                        "bosses": {"$push": "$ROOT"},
                        "count": {"$sum": 1},
                        "total_drops": {"$sum": {"$size": {"$ifNull": ["$drops", []]}}}
                    }
                },
                {
                    "$sort": {
                        "_id": 1
                    }
                }
            ]
            
            results = await self.aggregate(pipeline)
            
            tier_order = {"Legendary": 0, "Major": 1, "Minor": 2}
            results.sort(key=lambda x: tier_order.get(x["_id"], 3))
            
            grouped = []
            for result in results:
                bosses = [self._document_to_model(b) for b in result["bosses"]]
                grouped.append(
                    BossByTierResponse(
                        tier=result["_id"],
                        boss_count=result["count"],
                        bosses=bosses,
                        total_drops=result["total_drops"]
                    )
                )
            
            return grouped
            
        except Exception as e:
            logger.error(f"Error agrupando jefes por tier: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al agrupar jefes por tier"
            )
    
    async def analyze_drops(self) -> List[BossDropAnalysis]:
        """
        Analiza qué items dropean los jefes.
        Muestra qué jefes dropean cada item único.
        
        Returns:
            Análisis de drops
        """
        try:
            pipeline = [
                {
                    "$match": {
                        "drops": {"$exists": True, "$ne": None, "$ne": []}
                    }
                },
                {"$unwind": "$drops"},
                {
                    "$group": {
                        "_id": "$drops",
                        "dropped_by": {"$push": "$name"},
                        "drop_count": {"$sum": 1}
                    }
                },
                {"$sort": {"drop_count": -1}}
            ]
            
            results = await self.aggregate(pipeline)
            
            return [
                BossDropAnalysis(
                    item_name=result["_id"],
                    dropped_by=result["dropped_by"],
                    drop_count=result["drop_count"]
                )
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error analizando drops: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al analizar drops"
            )
    
    async def get_shardbearers(self) -> SharebearerAnalysis:
        """
        Obtiene análisis de Shardbearers (jefes con Gran Runa).
        Jefes obligatorios para completar el juego.
        
        Returns:
            Análisis de Shardbearers
        """
        try:
            query = {
                "drops": {
                    "$elemMatch": {"$regex": "Great Rune", "$options": "i"}
                }
            }
            
            documents = list(self.collection.find(query))
            shardbearers = [self._document_to_model(doc) for doc in documents]
            
            great_runes = []
            regions = set()
            
            for boss in shardbearers:
                if boss.drops:
                    for drop in boss.drops:
                        if "Great Rune" in drop:
                            great_runes.append(drop)
                
                if boss.region:
                    regions.add(boss.region)
            
            return SharebearerAnalysis(
                total_shardbearers=len(shardbearers),
                shardbearers=shardbearers,
                great_runes=great_runes,
                regions_with_shardbearers=list(regions)
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo shardbearers: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener shardbearers"
            )
    
    async def get_statistics(self) -> BossStatistics:
        """
        Obtiene estadísticas generales de jefes.
        
        Returns:
            Estadísticas agregadas
        """
        try:
            pipeline = [
                {
                    "$facet": {
                        "total": [
                            {"$count": "count"}
                        ],
                        "by_region": [
                            {
                                "$match": {
                                    "region": {"$exists": True, "$ne": None}
                                }
                            },
                            {
                                "$group": {
                                    "_id": "$region",
                                    "count": {"$sum": 1}
                                }
                            }
                        ],
                        "with_drops": [
                            {
                                "$match": {
                                    "drops": {"$exists": True, "$ne": None, "$ne": []}
                                }
                            },
                            {"$count": "count"}
                        ],
                        "unique_drops": [
                            {
                                "$match": {
                                    "drops": {"$exists": True, "$ne": None, "$ne": []}
                                }
                            },
                            {"$unwind": "$drops"},
                            {
                                "$group": {
                                    "_id": "$drops"
                                }
                            },
                            {"$count": "count"}
                        ]
                    }
                }
            ]
            
            results = await self.aggregate(pipeline)
            
            if not results:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No se encontraron datos"
                )
            
            result = results[0]
            
            total_bosses = result["total"][0]["count"] if result["total"] else 0
            bosses_with_drops = result["with_drops"][0]["count"] if result["with_drops"] else 0
            unique_drops = result["unique_drops"][0]["count"] if result["unique_drops"] else 0
            
            by_region = {
                r["_id"]: r["count"] 
                for r in result["by_region"]
            }
            
            return BossStatistics(
                total_bosses=total_bosses,
                bosses_by_region=by_region,
                total_unique_drops=unique_drops,
                bosses_with_drops=bosses_with_drops,
                bosses_without_drops=total_bosses - bosses_with_drops
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de jefes: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al calcular estadísticas"
            )
    
    async def search_by_drop(self, item_name: str) -> List[BossResponse]:
        """
        Busca jefes que dropean un item específico.
        
        Args:
            item_name: Nombre del item a buscar
            
        Returns:
            Lista de jefes que dropean el item
        """
        try:
            query = {
                "drops": {"$regex": item_name, "$options": "i"}
            }
            
            documents = list(self.collection.find(query))
            
            return [self._document_to_model(doc) for doc in documents]
            
        except Exception as e:
            logger.error(f"Error buscando jefes por drop {item_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al buscar jefes por drop"
            )

boss_service = BossService()