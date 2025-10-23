"""
Modelos Pydantic para validación y serialización de datos.

Este módulo exporta todos los modelos usados en la API.
Organizado por categorías para fácil importación.
"""

from app.models.base import (
    PyObjectId,
    BaseDocument,
    AttackStats,
    DefenseStats,
    ResistanceStats,
    RequirementStats,
    ScalingStats,
    PaginationParams,
    FilterParams,
)

from app.models.weapons import (
    WeaponBase,
    WeaponCreate,
    WeaponUpdate,
    WeaponInDB,
    WeaponResponse,
    WeaponListResponse,
    WeaponFilterParams,
    WeaponStatsComparison,
)

from app.models.armors import (
    ArmorBase,
    ArmorCreate,
    ArmorUpdate,
    ArmorInDB,
    ArmorResponse,
    ArmorListResponse,
    ArmorFilterParams,
    ArmorSetResponse,
    ArmorOptimizationRequest,
)

from app.models.bosses import (
    BossBase,
    BossCreate,
    BossUpdate,
    BossInDB,
    BossResponse,
    BossListResponse,
    BossFilterParams,
    BossStatistics,
    BossByRegionResponse,
    BossDropAnalysis,
    BossByTierResponse,
    SharebearerAnalysis,
)

from app.models.classes import (
    CharacterStats,
    ClassBase,
    ClassCreate,
    ClassUpdate,
    ClassInDB,
    ClassResponse,
    ClassListResponse,
    ClassFilterParams,
    ClassComparison,
    BuildRecommendation,
)

from app.models.spells import (
    SpellBase,
    SpellCreate,
    SpellUpdate,
    SpellInDB,
    SpellResponse,
    SpellListResponse,
    SpellFilterParams,
    SpellLoadout,
    SpellOptimizationRequest,
)

from app.models.items import (
    ItemBase,
    ItemCreate,
    ItemUpdate,
    ItemInDB,
    ItemResponse,
    ItemListResponse,
    ItemFilterParams,
    TalismanBase,
    TalismanCreate,
    TalismanUpdate,
    TalismanInDB,
    TalismanResponse,
    TalismanListResponse,
)

from app.models.responses import (
    SuccessResponse,
    ErrorDetail,
    ErrorResponse,
    ValidationErrorResponse,
    NotFoundErrorResponse,
    PaginatedResponse,
    AggregationResponse,
    BulkOperationResponse,
    HealthCheckResponse,
    ComparisonResponse,
    OptimizationResponse,
    StatisticsResponse,
    MessageResponse,
)

__all__ = [
    # Base models
    "PyObjectId",
    "BaseDocument",
    "AttackStats",
    "DefenseStats",
    "ResistanceStats",
    "RequirementStats",
    "ScalingStats",
    "PaginationParams",
    "FilterParams",
    
    # Weapons
    "WeaponBase",
    "WeaponCreate",
    "WeaponUpdate",
    "WeaponInDB",
    "WeaponResponse",
    "WeaponListResponse",
    "WeaponFilterParams",
    "WeaponStatsComparison",
    
    # Armors
    "ArmorBase",
    "ArmorCreate",
    "ArmorUpdate",
    "ArmorInDB",
    "ArmorResponse",
    "ArmorListResponse",
    "ArmorFilterParams",
    "ArmorSetResponse",
    "ArmorOptimizationRequest",
    
    # Bosses
    "BossBase",
    "BossCreate",
    "BossUpdate",
    "BossInDB",
    "BossResponse",
    "BossListResponse",
    "BossFilterParams",
    "BossStatistics",
    "BossByRegionResponse",
    "BossDropAnalysis",
    
    # Classes
    "CharacterStats",
    "ClassBase",
    "ClassCreate",
    "ClassUpdate",
    "ClassInDB",
    "ClassResponse",
    "ClassListResponse",
    "ClassFilterParams",
    "ClassComparison",
    "BuildRecommendation",
    
    # Spells
    "SpellBase",
    "SpellCreate",
    "SpellUpdate",
    "SpellInDB",
    "SpellResponse",
    "SpellListResponse",
    "SpellFilterParams",
    "SpellLoadout",
    "SpellOptimizationRequest",
    
    # Items
    "ItemBase",
    "ItemCreate",
    "ItemUpdate",
    "ItemInDB",
    "ItemResponse",
    "ItemListResponse",
    "ItemFilterParams",
    "TalismanBase",
    "TalismanCreate",
    "TalismanUpdate",
    "TalismanInDB",
    "TalismanResponse",
    "TalismanListResponse",
    
    # Responses
    "SuccessResponse",
    "ErrorDetail",
    "ErrorResponse",
    "ValidationErrorResponse",
    "NotFoundErrorResponse",
    "PaginatedResponse",
    "AggregationResponse",
    "BulkOperationResponse",
    "HealthCheckResponse",
    "ComparisonResponse",
    "OptimizationResponse",
    "StatisticsResponse",
    "MessageResponse",
]