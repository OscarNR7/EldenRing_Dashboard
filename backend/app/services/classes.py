from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import logging

from app.services.base_service import BaseService
from app.models.classes import (
    ClassResponse,
    ClassCreate,
    ClassUpdate,
    ClassFilterParams,
    ClassComparison,
    BuildRecommendation
)
from app.models.base import PaginationParams

logger = logging.getLogger(__name__)

class ClassService(BaseService[ClassResponse]):
    """
    Servicio especializado para clases con análisis de builds y comparaciones.
    """
    
    def __init__(self):
        super().__init__("classes", ClassResponse)
    
    def _build_class_filter_query(self, filters: ClassFilterParams) -> Dict[str, Any]:
        """
        Construye query específica para clases, utilizando el filtro base
        y añadiendo lógica específica para clases.
        
        Args:
            filters: Filtros de clases
            
        Returns:
            Query de MongoDB
        """
        # Usar el constructor de filtros base para manejar 'name', etc.
        base_query = super()._build_filter_query(filters.model_dump(exclude_unset=True))
        query = base_query
        
        if filters.min_level is not None:
            query["stats.level"] = {"$gte": filters.min_level}
        
        if filters.max_level is not None:
            if "stats.level" in query:
                query["stats.level"]["$lte"] = filters.max_level
            else:
                query["stats.level"] = {"$lte": filters.max_level}
        
        if filters.min_strength is not None:
            query["stats.strength"] = {"$gte": filters.min_strength}
        
        if filters.min_intelligence is not None:
            query["stats.intelligence"] = {"$gte": filters.min_intelligence}
        
        if filters.min_faith is not None:
            query["stats.faith"] = {"$gte": filters.min_faith}
        
        if filters.archetype:
            # Asumiendo que el campo 'archetype' existe en el documento de MongoDB
            # y que queremos una búsqueda case-insensitive
            query["archetype"] = {"$regex": filters.archetype, "$options": "i"}
        
        return query
    
    async def get_classes(
        self,
        filters: Optional[ClassFilterParams] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Dict[str, Any]:
        """
        Obtiene clases con filtros específicos.
        
        Args:
            filters: Filtros de clases
            pagination: Paginación
            
        Returns:
            Lista de clases con metadatos
        """
        try:
            filters = filters or ClassFilterParams()
            pagination = pagination or PaginationParams()
            
            query = self._build_class_filter_query(filters)
            
            return await self.get_many(filters=query, pagination=pagination)
            
        except Exception as e:
            logger.error(f"Error obteniendo clases: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener clases"
            )
    
    async def get_by_archetype(self, archetype: str) -> List[ClassResponse]:
        """
        Obtiene clases por arquetipo.
        
        Args:
            archetype: Tipo de arquetipo (Strength, Dexterity, etc.)
            
        Returns:
            Lista de clases del arquetipo
        """
        try:
            # La validación del arquetipo ya se hace en el modelo ClassFilterParams
            # o se puede hacer aquí si no se usa un filtro de Pydantic.
            # Para asegurar consistencia, normalizamos y validamos aquí también.
            valid_archetypes = [
                'Strength', 'Dexterity', 'Quality', 'Sorcerer', 
                'Cleric', 'Occult', 'Tank', 'Hybrid', 'Balanced'
            ]
            
            archetype = archetype.strip().title()
            
            if archetype not in valid_archetypes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Arquetipo inválido. Opciones: {', '.join(valid_archetypes)}"
                )
            
            # Realizar el filtrado a nivel de base de datos
            query = {"archetype": {"$regex": archetype, "$options": "i"}}
            documents = list(self.collection.find(query))
            
            return [self._document_to_model(doc) for doc in documents]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo clases por arquetipo {archetype}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener clases por arquetipo"
            )
    
    async def compare_classes(
        self,
        comparison: ClassComparison
    ) -> Dict[str, Any]:
        """
        Compara múltiples clases en estadísticas específicas.
        
        Args:
            comparison: Parámetros de comparación
            
        Returns:
            Análisis comparativo completo
        """
        try:
            from bson import ObjectId
            
            class_ids = [
                self._validate_object_id(cid) for cid in comparison.class_ids
            ]
            
            classes = list(self.collection.find({"_id": {"$in": class_ids}}))
            
            if len(classes) != len(class_ids):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Una o más clases no encontradas"
                )
            
            classes_models = [self._document_to_model(c) for c in classes]
            
            stats_comparison = {}
            for stat in comparison.compare_stats:
                stats_comparison[stat] = {}
                for class_model in classes_models:
                    if class_model.stats:
                        stat_value = getattr(class_model.stats, stat, None)
                        stats_comparison[stat][class_model.name] = stat_value
            
            best_per_stat = {}
            for stat, values in stats_comparison.items():
                if values:
                    best_class = max(values.items(), key=lambda x: x[1] if x[1] else 0)
                    best_per_stat[stat] = best_class[0]
            
            total_stats = {}
            for class_model in classes_models:
                if class_model.stats:
                    total_stats[class_model.name] = class_model.stats.total_stats
            
            most_versatile = max(total_stats.items(), key=lambda x: x[1])[0] if total_stats else None
            
            return {
                "classes": classes_models,
                "stats_comparison": stats_comparison,
                "best_per_stat": best_per_stat,
                "total_stats": total_stats,
                "most_versatile": most_versatile,
                "archetypes": {c.name: c.archetype for c in classes_models}
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error comparando clases: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en comparación de clases"
            )
    
    async def get_best_starting_class(
        self,
        build_type: str
    ) -> Dict[str, Any]:
        """
        Recomienda la mejor clase inicial para un tipo de build.
        
        Args:
            build_type: Tipo de build deseado
            
        Returns:
            Clase recomendada con justificación
        """
        try:
            build_type = build_type.lower()
            
            stat_priorities = {
                "strength": ["strength", "vigor", "endurance"],
                "dexterity": ["dexterity", "vigor", "endurance"],
                "quality": ["strength", "dexterity", "vigor"],
                "intelligence": ["intelligence", "mind", "vigor"],
                "faith": ["faith", "mind", "vigor"],
                "sorcerer": ["intelligence", "mind", "vigor"],
                "cleric": ["faith", "mind", "vigor"],
                "arcane": ["arcane", "mind", "vigor"],
                "tank": ["vigor", "endurance", "strength"],
                "glass_cannon": ["intelligence", "faith", "arcane"]
            }
            
            if build_type not in stat_priorities:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Build type inválido. Opciones: {', '.join(stat_priorities.keys())}"
                )
            
            priority_stats = stat_priorities[build_type]
            
            documents = list(self.collection.find({}))
            classes_models = [self._document_to_model(doc) for doc in documents]
            
            scored_classes = []
            for class_model in classes_models:
                if not class_model.stats:
                    continue
                
                score = 0
                stat_details = {}
                
                for i, stat in enumerate(priority_stats):
                    weight = len(priority_stats) - i
                    stat_value = getattr(class_model.stats, stat, 0) or 0
                    score += stat_value * weight
                    stat_details[stat] = stat_value
                
                starting_level = class_model.stats.level or 1
                score -= starting_level * 0.5
                
                scored_classes.append({
                    "class": class_model,
                    "score": score,
                    "starting_level": starting_level,
                    "priority_stats": stat_details,
                    "archetype": class_model.archetype
                })
            
            scored_classes.sort(key=lambda x: x["score"], reverse=True)
            
            best_class = scored_classes[0] if scored_classes else None
            alternatives = scored_classes[1:4] if len(scored_classes) > 1 else []
            
            return {
                "build_type": build_type,
                "recommended_class": best_class,
                "alternatives": alternatives,
                "priority_stats": priority_stats,
                "recommendation_reason": (
                    f"Esta clase tiene las mejores stats iniciales para un build {build_type}, "
                    f"maximizando {', '.join(priority_stats[:2])} mientras mantiene un nivel inicial bajo."
                )
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo mejor clase para build {build_type}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al recomendar clase"
            )
    
    async def get_stat_distribution(self) -> Dict[str, Any]:
        """
        Analiza la distribución de estadísticas entre todas las clases.
        
        Returns:
            Análisis estadístico de distribución
        """
        try:
            pipeline = [
                {
                    "$project": {
                        "name": 1,
                        "vigor": "$stats.vigor",
                        "mind": "$stats.mind",
                        "endurance": "$stats.endurance",
                        "strength": "$stats.strength",
                        "dexterity": "$stats.dexterity",
                        "intelligence": "$stats.intelligence",
                        "faith": "$stats.faith",
                        "arcane": "$stats.arcane",
                        "level": "$stats.level"
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg_vigor": {"$avg": "$vigor"},
                        "avg_mind": {"$avg": "$mind"},
                        "avg_endurance": {"$avg": "$endurance"},
                        "avg_strength": {"$avg": "$strength"},
                        "avg_dexterity": {"$avg": "$dexterity"},
                        "avg_intelligence": {"$avg": "$intelligence"},
                        "avg_faith": {"$avg": "$faith"},
                        "avg_arcane": {"$avg": "$arcane"},
                        "avg_level": {"$avg": "$level"},
                        "max_vigor": {"$max": "$vigor"},
                        "max_mind": {"$max": "$mind"},
                        "max_strength": {"$max": "$strength"},
                        "max_dexterity": {"$max": "$dexterity"},
                        "max_intelligence": {"$max": "$intelligence"},
                        "max_faith": {"$max": "$faith"},
                        "min_vigor": {"$min": "$vigor"},
                        "min_mind": {"$min": "$mind"},
                        "min_strength": {"$min": "$strength"},
                        "min_dexterity": {"$min": "$dexterity"},
                        "min_intelligence": {"$min": "$intelligence"},
                        "min_faith": {"$min": "$faith"}
                    }
                }
            ]
            
            results = await self.aggregate(pipeline)
            
            if results:
                stats = results[0]
                del stats["_id"]
                
                for key, value in stats.items():
                    if isinstance(value, float):
                        stats[key] = round(value, 2)
                
                return stats
            
            return {}
            
        except Exception as e:
            logger.error(f"Error obteniendo distribución de stats: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al analizar distribución"
            )
    
    async def get_build_recommendation(
        self,
        class_id: str
    ) -> BuildRecommendation:
        """
        Genera recomendaciones de build para una clase específica.
        
        Args:
            class_id: ID de la clase
            
        Returns:
            Recomendaciones de armas, hechizos y stats
        """
        try:
            class_model = await self.get_by_id(class_id)
            
            if not class_model.stats:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La clase no tiene estadísticas definidas"
                )
            
            primary_stats = class_model.primary_stats
            archetype = class_model.archetype
            
            weapon_recommendations = {
                "Strength": ["Greatsword", "Colossal Sword", "Great Hammer"],
                "Dexterity": ["Katana", "Curved Sword", "Spear"],
                "Quality": ["Straight Sword", "Greatsword", "Halberd"],
                "Sorcerer": ["Staff", "Glintstone Staff"],
                "Cleric": ["Sacred Seal", "Cipher Pata"],
                "Occult": ["Occult Weapon", "Reduvia"],
                "Tank": ["Greatshield", "Lance"],
                "Hybrid": ["Quality Weapon", "Faith/Int Weapon"]
            }
            
            spell_recommendations = {
                "Sorcerer": ["Glintstone Pebble", "Rock Sling", "Comet Azur"],
                "Cleric": ["Heal", "Lightning Spear", "Black Flame"],
                "Occult": ["Bloodflame Blade", "Dragon Communion"]
            }
            
            stat_priority = {
                "Strength": ["Vigor", "Endurance", "Strength"],
                "Dexterity": ["Vigor", "Endurance", "Dexterity"],
                "Quality": ["Vigor", "Strength", "Dexterity"],
                "Sorcerer": ["Mind", "Intelligence", "Vigor"],
                "Cleric": ["Mind", "Faith", "Vigor"],
                "Occult": ["Arcane", "Mind", "Vigor"],
                "Tank": ["Vigor", "Endurance", "Strength"],
                "Hybrid": ["Vigor", "Mind", "Primary Stats"]
            }
            
            playstyle_guide = {
                "Strength": "Build enfocado en armas pesadas y daño físico alto. Prioriza armadura pesada y resistencia.",
                "Dexterity": "Build ágil con armas rápidas. Enfócate en esquivar y ataques críticos.",
                "Quality": "Build versátil que usa STR y DEX. Acceso a más opciones de armas.",
                "Sorcerer": "Build de hechicero con magia ofensiva. Mantén distancia y usa hechizos poderosos.",
                "Cleric": "Build de fe con incantaciones. Balance entre daño y soporte.",
                "Occult": "Build basado en arcano. Efectos de estado y sangrado.",
                "Tank": "Build defensivo con HP alto y armadura pesada.",
                "Hybrid": "Build mixto con múltiples opciones de combate."
            }
            
            return BuildRecommendation(
                class_name=class_model.name,
                recommended_weapons=weapon_recommendations.get(archetype, ["Balanced Weapon"]),
                recommended_spells=spell_recommendations.get(archetype, []),
                recommended_stats_priority=stat_priority.get(archetype, primary_stats),
                playstyle=playstyle_guide.get(archetype, "Build balanceado y versátil")
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generando recomendación de build: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al generar recomendación"
            )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de clases.
        
        Returns:
            Estadísticas agregadas
        """
        try:
            documents = list(self.collection.find({}))
            classes_models = [self._document_to_model(doc) for doc in documents]
            
            archetype_distribution = {}
            for class_model in classes_models:
                archetype = class_model.archetype
                archetype_distribution[archetype] = archetype_distribution.get(archetype, 0) + 1
            
            level_range = {
                "min": min(c.stats.level for c in classes_models if c.stats and c.stats.level),
                "max": max(c.stats.level for c in classes_models if c.stats and c.stats.level),
                "avg": sum(c.stats.level for c in classes_models if c.stats and c.stats.level) / len(classes_models)
            }
            
            return {
                "total_classes": len(classes_models),
                "archetype_distribution": archetype_distribution,
                "level_range": level_range,
                "class_names": [c.name for c in classes_models]
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de clases: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al calcular estadísticas"
            )

class_service = ClassService()