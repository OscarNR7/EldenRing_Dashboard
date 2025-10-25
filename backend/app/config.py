import os
import json
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
import logging

# Cargar variables de entorno
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Configuración centralizada de la aplicación usando Pydantic Settings.
    Lee las variables desde el archivo .env
    """
    
    # MongoDB (valores por defecto - se sobrescriben con .env)
    MONGO_URI: str = Field(
        default="mongodb://localhost:27017/",
        description="URI de conexión a MongoDB (local o Atlas)"
    )
    DATABASE_NAME: str = Field(
        default="eldenring_db",
        description="Nombre de la base de datos"
    )
    
    # API
    API_V1_PREFIX: str = Field(default="/api/v1")
    PROJECT_NAME: str = Field(default="Elden Ring Analytics API")
    VERSION: str = Field(default="1.0.0")
    DESCRIPTION: str = Field(
        default="API REST para análisis de datos de Elden Ring - Stack FARM"
    )
    
    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    RELOAD: bool = Field(default=True)
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )
    
    # Environment
    ENVIRONMENT: str = Field(default="development")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    
    # Paginación por defecto
    DEFAULT_PAGE_SIZE: int = Field(default=20)
    MAX_PAGE_SIZE: int = Field(default=100)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"
    
    @property
    def is_development(self) -> bool:
        """Verifica si estamos en desarrollo"""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Verifica si estamos en producción"""
        return self.ENVIRONMENT.lower() == "production"
    
    def get_cors_origins(self) -> List[str]:
        """
        Parsea CORS_ORIGINS desde una variable de entorno.
        Puede ser una lista en el código, un string JSON o un string separado por comas.
        """
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS

        if isinstance(self.CORS_ORIGINS, str):
            # Intentar parsear como JSON
            if self.CORS_ORIGINS.startswith("[") and self.CORS_ORIGINS.endswith("]"):
                try:
                    return json.loads(self.CORS_ORIGINS)
                except json.JSONDecodeError:
                    logger.warning(
                        "CORS_ORIGINS parece ser un JSON pero no se pudo parsear. "
                        "Tratando como string separado por comas."
                    )
            
            # Tratar como string separado por comas
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

        # Fallback a una lista vacía si el tipo no es manejado
        return []

# Instancia global de configuración
settings = Settings()

# Log de configuración inicial (solo en desarrollo)
if settings.is_development:
    logger = logging.getLogger(__name__)
    logger.info(f"Configuración cargada: {settings.DATABASE_NAME}")