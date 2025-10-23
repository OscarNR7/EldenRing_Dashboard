from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    """
    Clase para manejar la conexión a MongoDB de forma singleton.
    Garantiza una única conexión reutilizable en toda la aplicación.
    """
    
    client: Optional[MongoClient] = None
    database = None
    
    @classmethod
    def connect(cls):
        """
        Establece conexión con MongoDB
        """
        try:
            if cls.client is None:
                logger.info(f"Conectando a MongoDB: {settings.DATABASE_NAME}")
                
                cls.client = MongoClient(
                    settings.MONGO_URI,
                    serverSelectionTimeoutMS=5000,  # Timeout de 5 segundos (Atlas puede tardar más) - cambiar a 10000 en producción si es necesario
                    connectTimeoutMS=20000,
                    socketTimeoutMS=20000,
                    maxPoolSize=50,
                    minPoolSize=10,
                    retryWrites=True,
                    w='majority'
                )
                
                # Verificar conexión
                cls.client.admin.command('ping')
                cls.database = cls.client[settings.DATABASE_NAME]
                
                # Log de colecciones disponibles
                collections = cls.database.list_collection_names()
                logger.info(f"Conexión exitosa a MongoDB")
                logger.info(f"Colecciones disponibles: {len(collections)}")
                
                if settings.is_development:
                    logger.info(f"   Colecciones: {', '.join(collections)}")
                
            return cls.database
            
        except ConnectionFailure as e:
            logger.error(f"Error de conexión a MongoDB: {e}")
            raise
        except ServerSelectionTimeoutError as e:
            logger.error(f"Timeout al conectar a MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al conectar: {e}")
            raise
    
    @classmethod
    def close(cls):
        """
        Cierra la conexión a MongoDB
        """
        if cls.client:
            logger.info("Cerrando conexión a MongoDB...")
            cls.client.close()
            cls.client = None
            cls.database = None
            logger.info("Conexión cerrada")
    
    @classmethod
    def get_database(cls):
        """
        Obtiene la instancia de la base de datos.
        Si no existe conexión, la establece.
        """
        if cls.database is None:
            cls.connect()
        return cls.database
    
    @classmethod
    def get_collection(cls, collection_name: str):
        """
        Obtiene una colección específica de MongoDB
        
        Args:
            collection_name: Nombre de la colección
            
        Returns:
            Collection object de PyMongo
        """
        db = cls.get_database()
        return db[collection_name]
    
    @classmethod
    def health_check(cls) -> dict:
        """
        Verifica el estado de la conexión a MongoDB
        
        Returns:
            dict con información del estado
        """
        try:
            db = cls.get_database()
            db.command('ping')
            
            collections = db.list_collection_names()
            
            return {
                "status": "healthy",
                "database": settings.DATABASE_NAME,
                "collections_count": len(collections),
                "collections": collections
            }
        except Exception as e:
            logger.error(f"Health check falló: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Función helper para obtener la base de datos (para usar en dependencias)
def get_database():
    """
    Dependency para FastAPI que retorna la base de datos.
    Se usa en los routers como: db = Depends(get_database)
    """
    return MongoDB.get_database()

# Función helper para obtener una colección específica
def get_collection(collection_name: str):
    """
    Helper para obtener una colección específica
    """
    return MongoDB.get_collection(collection_name)