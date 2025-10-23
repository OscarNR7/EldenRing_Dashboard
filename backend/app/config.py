import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

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
    CORS_ORIGINS: List[str] = Field(
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
        Parsea CORS_ORIGINS si viene como string separado por comas
        """
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS

# Instancia global de configuración
settings = Settings()

# Log de configuración inicial (solo en desarrollo)
if settings.is_development:
    print(f"Configuración cargada:")
    print(f"   - Base de datos: {settings.DATABASE_NAME}")
    print(f"   - Puerto: {settings.PORT}")
    print(f"   - Entorno: {settings.ENVIRONMENT}")
    print(f"   - CORS Origins: {settings.get_cors_origins()}")