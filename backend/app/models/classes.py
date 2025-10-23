from pydantic import Field, field_validator, computed_field
from typing import Optional, List, Dict
from app.models.base import BaseDocument, FilterParams


class CharacterStats(BaseDocument):
    """
    Modelo para estadísticas base de un personaje.
    """
    level: Optional[int] = Field(default=None, ge=1, le=713, description="Nivel del personaje")
    vigor: Optional[int] = Field(default=None, ge=1, le=99, description="Vigor")
    mind: Optional[int] = Field(default=None, ge=1, le=99, description="Mente")
    endurance: Optional[int] = Field(default=None, ge=1, le=99, description="Resistencia")
    strength: Optional[int] = Field(default=None, ge=1, le=99, description="Fuerza")
    dexterity: Optional[int] = Field(default=None, ge=1, le=99, description="Destreza")
    intelligence: Optional[int] = Field(default=None, ge=1, le=99, description="Inteligencia")
    faith: Optional[int] = Field(default=None, ge=1, le=99, description="Fe")
    arcane: Optional[int] = Field(default=None, ge=1, le=99, description="Arcano")

    @computed_field
    @property
    def total_stats(self) -> int:
        """Suma total de estadísticas"""
        stats = [
            self.vigor, self.mind, self.endurance, self.strength,
            self.dexterity, self.intelligence, self.faith, self.arcane
        ]
        return sum(s for s in stats if s is not None)


