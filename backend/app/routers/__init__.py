# backend/app/routers/__init__.py

from app.routers import weapons
from app.routers import bosses
from app.routers import armors
from app.routers import classes
from app.routers import analytics

__all__ = [
    "weapons",
    "bosses",
    "armors",
    "classes",
    "analytics"
]