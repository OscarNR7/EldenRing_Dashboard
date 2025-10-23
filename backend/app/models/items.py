from pydantic import Field, field_validator, computed_field
from typing import Optional, List
from app.models.base import BaseDocument, FilterParams


class ItemBase(BaseDocument):
    """
    Modelo base para items consumibles y materiales.
    """
    name: str = Field(..., min_length=1, max_length=200, description="Nombre del item")
    image: Optional[str] = Field(default=None, description="URL de la imagen")
    description: Optional[str] = Field(default=None, description="Descripción del item")
    type: Optional[str] = Field(default=None, description="Tipo de item")
    effect: Optional[str] = Field(default=None, description="Efecto del item")

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza el tipo de item"""
        if v:
            return v.strip().title()
        return v


class ItemCreate(BaseDocument):
    """
    Modelo para crear un item nuevo.
    Usado en operaciones POST.
    """
    name: str = Field(..., min_length=1, max_length=200)
    image: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    effect: Optional[str] = None


class ItemUpdate(BaseDocument):
    """
    Modelo para actualizar un item.
    Todos los campos son opcionales (PATCH).
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    image: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    effect: Optional[str] = None


class ItemInDB(ItemBase):
    """
    Modelo para items almacenados en la base de datos.
    """
    pass


class ItemResponse(ItemBase):
    """
    Modelo de respuesta para items.
    Es lo que se retorna en los endpoints.
    """
    pass


class ItemListResponse(BaseDocument):
    """
    Modelo de respuesta para listados de items con paginación.
    """
    items: List[ItemResponse] = Field(description="Lista de items")
    total: int = Field(description="Total de registros")
    skip: int = Field(description="Registros omitidos")
    limit: int = Field(description="Límite de registros por página")


class ItemFilterParams(FilterParams):
    """
    Parámetros de filtrado específicos para items.
    """
    item_type: Optional[str] = Field(
        default=None,
        description="Filtrar por tipo de item"
    )
    
    has_effect: Optional[bool] = Field(
        default=None,
        description="Filtrar items con efecto"
    )


class TalismanBase(BaseDocument):
    """
    Modelo base para talismanes.
    """
    name: str = Field(..., min_length=1, max_length=200, description="Nombre del talismán")
    image: Optional[str] = Field(default=None, description="URL de la imagen")
    description: Optional[str] = Field(default=None, description="Descripción del talismán")
    effect: Optional[str] = Field(default=None, description="Efecto del talismán")


class TalismanCreate(BaseDocument):
    """
    Modelo para crear un talismán nuevo.
    """
    name: str = Field(..., min_length=1, max_length=200)
    image: Optional[str] = None
    description: Optional[str] = None
    effect: Optional[str] = None


class TalismanUpdate(BaseDocument):
    """
    Modelo para actualizar un talismán.
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    image: Optional[str] = None
    description: Optional[str] = None
    effect: Optional[str] = None


class TalismanInDB(TalismanBase):
    """
    Modelo para talismanes almacenados en la base de datos.
    """
    pass


class TalismanResponse(TalismanBase):
    """
    Modelo de respuesta para talismanes.
    """
    pass


class TalismanListResponse(BaseDocument):
    """
    Modelo de respuesta para listados de talismanes con paginación.
    """
    items: List[TalismanResponse] = Field(description="Lista de talismanes")
    total: int = Field(description="Total de registros")
    skip: int = Field(description="Registros omitidos")
    limit: int = Field(description="Límite de registros por página")