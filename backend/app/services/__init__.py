"""
Servicios de la aplicación.
Capa de lógica de negocio entre routers y base de datos.
"""

from app.services.base_service import BaseService
from app.services.weapons import weapon_service
from app.services.bosses import boss_service
from app.services.armors import armor_service
from app.services.classes import class_service

__all__ = [
    "BaseService",
    "weapon_service",
    "boss_service",
    "armor_service",
    "class_service",
]