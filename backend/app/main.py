from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

from app.config import settings
from app.database import MongoDB

# Configurar logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejador del ciclo de vida de la aplicación.
    Se ejecuta al iniciar y al cerrar el servidor.
    """
    # Startup
    logger.info("Iniciando aplicación...")
    logger.info(f"{settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Entorno: {settings.ENVIRONMENT}")
    
    try:
        # Conectar a MongoDB
        MongoDB.connect()
        logger.info("Aplicación lista")
    except Exception as e:
        logger.error(f"Error al iniciar: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Cerrando aplicación...")
    MongoDB.close()
    logger.info("Aplicación cerrada correctamente")

# Crear instancia de FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware que registra todas las peticiones HTTP
    """
    start_time = time.time()
    
    # Log de request
    logger.info(f"{request.method} {request.url.path}")
    
    # Procesar request
    response = await call_next(request)
    
    # Calcular tiempo de procesamiento
    process_time = time.time() - start_time
    
    # Log de response
    logger.info(
        f"{request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.3f}s"
    )
    
    # Agregar header con tiempo de procesamiento
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Manejador global de excepciones
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Manejador global para excepciones no capturadas
    """
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.is_development else "An unexpected error occurred",
            "path": str(request.url.path)
        }
    )

# ============================================
# ENDPOINTS BÁSICOS
# ============================================

@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raíz - Información básica de la API
    """
    return {
        "message": f"Bienvenido a {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "status": "operational"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint de health check - Verifica el estado de la API y MongoDB
    """
    mongo_health = MongoDB.health_check()
    
    return {
        "status": "healthy" if mongo_health["status"] == "healthy" else "degraded",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": mongo_health
    }

@app.get("/api/v1/health", tags=["Health"])
async def render_health_check():
    """
    Endpoint de health check para Render.
    """
    return {"status": "healthy"}

# ============================================
# IMPORTAR Y REGISTRAR ROUTERS (próximo paso)
# ============================================

# from app.routers import weapons, armors, bosses, classes, analytics
# 
from app.routers import weapons
from app.routers import bosses
from app.routers import armors
from app.routers import classes
app.include_router(
    weapons.router,
    prefix=f"{settings.API_V1_PREFIX}/weapons",
    tags=["Weapons"]
)

app.include_router(
    bosses.router,
    prefix=f"{settings.API_V1_PREFIX}/bosses",
    tags=["Bosses"]
)

app.include_router(
    armors.router,
    prefix=f"{settings.API_V1_PREFIX}/armors",
    tags=["Armors"]
)

app.include_router(
    classes.router,
    prefix=f"{settings.API_V1_PREFIX}/classes",
    tags=["Classes"]
)
# 
# app.include_router(
#     armors.router,
#     prefix=f"{settings.API_V1_PREFIX}/armors",
#     tags=["Armors"]
# )
# 
# ... más routers

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f" Iniciando servidor en {settings.HOST}:{settings.PORT}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )