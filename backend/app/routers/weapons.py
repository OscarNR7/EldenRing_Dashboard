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
    Obtiene una lista paginada de armas con filtros opcionales.
    
    **Ejemplos de uso:**
    ```
    GET /api/v1/weapons?category=Katana&min_damage=50&limit=10
    GET /api/v1/weapons?min_strength=20&max_strength=40
    GET /api/v1/weapons?has_passive=true
    ```
    """
    result = await weapon_service.get_weapons(filters, pagination)
    return WeaponListResponse(**result)

@router.get(
    "/categories",
    response_model=List[str],
    summary="Obtener todas las categorías",
    description="Retorna lista de todas las categorías únicas de armas",
    tags=["Weapons - Queries"]
)
async def get_weapon_categories():
    """
    Obtiene todas las categorías disponibles de armas.
    
    **Útil para:**
    - Debugging
    - Validación de búsquedas
    - Construcción de filtros en frontend
    
    **Ejemplo de uso:**
    ```
    GET /api/v1/weapons/categories
    ```
    """
    return await weapon_service.get_all_categories()

@router.get(
    "/category/{category}",
    response_model=List[WeaponResponse],
    summary="Obtener armas por categoría",
    description="Retorna todas las armas de una categoría específica",
    tags=["Weapons - Queries"]
)
async def get_weapons_by_category(
    category: str = Path(
        ...,
        description="Categoría de arma (case-insensitive)",
        examples={
            "katana": {"value": "Katana"},
            "greatsword": {"value": "Greatsword"},
            "axe": {"value": "Axe"}
        }
    )
):
    """
    Obtiene todas las armas de una categoría.
    
    La búsqueda es case-insensitive, por lo que "katana", "Katana" y "KATANA" 
    retornarán los mismos resultados.
    
    **Categorías comunes:**
    - Dagger, Straight Sword, Greatsword, Colossal Sword
    - Curved Sword, Katana, Twinblade
    - Hammer, Great Hammer, Flail
    - Axe, Greataxe, Spear, Great Spear
    - Halberd, Reaper, Whip, Fist, Claw
    
    **Ejemplo de uso:**
    ```
    GET /api/v1/weapons/category/Katana
    GET /api/v1/weapons/category/hammer  # case-insensitive
    ```
    """
    weapons = await weapon_service.get_by_category(category)
    
    if not weapons:
        logger.warning(f"No se encontraron armas para categoría: {category}")
        return []
    
    return weapons

@router.get(
    "/by-id/{weapon_id}",
    response_model=WeaponResponse,
    summary="Obtener arma por ID",
    description="Retorna un arma específica por su ID",
    tags=["Weapons - CRUD"]
)
async def get_weapon_by_id(
    weapon_id: str = Path(
        ...,
        description="ID del arma",
        example="507f1f77bcf86cd799439011"
    )
):
    """
    Obtiene un arma por su ID de MongoDB.
    
    **Ejemplo de uso:**
    ```
    GET /api/v1/weapons/by-id/507f1f77bcf86cd799439011
    ```
    """
    return await weapon_service.get_by_id(weapon_id)


# Endpoint deshabilitado temporalmente por estructura de datos incompatible:
@router.get(
    "/best-damage-to-weight",
    response_model=List[dict],
    summary="Armas con mejor ratio daño/peso",
    description="Retorna armas ordenadas por mejor relación daño/peso",
    tags=["Weapons - Analytics"]
)
async def get_best_damage_to_weight_weapons(
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Número de armas a retornar"
    ),
    category: Optional[str] = Query(
        default=None,
        description="Filtrar por categoría (opcional)"
    )
):
    """
    Obtiene las armas con mejor relación daño/peso.
    
    Útil para encontrar armas eficientes que maximizan el daño
    sin penalizar demasiado el equip load.
    
    **Ejemplo de uso:**
    ```
    GET /api/v1/weapons/best-damage-to-weight?limit=10
    GET /api/v1/weapons/best-damage-to-weight?limit=5&category=Katana
    ```
    """
    return await weapon_service.get_best_damage_to_weight(limit, category)

@router.post(
    "/compare",
    response_model=dict,
    summary="Comparar armas",
    description="Compara estadísticas entre 2-5 armas",
    tags=["Weapons - Analytics"]
)
async def compare_weapons(
    comparison: WeaponStatsComparison
):
    """
    Compara múltiples armas mostrando sus estadísticas lado a lado.
    
    **Límites:**
    - Mínimo: 2 armas
    - Máximo: 5 armas
    
    **Retorna:**
    - Comparación de daño
    - Comparación de peso
    - Ratio daño/peso
    - Ganador por cada métrica
    
    **Ejemplo de uso:**
    ```json
    POST /api/v1/weapons/compare
    {
      "weapon_ids": [
        "507f1f77bcf86cd799439011",
        "507f1f77bcf86cd799439012"
      ]
    }
    ```
    """
    return await weapon_service.compare_weapons(comparison)

@router.get(
    "/by-build/{build_type}",
    response_model=List[WeaponResponse],
    summary="Armas recomendadas por build",
    description="Retorna armas óptimas para un tipo de build específico",
    tags=["Weapons - Analytics"]
)
async def get_weapons_by_build_type(
    build_type: str = Path(
        ...,
        description="Tipo de build",
        examples={
            "strength": {"value": "strength"},
            "dexterity": {"value": "dexterity"},
            "quality": {"value": "quality"},
            "intelligence": {"value": "intelligence"},
            "faith": {"value": "faith"}
        }
    )
):
    """
    Obtiene armas recomendadas para un tipo de build.
    
    **Tipos de build soportados:**
    - **strength**: Armas con escalado A/S en Fuerza
    - **dexterity**: Armas con escalado A/S en Destreza
    - **quality**: Armas con buen escalado en STR y DEX
    - **intelligence**: Armas mágicas con escalado A/S en INT
    - **faith**: Armas sagradas con escalado A/S en FE
    - **arcane**: Armas con escalado A/S en Arcano
    
    **Ejemplo de uso:**
    ```
    GET /api/v1/weapons/by-build/strength
    GET /api/v1/weapons/by-build/quality
    ```
    """
    return await weapon_service.get_by_build_type(build_type)

@router.get(
    "/statistics",
    response_model=dict,
    summary="Estadísticas de armas",
    description="Retorna estadísticas agregadas de todas las armas",
    tags=["Weapons - Analytics"]
)
async def get_weapon_statistics():
    """
    Obtiene estadísticas generales del arsenal de armas.
    
    **Incluye:**
    - Distribución por categoría
    - Promedios de peso y daño
    - Top 5 armas con mayor daño
    - Total de armas disponibles
    
    **Ejemplo de uso:**
    ```
    GET /api/v1/weapons/statistics
    ```
    """
    return await weapon_service.get_statistics()

@router.post(
    "/",
    response_model=WeaponResponse,
    summary="Crear arma",
    description="Crea un arma nueva",
    tags=["Weapons - CRUD"],
    status_code=status.HTTP_201_CREATED
)
async def create_weapon(weapon: WeaponCreate):
    """
    Crea un arma nueva en la base de datos.
    
    **Ejemplo de uso:**
    ```json
    POST /api/v1/weapons
    {
      "name": "Custom Sword",
      "category": "Straight Sword",
      "weight": 5.0,
      "attack": {
        "physical": 120,
        "magic": 0
      },
      "requiredAttributes": {
        "strength": 15,
        "dexterity": 12
      }
    }
    ```
    """
    return await weapon_service.create(weapon)

@router.patch(
    "/{weapon_id}",
    response_model=WeaponResponse,
    summary="Actualizar arma",
    description="Actualiza parcialmente un arma existente",
    tags=["Weapons - CRUD"]
)
async def update_weapon(
    weapon_id: str = Path(..., description="ID del arma"),
    weapon_update: WeaponUpdate = None
):
    """
    Actualiza campos específicos de un arma (PATCH).
    
    Solo se actualizan los campos proporcionados.
    
    **Ejemplo de uso:**
    ```json
    PATCH /api/v1/weapons/507f1f77bcf86cd799439011
    {
      "weight": 6.0,
      "attack": {
        "physical": 125
      }
    }
    ```
    """
    update_data = weapon_update.model_dump(exclude_unset=True)
    return await weapon_service.update(weapon_id, update_data)

@router.delete(
    "/{weapon_id}",
    response_model=MessageResponse,
    summary="Eliminar arma",
    description="Elimina un arma de la base de datos",
    tags=["Weapons - CRUD"],
    status_code=status.HTTP_200_OK
)
async def delete_weapon(
    weapon_id: str = Path(..., description="ID del arma a eliminar")
):
    """
    Elimina un arma de la base de datos.
    
    **Advertencia:** Esta operación no se puede deshacer.
    
    **Ejemplo de uso:**
    ```
    DELETE /api/v1/weapons/507f1f77bcf86cd799439011
    ```
    """
    result = await weapon_service.delete(weapon_id)
    return MessageResponse(message=result["message"])