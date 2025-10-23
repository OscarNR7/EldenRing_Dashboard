from pydantic import Field, field_validator, computed_field
from typing import Optional, List, Dict
from app.models.base import BaseDocument, FilterParams


class BossBase(BaseDocument):
    """
    Modelo base para jefes de Elden Ring.
    Contiene información de enemigos principales y jefes.
    """
    name: str = Field(..., min_length=1, max_length=200, description="Nombre del jefe")
    image: Optional[str] = Field(default=None, description="URL de la imagen")
    description: Optional[str] = Field(default=None, description="Descripción del jefe")
    location: Optional[str] = Field(default=None, description="Ubicación donde se encuentra")
    region: Optional[str] = Field(default=None, description="Región del mapa")
    
    drops: Optional[List[str]] = Field(
        default=None,
        description="Lista de items que dropea"
    )
    
    healthPoints: Optional[str] = Field(
        default=None,
        description="Puntos de vida del jefe"
    )
    
    @field_validator('region')
    @classmethod
    def validate_region(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza el nombre de la región"""
        if v:
            return v.strip().title()
        return v
    
    @field_validator('location')
    @classmethod
    def validate_location(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza el nombre de la ubicación"""
        if v:
            return v.strip().title()
        return v

    @computed_field
    @property
    def drop_count(self) -> int:
        """Número de items que dropea el jefe"""
        if self.drops:
            return len(self.drops)
        return 0
    
    @computed_field
    @property
    def has_remembrance(self) -> bool:
        """Indica si el jefe tiene una remembranza asociada"""
        if self.drops:
            return any('Remembrance' in item for item in self.drops)
        return False
    
    @computed_field
    @property
    def has_great_rune(self) -> bool:
        """Indica si el jefe otorga una Gran Runa al ser derrotado"""
        if self.drops:
            return any('Great Rune' in item for item in self.drops)
        return False
    
    @computed_field
    @property
    def is_shardbearer(self) -> bool:
        """Indica si el jefe es un portador de fragmento (Shardbearer)"""
        return self.has_great_rune
    
    @computed_field
    @property
    def boss_tier(self) -> str:
        """
        Clasifica el jefe en tiers según sus drops.
        - Legendary: Otorga Gran Runa
        - Major: Otorga Remembranza
        - Minor: Otros jefes
        """
        if self.has_great_rune:
            return "Legendary"
        elif self.has_remembrance:
            return "Major"
        return "Minor"
    
    @computed_field
    @property
    def is_required_for_ending(self) -> bool:
        """
        Indica si el jefe es requerido para completar el juego.
        Los Shardbearers son obligatorios.
        """
        return self.is_shardbearer


class BossCreate(BaseDocument):
    """
    Modelo para crear un jefe nuevo.
    Usado en operaciones POST.
    """
    name: str = Field(..., min_length=1, max_length=200)
    image: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    region: Optional[str] = None
    drops: Optional[List[str]] = None
    healthPoints: Optional[str] = None


class BossUpdate(BaseDocument):
    """
    Modelo para actualizar un jefe.
    Todos los campos son opcionales (PATCH).
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    image: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    region: Optional[str] = None
    drops: Optional[List[str]] = None
    healthPoints: Optional[str] = None


class BossInDB(BossBase):
    """
    Modelo para jefes almacenados en la base de datos.
    """
    pass


class BossResponse(BossBase):
    """
    Modelo de respuesta para jefes.
    Es lo que se retorna en los endpoints.
    """
    pass


class BossListResponse(BaseDocument):
    """
    Modelo de respuesta para listados de jefes con paginación.
    """
    items: List[BossResponse] = Field(description="Lista de jefes")
    total: int = Field(description="Total de registros")
    skip: int = Field(description="Registros omitidos")
    limit: int = Field(description="Límite de registros por página")


class BossFilterParams(FilterParams):
    """
    Parámetros de filtrado específicos para jefes.
    """
    region: Optional[str] = Field(
        default=None,
        description="Filtrar por región"
    )
    
    location: Optional[str] = Field(
        default=None,
        description="Filtrar por ubicación específica"
    )
    
    has_drops: Optional[bool] = Field(
        default=None,
        description="Filtrar jefes que dropean items"
    )
    
    drop_item: Optional[str] = Field(
        default=None,
        description="Filtrar por item específico que dropea"
    )
    
    has_remembrance: Optional[bool] = Field(
        default=None,
        description="Filtrar jefes que otorgan Remembranza"
    )
    
    has_great_rune: Optional[bool] = Field(
        default=None,
        description="Filtrar jefes que otorgan Gran Runa (Shardbearers)"
    )
    
    boss_tier: Optional[str] = Field(
        default=None,
        description="Filtrar por tier: Legendary, Major, Minor"
    )
    
    is_required: Optional[bool] = Field(
        default=None,
        description="Filtrar jefes requeridos para completar el juego"
    )

    @field_validator('boss_tier')
    @classmethod
    def validate_boss_tier(cls, v: Optional[str]) -> Optional[str]:
        """Valida el tier del jefe"""
        if v:
            valid_tiers = ['Legendary', 'Major', 'Minor']
            normalized = v.strip().title()
            if normalized not in valid_tiers:
                raise ValueError(f"boss_tier debe ser uno de: {', '.join(valid_tiers)}")
            return normalized
        return v


class BossStatistics(BaseDocument):
    """
    Modelo para estadísticas agregadas de jefes.
    """
    total_bosses: int = Field(description="Total de jefes")
    bosses_by_region: Dict[str, int] = Field(description="Jefes agrupados por región")
    total_unique_drops: int = Field(description="Total de drops únicos")
    bosses_with_drops: int = Field(description="Jefes que dropean items")
    bosses_without_drops: int = Field(description="Jefes sin drops")


class BossByRegionResponse(BaseDocument):
    """
    Modelo para agrupar jefes por región.
    """
    region: str = Field(description="Nombre de la región")
    boss_count: int = Field(description="Número de jefes en la región")
    bosses: List[BossResponse] = Field(description="Lista de jefes")


class BossDropAnalysis(BaseDocument):
    """
    Modelo para análisis de drops de jefes.
    """
    item_name: str = Field(description="Nombre del item")
    dropped_by: List[str] = Field(description="Lista de jefes que dropean este item")
    drop_count: int = Field(description="Número de jefes que lo dropean")


class BossByTierResponse(BaseDocument):
    """
    Modelo para agrupar jefes por tier.
    """
    tier: str = Field(description="Tier del jefe: Legendary, Major, Minor")
    boss_count: int = Field(description="Número de jefes en este tier")
    bosses: List[BossResponse] = Field(description="Lista de jefes")
    total_drops: int = Field(description="Total de drops únicos en este tier")


class SharebearerAnalysis(BaseDocument):
    """
    Modelo para análisis específico de Shardbearers.
    Jefes que otorgan Gran Runa y son obligatorios para el juego.
    """
    total_shardbearers: int = Field(description="Total de Shardbearers")
    shardbearers: List[BossResponse] = Field(description="Lista de Shardbearers")
    great_runes: List[str] = Field(description="Lista de Grandes Runas disponibles")
    regions_with_shardbearers: List[str] = Field(description="Regiones con Shardbearers")