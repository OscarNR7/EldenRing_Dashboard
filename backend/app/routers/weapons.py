from fastapi import APIRouter, Depends, Query, Path, status
from typing import List, Optional
import logging

from app.services.weapons import weapon_service
from app.models.weapons import (
    WeaponResponse,
    WeaponCreate,
    WeaponUpdate,
    WeaponListResponse,
    WeaponFilterParams,
    WeaponStatsComparison
)
from app.models.base import PaginationParams
from app.models.responses import (
    SuccessResponse,
    MessageResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/",
    response_model=WeaponListResponse,
    summary="Obtener lista de armas",
    description="Retorna una lista paginada de armas con filtros opcionales",
    tags=["Weapons - CRUD"],
    status_code=status.HTTP_200_OK
)
async def get_weapons(
    filters: WeaponFilterParams = Depends(),
    pagination: PaginationParams = Depends(),
):
    """
    Obtiene una lista paginada de armas con filtros opcionales

    GET /api/v1/weapons?category=Katana&min_damage=50&limit=10

    """
    result = await weapon_service.get_weapons(filters, pagination)
    return WeaponListResponse(**result)

