from fastapi import APIRouter, Depends, Path, status, Body
from typing import List, Optional
import logging

from app.services.bosses import boss_service
from app.models.bosses import (
    BossResponse,
    BossCreate,
    BossUpdate,
    BossListResponse,
    BossFilterParams
)
from app.models.base import PaginationParams
from app.models.responses import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/",
    response_model=BossListResponse,
    summary="Obtener lista de jefes",
    description="Retorna una lista paginada de jefes con filtros opcionales",
    tags=["Bosses - CRUD"],
    status_code=status.HTTP_200_OK
)
async def get_bosses(
    filters: BossFilterParams = Depends(),
    pagination: PaginationParams = Depends(),
):
    """
    Obtiene una lista paginada de jefes con filtros opcionales.
    """
    logger.info(f"Obteniendo jefes con filtros: {filters} y paginación: {pagination}")
    result = await boss_service.get_bosses(filters, pagination)
    return BossListResponse(**result)

@router.post(
    "/",
    response_model=BossResponse,
    summary="Crear jefe",
    description="Crea un jefe nuevo",
    tags=["Bosses - CRUD"],
    status_code=status.HTTP_201_CREATED
)
async def create_boss(boss: BossCreate):
    """
    Crea un jefe nuevo en la base de datos.
    """
    logger.info(f"Creando nuevo jefe: {boss.name}")
    return await boss_service.create(boss)

@router.get(
    "/by-id/{boss_id}",
    response_model=BossResponse,
    summary="Obtener jefe por ID",
    description="Retorna un jefe específico por su ID",
    tags=["Bosses - CRUD"]
)
async def get_boss_by_id(
    boss_id: str = Path(..., description="ID del jefe", example="507f1f77bcf86cd799439011")
):
    """
    Obtiene un jefe por su ID de MongoDB.
    """
    logger.info(f"Obteniendo jefe con ID: {boss_id}")
    return await boss_service.get_by_id(boss_id)

@router.patch(
    "/{boss_id}",
    response_model=BossResponse,
    summary="Actualizar jefe",
    description="Actualiza parcialmente un jefe existente",
    tags=["Bosses - CRUD"]
)
async def update_boss(
    boss_id: str = Path(..., description="ID del jefe"),
    boss_update: BossUpdate = Body(..., description="Datos a actualizar del jefe")
):
    """
    Actualiza campos específicos de un jefe (PATCH).
    """
    logger.info(f"Actualizando jefe con ID: {boss_id} y datos: {boss_update.model_dump(exclude_unset=True)}")
    update_data = boss_update.model_dump(exclude_unset=True)
    return await boss_service.update(boss_id, update_data)

@router.delete(
    "/{boss_id}",
    response_model=MessageResponse,
    summary="Eliminar jefe",
    description="Elimina un jefe de la base de datos",
    tags=["Bosses - CRUD"],
    status_code=status.HTTP_200_OK
)
async def delete_boss(
    boss_id: str = Path(..., description="ID del jefe a eliminar")
):
    """
    Elimina un jefe de la base de datos.
    """
    logger.info(f"Eliminando jefe con ID: {boss_id}")
    result = await boss_service.delete(boss_id)
    return MessageResponse(message=result["message"])
