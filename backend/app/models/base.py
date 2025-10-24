from pydantic import BaseModel, Field, ConfigDict, field_validator, GetCoreSchemaHandler
from pydantic_core import core_schema
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(str):
    """Clase personalizada para manejar ObjectId de MongoDB en Pydantic."""
   
    @classmethod
    def __get_pydantic_core_schema__(cls, __source_type, __handler: GetCoreSchemaHandler):
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema()
        )

    @classmethod
    def validate(cls, v, _info=None):
        """Valida y convierte valores a ObjectId, retornando string para JSON."""
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return v
            raise ValueError("Invalid ObjectId format")
        raise ValueError("ObjectId must be a string or ObjectId instance")
    
    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, _handler):
        """Define cómo se mostrará en OpenAPI / JSON Schema."""
        return {"type": "string", "format": "objectid", "example": "507f1f77bcf86cd799439011"}
    
class BaseDocument(BaseModel):
    """Modelo base para todos los documentos de MongoDB."""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        str_strip_whitespace=True,
        validate_assignment=True,  
    )
    id: Optional[PyObjectId] = Field(default=None, alias="_id", description="Id de MongoDB")

    def model_dump_mongo(self, **kwargs) -> Dict[str, Any]:
        """Convierte el modelo a un diccionario compatible con MongoDB."""
        data = self.model_dump(
            by_alias=True,
            exclude_none=True,
            **kwargs
        )
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        return data

class AttackStats(BaseModel):
    """Modelo para estadísticas de ataques."""
    model_config = ConfigDict(str_strip_whitespace=True)

    physical: Optional[int] = Field(default=None, description="Dano Fisico")
    magic: Optional[int] = Field(default=None, description="Dano Magico")    
    fire: Optional[int] = Field(default=None, ge=0, description="Daño de fuego")
    lightning: Optional[int] = Field(default=None, ge=0, description="Daño eléctrico")
    holy: Optional[int] = Field(default=None, ge=0, description="Daño sagrado")
    critical: Optional[int] = Field(default=None, ge=0, description="Daño crítico")
    status_effects: Optional[Dict[str, int]] = Field(default=None, description="Efectos de estado y sus probabilidades")

    def total_damage(self) -> int:
        """Calcula el daño total sumando todos los tipos de daño."""
        return sum(
            v for v in [
                self.physical, self.magic, self.fire,
                self.lightning, self.holy
            ] if v is not None
        )

class DefenseStats(BaseModel):
    """
    Modelo para estadísticas de defensa.
    Usado en armaduras, escudos, etc.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    physical: Optional[float] = Field(default=None, ge=0, description="Defensa física")
    strike: Optional[float] = Field(default=None, ge=0, description="Defensa contra golpes")
    slash: Optional[float] = Field(default=None, ge=0, description="Defensa contra cortes")
    pierce: Optional[float] = Field(default=None, ge=0, description="Defensa contra perforaciones")
    magic: Optional[float] = Field(default=None, ge=0, description="Defensa mágica")
    fire: Optional[float] = Field(default=None, ge=0, description="Defensa contra fuego")
    lightning: Optional[float] = Field(default=None, ge=0, description="Defensa eléctrica")
    holy: Optional[float] = Field(default=None, ge=0, description="Defensa sagrada")

class ResistanceStats(BaseModel):
    """
    Modelo para resistencias a efectos de estado.
    Usado en armaduras principalmente.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    immunity: Optional[int] = Field(default=None, ge=0, description="Inmunidad")
    robustness: Optional[int] = Field(default=None, ge=0, description="Robustez")
    focus: Optional[int] = Field(default=None, ge=0, description="Concentración")
    vitality: Optional[int] = Field(default=None, ge=0, description="Vitalidad")
    poise: Optional[float] = Field(default=None, ge=0, description="Firmeza")


class RequirementStats(BaseModel):
    """
    Modelo para requerimientos de atributos.
    Usado en armas, hechizos, etc.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    strength: Optional[int] = Field(default=None, ge=0, le=99, description="Fuerza requerida")
    dexterity: Optional[int] = Field(default=None, ge=0, le=99, description="Destreza requerida")
    intelligence: Optional[int] = Field(default=None, ge=0, le=99, description="Inteligencia requerida")
    faith: Optional[int] = Field(default=None, ge=0, le=99, description="Fe requerida")
    arcane: Optional[int] = Field(default=None, ge=0, le=99, description="Arcano requerido")

    def total_requirements(self) -> int:
        """Suma total de todos los requerimientos"""
        return sum(
            v for v in [
                self.strength, self.dexterity, self.intelligence,
                self.faith, self.arcane
            ] if v is not None
        )


class ScalingStats(BaseModel):
    """
    Modelo para escalado de atributos.
    Usado en armas principalmente.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    strength: Optional[str] = Field(default=None, description="Escalado de fuerza (E, D, C, B, A, S)")
    dexterity: Optional[str] = Field(default=None, description="Escalado de destreza")
    intelligence: Optional[str] = Field(default=None, description="Escalado de inteligencia")
    faith: Optional[str] = Field(default=None, description="Escalado de fe")
    arcane: Optional[str] = Field(default=None, description="Escalado de arcano")

    @field_validator('strength', 'dexterity', 'intelligence', 'faith', 'arcane')
    @classmethod
    def validate_scaling(cls, v: Optional[str]) -> Optional[str]:
        """Valida que el escalado sea una letra válida"""
        if v is None:
            return v
        valid_grades = ['E', 'D', 'C', 'B', 'A', 'S', '-']
        if v.upper() not in valid_grades:
            raise ValueError(f"Escalado debe ser uno de: {', '.join(valid_grades)}")
        return v.upper()


class PaginationParams(BaseModel):
    """
    Modelo para parámetros de paginación.
    Usado en queries de listado.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    skip: int = Field(default=0, ge=0, description="Número de registros a omitir")
    limit: int = Field(default=20, ge=1, le=100, description="Número máximo de registros")
    sort_by: Optional[str] = Field(default=None, description="Campo por el cual ordenar")
    sort_order: int = Field(default=1, description="Orden: 1 (ascendente) o -1 (descendente)")

    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v: int) -> int:
        """Valida que el orden sea 1 o -1"""
        if v not in [1, -1]:
            raise ValueError("sort_order debe ser 1 (ascendente) o -1 (descendente)")
        return v

class FilterParams(BaseModel):
    """
    Modelo base para filtros de búsqueda.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, description="Filtrar por nombre (búsqueda parcial)")
    category: Optional[str] = Field(default=None, description="Filtrar por categoría")
    min_weight: Optional[float] = Field(default=None, ge=0, description="Peso mínimo")
    max_weight: Optional[float] = Field(default=None, ge=0, description="Peso máximo")

    @field_validator('max_weight')
    @classmethod
    def validate_weight_range(cls, v: Optional[float], info) -> Optional[float]:
        """Valida que max_weight sea mayor que min_weight"""
        if v is not None and info.data.get('min_weight') is not None:
            if v < info.data['min_weight']:
                raise ValueError("max_weight debe ser mayor que min_weight")
        return v