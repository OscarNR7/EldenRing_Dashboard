from pydantic import Field, field_validator, computed_field
from typing import Optional, List
from app.models.base import (
    BaseDocument,
    AttackStats,
    RequirementStats,
    ScalingStats,
    FilterParams
)

class WeaponBase(BaseDocument):
    """
    Modelo base para armas.
    Contiene todos los campos comunes de las armas de Elden Ring.
    """
    name: str = Field(..., min_length=1, max_length=200, description="Nombre del arma")
    image: Optional[str] = Field(default=None, description="URL de la imagen")
    description: Optional[str] = Field(default=None, description="Descripción del arma")
    category: Optional[str] = Field(default=None, description="Categoría del arma (Greatsword, Katana, etc.)")
    
    weight: Optional[float] = Field(default=None, ge=0, description="Peso del arma")
    
    attack: Optional[AttackStats] = Field(default=None, description="Estadísticas de ataque base")
    
    defence: Optional[dict] = Field(default=None, description="Estadísticas de defensa/bloqueo")
    
    scalesWith: Optional[ScalingStats] = Field(
        default=None,
        description="Escalado de atributos"
    )
    
    requiredAttributes: Optional[RequirementStats] = Field(
        default=None,
        description="Atributos requeridos"
    )
    
    passive: Optional[str] = Field(default=None, description="Efecto pasivo del arma")
    
    critical: Optional[int] = Field(default=None, ge=0, description="Bonus de crítico")

    @field_validator('category')
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza la categoría a formato título"""
        if v:
            return v.strip().title()
        return v

    @computed_field
    @property
    def total_attack_power(self) -> int:
        """Calcula el poder de ataque total del arma"""
        if self.attack:
            return self.attack.total_damage()
        return 0

    @computed_field
    @property
    def damage_to_weight_ratio(self) -> Optional[float]:
        """Calcula la relación daño/peso"""
        if self.weight and self.weight > 0 and self.attack:
            total_dmg = self.attack.total_damage()
            if total_dmg > 0:
                return round(total_dmg / self.weight, 2)
        return None

    @computed_field
    @property
    def total_requirements(self) -> int:
        """Suma total de requerimientos de atributos"""
        if self.requiredAttributes:
            return self.requiredAttributes.total_requirements()
        return 0

class WeaponCreate(BaseDocument):
    """
    Modelo para crear un arma nueva.
    Usado en operaciones POST.
    """
    name: str = Field(..., min_length=1, max_length=200)
    image: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    weight: Optional[float] = Field(default=None, ge=0)
    attack: Optional[AttackStats] = None
    defence: Optional[dict] = None
    scalesWith: Optional[ScalingStats] = None
    requiredAttributes: Optional[RequirementStats] = None
    passive: Optional[str] = None
    critical: Optional[int] = Field(default=None, ge=0)

class WeaponUpdate(BaseDocument):
    """
    Modelo para actualizar un arma.
    Todos los campos son opcionales (PATCH).
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    image: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    weight: Optional[float] = Field(default=None, ge=0)
    attack: Optional[AttackStats] = None
    defence: Optional[dict] = None
    scalesWith: Optional[ScalingStats] = None
    requiredAttributes: Optional[RequirementStats] = None
    passive: Optional[str] = None
    critical: Optional[int] = Field(default=None, ge=0)

class WeaponInDB(WeaponBase):
    """
    Modelo para armas almacenadas en la base de datos.
    Incluye campos adicionales de auditoría si es necesario.
    """
    pass

class WeaponResponse(WeaponBase):
    """
    Modelo de respuesta para armas.
    Es lo que se retorna en los endpoints.
    """
    pass

class WeaponListResponse(BaseDocument):
    """
    Modelo de respuesta para listados de armas con paginación.
    """
    items: List[WeaponResponse] = Field(description="Lista de armas")
    total: int = Field(description="Total de registros")
    skip: int = Field(description="Registros omitidos")
    limit: int = Field(description="Límite de registros por página")

class WeaponFilterParams(FilterParams):
    """
    Parámetros de filtrado específicos para armas.
    Extiende FilterParams base con campos específicos de armas.
    """
    min_damage: Optional[int] = Field(default=None, ge=0, description="Daño físico mínimo")
    max_damage: Optional[int] = Field(default=None, ge=0, description="Daño físico máximo")
    
    min_strength: Optional[int] = Field(default=None, ge=0, le=99, description="Fuerza mínima requerida")
    max_strength: Optional[int] = Field(default=None, ge=0, le=99, description="Fuerza máxima requerida")
    
    min_dexterity: Optional[int] = Field(default=None, ge=0, le=99, description="Destreza mínima requerida")
    max_dexterity: Optional[int] = Field(default=None, ge=0, le=99, description="Destreza máxima requerida")
    
    scaling_grade: Optional[str] = Field(
        default=None,
        description="Grado mínimo de escalado (E, D, C, B, A, S)"
    )
    
    has_passive: Optional[bool] = Field(default=None, description="Filtrar armas con efecto pasivo")

    @field_validator('max_damage')
    @classmethod
    def validate_damage_range(cls, v: Optional[int], info) -> Optional[int]:
        """Valida que max_damage sea mayor que min_damage"""
        if v is not None and info.data.get('min_damage') is not None:
            if v < info.data['min_damage']:
                raise ValueError("max_damage debe ser mayor que min_damage")
        return v

    @field_validator('scaling_grade')
    @classmethod
    def validate_scaling_grade(cls, v: Optional[str]) -> Optional[str]:
        """Valida que el grado de escalado sea válido"""
        if v:
            valid_grades = ['E', 'D', 'C', 'B', 'A', 'S']
            if v.upper() not in valid_grades:
                raise ValueError(f"scaling_grade debe ser uno de: {', '.join(valid_grades)}")
            return v.upper()
        return v

class WeaponStatsComparison(BaseDocument):
    """
    Modelo para comparar estadísticas entre múltiples armas.
    """
    weapon_ids: List[str] = Field(..., min_length=2, max_length=5, description="IDs de armas a comparar")
    
    @field_validator('weapon_ids')
    @classmethod
    def validate_weapon_ids(cls, v: List[str]) -> List[str]:
        """Valida que no haya IDs duplicados"""
        if len(v) != len(set(v)):
            raise ValueError("No se pueden comparar armas duplicadas")
        return v