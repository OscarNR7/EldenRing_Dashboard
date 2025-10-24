from fastapi import APIRouter, Depends, Path, status, Body
from typing import List, Optional
import logging

from app.services.armors import armor_service
from app.models.armors import (
    ArmorResponse,
    ArmorCreate,
    ArmorUpdate,
    ArmorListResponse,
    ArmorFilterParams
)
from app.models.base import PaginationParams
from app.models.responses import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/",
    response_model=ArmorListResponse,
    summary="Obtener lista de armaduras",
    description="Retorna una lista paginada de armaduras con filtros opcionales",
    tags=["Armors - CRUD"],
    status_code=status.HTTP_200_OK
)
async def get_armors(
    filters: ArmorFilterParams = Depends(),
    pagination: PaginationParams = Depends(),
):
    """
    Obtiene una lista paginada de armaduras con filtros opcionales.
    """
    logger.info(f"Obteniendo armaduras con filtros: {filters} y paginación: {pagination}")
    result = await armor_service.get_armors(filters, pagination)
    return ArmorListResponse(**result)

@router.post(
    "/",
    response_model=ArmorResponse,
    summary="Crear armadura",
    description="Crea una armadura nueva",
    tags=["Armors - CRUD"],
    status_code=status.HTTP_201_CREATED
)
async def create_armor(armor: ArmorCreate):
    """
    Crea una armadura nueva en la base de datos.
    """
    logger.info(f"Creando nueva armadura: {armor.name}")
    return await armor_service.create(armor)

@router.get(
    "/by-id/{armor_id}",
    response_model=ArmorResponse,
    summary="Obtener armadura por ID",
    description="Retorna una armadura específica por su ID",
    tags=["Armors - CRUD"]
)
async def get_armor_by_id(
    armor_id: str = Path(..., description="ID de la armadura", example="507f1f77bcf86cd799439011")
):
    """
    Obtiene una armadura por su ID de MongoDB.
    """
    logger.info(f"Obteniendo armadura con ID: {armor_id}")
    return await armor_service.get_by_id(armor_id)

@router.patch(
    "/{armor_id}",
    response_model=ArmorResponse,
    summary="Actualizar armadura",
    description="Actualiza parcialmente una armadura existente",
    tags=["Armors - CRUD"]
)
async def update_armor(
    armor_id: str = Path(..., description="ID de la armadura"),
    armor_update: ArmorUpdate = Body(..., description="Datos a actualizar de la armadura")
):
    """
    Actualiza campos específicos de una armadura (PATCH).
    """
    logger.info(f"Actualizando armadura con ID: {armor_id} y datos: {armor_update.model_dump(exclude_unset=True)}")
    update_data = armor_update.model_dump(exclude_unset=True)
    return await armor_service.update(armor_id, update_data)

@router.delete(
    "/{armor_id}",
    response_model=MessageResponse,
    summary="Eliminar armadura",
    description="Elimina una armadura de la base de datos",
    tags=["Armors - CRUD"],
    status_code=status.HTTP_200_OK
)
async def delete_armor(
    armor_id: str = Path(..., description="ID de la armadura a eliminar")
):
    """
    Elimina una armadura de la base de datos.
    """
    logger.info(f"Eliminando armadura con ID: {armor_id}")
    result = await armor_service.delete(armor_id)
    return MessageResponse(message=result["message"])
