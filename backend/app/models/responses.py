from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')


class SuccessResponse(BaseModel, Generic[T]):
    """
    Modelo genérico para respuestas exitosas.
    """
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")
    message: str = Field(description="Mensaje descriptivo")
    data: Optional[T] = Field(default=None, description="Datos de respuesta")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de la respuesta")


class ErrorDetail(BaseModel):
    """
    Modelo para detalles de error.
    """
    field: Optional[str] = Field(default=None, description="Campo que causó el error")
    message: str = Field(description="Mensaje de error")
    type: Optional[str] = Field(default=None, description="Tipo de error")


class ErrorResponse(BaseModel):
    """
    Modelo para respuestas de error.
    """
    success: bool = Field(default=False, description="Indica que la operación falló")
    error: str = Field(description="Tipo de error")
    message: str = Field(description="Mensaje de error")
    details: Optional[List[ErrorDetail]] = Field(default=None, description="Detalles específicos del error")
    path: Optional[str] = Field(default=None, description="Path del endpoint")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp del error")


class ValidationErrorResponse(ErrorResponse):
    """
    Modelo específico para errores de validación.
    """
    error: str = Field(default="Validation Error", description="Tipo de error")


class NotFoundErrorResponse(ErrorResponse):
    """
    Modelo específico para errores 404.
    """
    error: str = Field(default="Not Found", description="Tipo de error")
    resource: Optional[str] = Field(default=None, description="Recurso no encontrado")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Modelo genérico para respuestas paginadas.
    """
    items: List[T] = Field(description="Lista de items")
    total: int = Field(ge=0, description="Total de registros")
    page: int = Field(ge=1, description="Página actual")
    page_size: int = Field(ge=1, description="Tamaño de página")
    total_pages: int = Field(ge=0, description="Total de páginas")
    has_next: bool = Field(description="Indica si hay siguiente página")
    has_previous: bool = Field(description="Indica si hay página anterior")


class AggregationResponse(BaseModel):
    """
    Modelo para respuestas de agregaciones/estadísticas.
    """
    aggregation_type: str = Field(description="Tipo de agregación")
    results: Dict[str, Any] = Field(description="Resultados de la agregación")
    count: int = Field(ge=0, description="Número de documentos agregados")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")


class BulkOperationResponse(BaseModel):
    """
    Modelo para respuestas de operaciones en bulk.
    """
    success: bool = Field(description="Indica si la operación fue exitosa")
    total_processed: int = Field(ge=0, description="Total de registros procesados")
    successful: int = Field(ge=0, description="Registros procesados exitosamente")
    failed: int = Field(ge=0, description="Registros que fallaron")
    errors: Optional[List[ErrorDetail]] = Field(default=None, description="Detalles de errores")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")


class HealthCheckResponse(BaseModel):
    """
    Modelo para respuesta de health check.
    """
    status: str = Field(description="Estado del servicio: healthy, degraded, unhealthy")
    version: str = Field(description="Versión de la API")
    environment: str = Field(description="Entorno: development, production")
    database: Dict[str, Any] = Field(description="Estado de la base de datos")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")


class ComparisonResponse(BaseModel):
    """
    Modelo para respuestas de comparación entre items.
    """
    comparison_type: str = Field(description="Tipo de comparación: weapons, armors, classes, etc.")
    items_compared: int = Field(ge=2, description="Número de items comparados")
    comparison_data: Dict[str, Any] = Field(description="Datos de la comparación")
    winner: Optional[Dict[str, Any]] = Field(default=None, description="Item ganador si aplica")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")


class OptimizationResponse(BaseModel):
    """
    Modelo para respuestas de optimización.
    """
    optimization_type: str = Field(description="Tipo de optimización")
    criteria: Dict[str, Any] = Field(description="Criterios de optimización usados")
    recommended_items: List[Dict[str, Any]] = Field(description="Items recomendados")
    score: Optional[float] = Field(default=None, description="Score de optimización")
    alternatives: Optional[List[Dict[str, Any]]] = Field(default=None, description="Alternativas")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")


class StatisticsResponse(BaseModel):
    """
    Modelo para respuestas de estadísticas generales.
    """
    total_weapons: Optional[int] = Field(default=None, description="Total de armas")
    total_armors: Optional[int] = Field(default=None, description="Total de armaduras")
    total_bosses: Optional[int] = Field(default=None, description="Total de jefes")
    total_spells: Optional[int] = Field(default=None, description="Total de hechizos")
    total_classes: Optional[int] = Field(default=None, description="Total de clases")
    total_items: Optional[int] = Field(default=None, description="Total de items")
    database_size: Optional[str] = Field(default=None, description="Tamaño de la base de datos")
    last_updated: Optional[datetime] = Field(default=None, description="Última actualización")


class MessageResponse(BaseModel):
    """
    Modelo simple para respuestas con solo un mensaje.
    """
    message: str = Field(description="Mensaje de respuesta")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")