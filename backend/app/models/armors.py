from pydantic import Field, field_validator, computed_field
from typing import Optional, List
from app.models.base import (
    BaseDocument,
    DefenseStats,
    ResistanceStats,
    FilterParams
)

class ArmorBase(BaseDocument):
    """
    modelo base para armaduras.
    Representa las piezas de armadura en Elden Ring.
    """
    name: str = Field(..., min_length=1, max_length=200, description="Nombre de la armadura")
    image: Optional[str] = Field(default=None, description="URL de la imagen")
    description: Optional[str] = Field(default=None, description="Descripción de la armadura")
    category: Optional[str] = Field(default=None, description="Categoría (Head, Chest, Arms, Legs)")
    
    weight: Optional[float] = Field(default=None, ge=0, description="Peso de la pieza")
    
    dmgNegation: Optional[DefenseStats] = Field(
        default=None,
        description="Negación de daño"
    )
    
    resistance: Optional[ResistanceStats] = Field(
        default=None,
        description="Resistencias a efectos de estado"
    )

    @field_validator('category')
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """valida y normaliza la categoría de armadura"""
        if v:
            valid_categories = ['Head', 'Chest', 'Arms', 'Legs', 'Helm', 'Armor', 'Gauntlets', 'Leg Armor']
            normalized = v.strip().title()
            if normalized not in valid_categories:
                return normalized
            return normalized
        return v
    
    @computed_field
    @property
    def average_physical_defense(self) -> Optional[float]:
        """Calcula la defensa física promedio"""
        if self.dmgNegation:
            physical_defenses = [
                self.dmgNegation.physical,
                self.dmgNegation.strike,
                self.dmgNegation.slash,
                self.dmgNegation.pierce
            ]
            valid_defenses = [d for d in physical_defenses if d is not None]
            if valid_defenses:
                return round(sum(valid_defenses) / len(valid_defenses), 2)
        return None

    @computed_field
    @property
    def average_elemental_defense(self) -> Optional[float]:
        """Calcula la defensa elemental promedio"""
        if self.dmgNegation:
            elemental_defenses = [
                self.dmgNegation.magic,
                self.dmgNegation.fire,
                self.dmgNegation.lightning,
                self.dmgNegation.holy
            ]
            valid_defenses = [d for d in elemental_defenses if d is not None]
            if valid_defenses:
                return round(sum(valid_defenses) / len(valid_defenses), 2)
        return None

    @computed_field
    @property
    def defense_to_weight_ratio(self) -> Optional[float]:
        """Calcula la relación defensa/peso"""
        if self.weight and self.weight > 0:
            avg_defense = self.average_physical_defense
            if avg_defense and avg_defense > 0:
                return round(avg_defense / self.weight, 2)
        return None

    @computed_field
    @property
    def total_resistance(self) -> int:
        """Suma total de resistencias"""
        if self.resistance:
            resistances = [
                self.resistance.immunity,
                self.resistance.robustness,
                self.resistance.focus,
                self.resistance.vitality
            ]
            return sum(r for r in resistances if r is not None)
        return 0
    
class ArmorCreate(BaseDocument):
    """Modelo para crear una armadura nueva. Con POST"""
    name: str = Field(..., min_length=1, max_length=200)
    image: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    weight: Optional[float] = Field(default=None, ge=0)
    dmgNegation: Optional[DefenseStats] = None
    resistance: Optional[ResistanceStats] = None

