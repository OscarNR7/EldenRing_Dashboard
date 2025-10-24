from fastapi import APIRouter, Depends, Path, status, Body
from typing import List, Optional
import logging

from app.services.classes import class_service
from app.models.classes import (
    ClassResponse,
    ClassCreate,
    ClassUpdate,
    ClassListResponse,
    ClassFilterParams
)
from app.models.base import PaginationParams
from app.models.responses import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/",
    response_model=ClassListResponse,
    summary="Obtener lista de clases",
    description="Retorna una lista paginada de clases con filtros opcionales",
    tags=["Classes - CRUD"],
    status_code=status.HTTP_200_OK
)
async def get_classes(
    filters: ClassFilterParams = Depends(),
    pagination: PaginationParams = Depends(),
):
    """
    Obtiene una lista paginada de clases con filtros opcionales.
    """
    logger.info(f"Obteniendo clases con filtros: {filters} y paginación: {pagination}")
    result = await class_service.get_classes(filters, pagination)
    return ClassListResponse(**result)

@router.post(
    "/",
    response_model=ClassResponse,
    summary="Crear clase",
    description="Crea una clase nueva",
    tags=["Classes - CRUD"],
    status_code=status.HTTP_201_CREATED
)
async def create_class(class_data: ClassCreate):
    """
    Crea una clase nueva en la base de datos.
    """
    logger.info(f"Creando nueva clase: {class_data.name}")
    return await class_service.create(class_data)

@router.get(
    "/by-id/{class_id}",
    response_model=ClassResponse,
    summary="Obtener clase por ID",
    description="Retorna una clase específica por su ID",
    tags=["Classes - CRUD"]
)
async def get_class_by_id(
    class_id: str = Path(..., description="ID de la clase", example="507f1f77bcf86cd799439011")
):
    """
    Obtiene una clase por su ID de MongoDB.
    """
    logger.info(f"Obteniendo clase con ID: {class_id}")
    return await class_service.get_by_id(class_id)

@router.patch(
    "/{class_id}",
    response_model=ClassResponse,
    summary="Actualizar clase",
    description="Actualiza parcialmente una clase existente",
    tags=["Classes - CRUD"]
)
async def update_class(
    class_id: str = Path(..., description="ID de la clase"),
    class_update: ClassUpdate = Body(..., description="Datos a actualizar de la clase")
):
    """
    Actualiza campos específicos de una clase (PATCH).
    """
    logger.info(f"Actualizando clase con ID: {class_id} y datos: {class_update.model_dump(exclude_unset=True)}")
    update_data = class_update.model_dump(exclude_unset=True)
    return await class_service.update(class_id, update_data)

@router.delete(
    "/{class_id}",
    response_model=MessageResponse,
    summary="Eliminar clase",
    description="Elimina una clase de la base de datos",
    tags=["Classes - CRUD"],
    status_code=status.HTTP_200_OK
)
async def delete_class(
    class_id: str = Path(..., description="ID de la clase a eliminar")
):
    """
    Elimina una clase de la base de datos.
    """
    logger.info(f"Eliminando clase con ID: {class_id}")
    result = await class_service.delete(class_id)
    return MessageResponse(message=result["message"])