class ClassBase(BaseDocument):
    """
    Modelo base para clases iniciales de personaje.
    """
    name: str = Field(..., min_length=1, max_length=200, description="Nombre de la clase")
    image: Optional[str] = Field(default=None, description="URL de la imagen")
    description: Optional[str] = Field(default=None, description="Descripción de la clase")
    
    stats: Optional[CharacterStats] = Field(
        default=None,
        description="Estadísticas iniciales de la clase"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Normaliza el nombre de la clase"""
        return v.strip().title()

    @computed_field
    @property
    def starting_level(self) -> Optional[int]:
        """Nivel inicial de la clase"""
        if self.stats:
            return self.stats.level
        return None

    @computed_field
    @property
    def primary_stats(self) -> List[str]:
        """
        Identifica las estadísticas principales de la clase.
        Retorna las 2-3 stats más altas.
        """
        if not self.stats:
            return []
        
        stat_dict = {
            'Vigor': self.stats.vigor,
            'Mind': self.stats.mind,
            'Endurance': self.stats.endurance,
            'Strength': self.stats.strength,
            'Dexterity': self.stats.dexterity,
            'Intelligence': self.stats.intelligence,
            'Faith': self.stats.faith,
            'Arcane': self.stats.arcane
        }
        
        valid_stats = {k: v for k, v in stat_dict.items() if v is not None}
        
        if not valid_stats:
            return []
        
        sorted_stats = sorted(valid_stats.items(), key=lambda x: x[1], reverse=True)
        return [stat[0] for stat in sorted_stats[:3]]

    @computed_field
    @property
    def archetype(self) -> str:
        """
        Determina el arquetipo de la clase basándose en stats principales.
        """
        primary = self.primary_stats
        
        if not primary:
            return "Balanced"
        
        if 'Strength' in primary and 'Dexterity' in primary:
            return "Quality"
        elif 'Strength' in primary:
            return "Strength"
        elif 'Dexterity' in primary:
            return "Dexterity"
        elif 'Intelligence' in primary:
            return "Sorcerer"
        elif 'Faith' in primary:
            return "Cleric"
        elif 'Arcane' in primary:
            return "Occult"
        elif 'Mind' in primary or 'Vigor' in primary:
            return "Tank"
        
        return "Hybrid"


class ClassCreate(BaseDocument):
    """
    Modelo para crear una clase nueva.
    Usado en operaciones POST.
    """
    name: str = Field(..., min_length=1, max_length=200)
    image: Optional[str] = None
    description: Optional[str] = None
    stats: Optional[CharacterStats] = None


class ClassUpdate(BaseDocument):
    """
    Modelo para actualizar una clase.
    Todos los campos son opcionales (PATCH).
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    image: Optional[str] = None
    description: Optional[str] = None
    stats: Optional[CharacterStats] = None


class ClassInDB(ClassBase):
    """
    Modelo para clases almacenadas en la base de datos.
    """
    pass


class ClassResponse(ClassBase):
    """
    Modelo de respuesta para clases.
    Es lo que se retorna en los endpoints.
    """
    pass


class ClassListResponse(BaseDocument):
    """
    Modelo de respuesta para listados de clases con paginación.
    """
    items: List[ClassResponse] = Field(description="Lista de clases")
    total: int = Field(description="Total de registros")
    skip: int = Field(description="Registros omitidos")
    limit: int = Field(description="Límite de registros por página")


class ClassFilterParams(FilterParams):
    """
    Parámetros de filtrado específicos para clases.
    """
    min_level: Optional[int] = Field(
        default=None,
        ge=1,
        le=713,
        description="Nivel mínimo"
    )
    max_level: Optional[int] = Field(
        default=None,
        ge=1,
        le=713,
        description="Nivel máximo"
    )
    
    min_strength: Optional[int] = Field(
        default=None,
        ge=1,
        le=99,
        description="Fuerza mínima"
    )
    
    min_intelligence: Optional[int] = Field(
        default=None,
        ge=1,
        le=99,
        description="Inteligencia mínima"
    )
    
    min_faith: Optional[int] = Field(
        default=None,
        ge=1,
        le=99,
        description="Fe mínima"
    )
    
    archetype: Optional[str] = Field(
        default=None,
        description="Filtrar por arquetipo (Strength, Dexterity, Quality, Sorcerer, etc.)"
    )

    @field_validator('archetype')
    @classmethod
    def validate_archetype(cls, v: Optional[str]) -> Optional[str]:
        """Valida el arquetipo"""
        if v:
            valid_archetypes = [
                'Strength', 'Dexterity', 'Quality', 'Sorcerer', 
                'Cleric', 'Occult', 'Tank', 'Hybrid', 'Balanced'
            ]
            normalized = v.strip().title()
            if normalized not in valid_archetypes:
                raise ValueError(f"archetype debe ser uno de: {', '.join(valid_archetypes)}")
            return normalized
        return v


class ClassComparison(BaseDocument):
    """
    Modelo para comparar múltiples clases.
    """
    class_ids: List[str] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="IDs de clases a comparar"
    )
    
    compare_stats: List[str] = Field(
        default=['strength', 'dexterity', 'intelligence', 'faith'],
        description="Estadísticas a comparar"
    )

    @field_validator('class_ids')
    @classmethod
    def validate_class_ids(cls, v: List[str]) -> List[str]:
        """Valida que no haya IDs duplicados"""
        if len(v) != len(set(v)):
            raise ValueError("No se pueden comparar clases duplicadas")
        return v

    @field_validator('compare_stats')
    @classmethod
    def validate_compare_stats(cls, v: List[str]) -> List[str]:
        """Valida que las stats sean válidas"""
        valid_stats = [
            'vigor', 'mind', 'endurance', 'strength', 
            'dexterity', 'intelligence', 'faith', 'arcane'
        ]
        for stat in v:
            if stat.lower() not in valid_stats:
                raise ValueError(f"stat '{stat}' no es válida. Usar: {', '.join(valid_stats)}")
        return [s.lower() for s in v]


class BuildRecommendation(BaseDocument):
    """
    Modelo para recomendaciones de build basadas en una clase.
    """
    class_name: str = Field(description="Nombre de la clase")
    recommended_weapons: List[str] = Field(description="Armas recomendadas")
    recommended_spells: List[str] = Field(description="Hechizos recomendados")
    recommended_stats_priority: List[str] = Field(description="Prioridad de stats para levelear")
    playstyle: str = Field(description="Estilo de juego recomendado")