class ArmorUpdate(BaseDocument):
    """Modelo para actualizar una armadura. Con PATCH"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    image: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    weight: Optional[float] = Field(default=None, ge=0)
    dmgNegation: Optional[DefenseStats] = None
    resistance: Optional[ResistanceStats] = None

class ArmorInDB(ArmorBase):
    """Modelo para armadura almacenada en la base de datos."""
    pass

class ArmorResponse(ArmorBase):
    """
    Modelo de respuesta de armaduras
    Lo que retorna en lo endpoints
    """
    pass

class ArmorListResponse(BaseDocument):
    """
    Modelo de respuesta para lista de armaduras con paginación.
    """
    items: List[ArmorResponse] = Field(description="Lista de armaduras")
    total: int = Field(description="Número total de armaduras")
    skip: int = Field(description="Registros omitidos")
    limit: int = Field(description="Límite de registros por pagina")

class ArmorFilterParams(FilterParams):
    """
    Parámetros de filtrado específicos para armaduras.
    """
    min_physical_defense: Optional[float] = Field(
        default=None, 
        ge=0, 
        description="Defensa física mínima promedio"
    )
    max_physical_defense: Optional[float] = Field(
        default=None, 
        ge=0, 
        description="Defensa física máxima promedio"
    )
    
    min_magic_defense: Optional[float] = Field(
        default=None, 
        ge=0, 
        description="Defensa mágica mínima"
    )
    max_magic_defense: Optional[float] = Field(
        default=None, 
        ge=0, 
        description="Defensa mágica máxima"
    )
    
    min_poise: Optional[float] = Field(
        default=None, 
        ge=0, 
        description="Firmeza mínima"
    )
    
    min_immunity: Optional[int] = Field(
        default=None, 
        ge=0, 
        description="Inmunidad mínima"
    )
    
    armor_slot: Optional[str] = Field(
        default=None,
        description="Slot de armadura (Head, Chest, Arms, Legs)"
    )

    @field_validator('armor_slot')
    @classmethod
    def validate_armor_slot(cls, v: Optional[str]) -> Optional[str]:
        """Valida que el slot sea válido"""
        if v:
            valid_slots = ['Head', 'Chest', 'Arms', 'Legs', 'Helm', 'Armor', 'Gauntlets', 'Leg Armor']
            normalized = v.strip().title()
            if normalized not in valid_slots:
                raise ValueError(f"armor_slot debe ser uno de: {', '.join(valid_slots)}")
            return normalized
        return v

class ArmorSetResponse(BaseDocument):
    """
    Modelo para representar un set completo de armadura.
    """
    set_name: str = Field(..., description="Nombre del set")
    helm: Optional[ArmorResponse] = Field(default=None, description="Casco")
    chest: Optional[ArmorResponse] = Field(default=None, description="Pechera")
    gauntlets: Optional[ArmorResponse] = Field(default=None, description="Guanteletes")
    legs: Optional[ArmorResponse] = Field(default=None, description="Grebas")
    
    @computed_field
    @property
    def total_weight(self) -> float:
        """Calcula el peso total del set"""
        pieces = [self.helm, self.chest, self.gauntlets, self.legs]
        return sum(
            piece.weight for piece in pieces 
            if piece and piece.weight is not None
        )
    
    @computed_field
    @property
    def set_bonus_description(self) -> Optional[str]:
        """Descripción del bonus de set si existe"""
        return None

class ArmorOptimizationRequest(BaseDocument):
    """
    Modelo para solicitudes de optimización de armadura.
    Permite encontrar el mejor set según criterios específicos.
    """
    max_weight: float = Field(..., gt=0, description="Peso máximo permitido")
    
    prioritize: str = Field(
        default="physical",
        description="Qué priorizar: physical, magic, fire, lightning, holy, poise"
    )
    
    required_poise: Optional[float] = Field(
        default=None,
        ge=0,
        description="Firmeza mínima requerida"
    )

    @field_validator('prioritize')
    @classmethod
    def validate_prioritize(cls, v: str) -> str:
        """Valida el criterio de priorización"""
        valid_priorities = ['physical', 'magic', 'fire', 'lightning', 'holy', 'poise', 'balanced']
        if v.lower() not in valid_priorities:
            raise ValueError(f"prioritize debe ser uno de: {', '.join(valid_priorities)}")
        return v.lower()