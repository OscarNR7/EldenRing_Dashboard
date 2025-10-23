from pydantic import Field, field_validator, computed_field
from typing import Optional, List
from app.models.base import BaseDocument, RequirementStats, FilterParams


class SpellBase(BaseDocument):
    """
    Modelo base para hechizos (sorceries e incantations).
    """
    name: str = Field(..., min_length=1, max_length=200, description="Nombre del hechizo")
    image: Optional[str] = Field(default=None, description="URL de la imagen")
    description: Optional[str] = Field(default=None, description="Descripción del hechizo")
    type: Optional[str] = Field(default=None, description="Tipo: Sorcery o Incantation")
    
    cost: Optional[int] = Field(default=None, ge=0, description="Costo de FP")
    slots: Optional[int] = Field(default=None, ge=0, le=10, description="Slots de memoria requeridos")
    
    effects: Optional[str] = Field(default=None, description="Efectos del hechizo")
    
    requires: Optional[RequirementStats] = Field(
        default=None,
        description="Requerimientos de stats"
    )

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        """Valida el tipo de hechizo"""
        if v:
            valid_types = ['Sorcery', 'Incantation']
            normalized = v.strip().title()
            if normalized not in valid_types:
                raise ValueError(f"type debe ser 'Sorcery' o 'Incantation'")
            return normalized
        return v

    @computed_field
    @property
    def efficiency_rating(self) -> Optional[float]:
        """
        Calcula un rating de eficiencia basado en slots y costo.
        Menor es mejor (menos recursos = más eficiente).
        """
        if self.slots and self.cost:
            if self.slots > 0:
                return round(self.cost / self.slots, 2)
        return None

    @computed_field
    @property
    def total_requirements(self) -> int:
        """Suma total de requerimientos"""
        if self.requires:
            return self.requires.total_requirements()
        return 0


class SpellCreate(BaseDocument):
    """
    Modelo para crear un hechizo nuevo.
    Usado en operaciones POST.
    """
    name: str = Field(..., min_length=1, max_length=200)
    image: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    cost: Optional[int] = Field(default=None, ge=0)
    slots: Optional[int] = Field(default=None, ge=0, le=10)
    effects: Optional[str] = None
    requires: Optional[RequirementStats] = None


class SpellUpdate(BaseDocument):
    """
    Modelo para actualizar un hechizo.
    Todos los campos son opcionales (PATCH).
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    image: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    cost: Optional[int] = Field(default=None, ge=0)
    slots: Optional[int] = Field(default=None, ge=0, le=10)
    effects: Optional[str] = None
    requires: Optional[RequirementStats] = None


class SpellInDB(SpellBase):
    """
    Modelo para hechizos almacenados en la base de datos.
    """
    pass


class SpellResponse(SpellBase):
    """
    Modelo de respuesta para hechizos.
    Es lo que se retorna en los endpoints.
    """
    pass


class SpellListResponse(BaseDocument):
    """
    Modelo de respuesta para listados de hechizos con paginación.
    """
    items: List[SpellResponse] = Field(description="Lista de hechizos")
    total: int = Field(description="Total de registros")
    skip: int = Field(description="Registros omitidos")
    limit: int = Field(description="Límite de registros por página")


class SpellFilterParams(FilterParams):
    """
    Parámetros de filtrado específicos para hechizos.
    """
    spell_type: Optional[str] = Field(
        default=None,
        description="Tipo de hechizo: Sorcery o Incantation"
    )
    
    min_cost: Optional[int] = Field(
        default=None,
        ge=0,
        description="Costo mínimo de FP"
    )
    max_cost: Optional[int] = Field(
        default=None,
        ge=0,
        description="Costo máximo de FP"
    )
    
    max_slots: Optional[int] = Field(
        default=None,
        ge=0,
        le=10,
        description="Slots máximos requeridos"
    )
    
    min_intelligence: Optional[int] = Field(
        default=None,
        ge=0,
        le=99,
        description="Inteligencia mínima requerida"
    )
    
    min_faith: Optional[int] = Field(
        default=None,
        ge=0,
        le=99,
        description="Fe mínima requerida"
    )

    @field_validator('spell_type')
    @classmethod
    def validate_spell_type(cls, v: Optional[str]) -> Optional[str]:
        """Valida el tipo de hechizo"""
        if v:
            valid_types = ['Sorcery', 'Incantation']
            normalized = v.strip().title()
            if normalized not in valid_types:
                raise ValueError(f"spell_type debe ser 'Sorcery' o 'Incantation'")
            return normalized
        return v


class SpellLoadout(BaseDocument):
    """
    Modelo para un loadout de hechizos.
    Representa una configuración específica de hechizos equipados.
    """
    loadout_name: str = Field(..., description="Nombre del loadout")
    spell_ids: List[str] = Field(..., max_length=10, description="IDs de hechizos en el loadout")
    total_slots_used: int = Field(ge=0, le=10, description="Total de slots usados")
    
    @field_validator('spell_ids')
    @classmethod
    def validate_spell_ids(cls, v: List[str]) -> List[str]:
        """Valida que no haya hechizos duplicados"""
        if len(v) != len(set(v)):
            raise ValueError("No se pueden tener hechizos duplicados en el loadout")
        return v


class SpellOptimizationRequest(BaseDocument):
    """
    Modelo para solicitudes de optimización de hechizos.
    Encuentra los mejores hechizos según criterios.
    """
    max_slots: int = Field(..., ge=1, le=10, description="Slots máximos disponibles")
    max_fp_cost: Optional[int] = Field(default=None, ge=0, description="Costo máximo de FP por hechizo")
    
    spell_type: Optional[str] = Field(
        default=None,
        description="Filtrar por tipo: Sorcery o Incantation"
    )
    
    character_intelligence: Optional[int] = Field(
        default=None,
        ge=1,
        le=99,
        description="Inteligencia del personaje"
    )
    
    character_faith: Optional[int] = Field(
        default=None,
        ge=1,
        le=99,
        description="Fe del personaje"
    )
    
    optimize_for: str = Field(
        default="balanced",
        description="Optimizar para: damage, utility, balanced"
    )

    @field_validator('spell_type')
    @classmethod
    def validate_spell_type(cls, v: Optional[str]) -> Optional[str]:
        """Valida el tipo de hechizo"""
        if v:
            valid_types = ['Sorcery', 'Incantation']
            normalized = v.strip().title()
            if normalized not in valid_types:
                raise ValueError(f"spell_type debe ser 'Sorcery' o 'Incantation'")
            return normalized
        return v

    @field_validator('optimize_for')
    @classmethod
    def validate_optimize_for(cls, v: str) -> str:
        """Valida el criterio de optimización"""
        valid_criteria = ['damage', 'utility', 'balanced', 'cost_efficient']
        if v.lower() not in valid_criteria:
            raise ValueError(f"optimize_for debe ser uno de: {', '.join(valid_criteria)}")
        return v.lower()