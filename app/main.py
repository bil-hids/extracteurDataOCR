"""Application FastAPI principale."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.error_handler import error_handler
from app.api.middleware.request_logging import RequestLoggingMiddleware
from app.api.v1.router import api_router
from app.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.database.connection import close_db, init_db

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gérer le cycle de vie de l'application."""
    # Startup
    logger.info("Démarrage de l'application...")
    
    # Vérifier et installer les dépendances
    from app.core.dependencies_checker import check_dependencies_on_startup
    dependencies_ok = await check_dependencies_on_startup()
    if not dependencies_ok:
        logger.warning("Certaines dépendances sont manquantes, mais l'application continue...")
    
    await init_db()
    logger.info("Base de données initialisée")

    yield

    # Shutdown
    logger.info("Arrêt de l'application...")
    await close_db()
    logger.info("Application arrêtée")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Système d'extraction et prétraitement de données multi-formats",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware custom
app.add_middleware(RequestLoggingMiddleware)
app.middleware("http")(error_handler)

# Routes
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
async def root() -> dict:
    """Endpoint racine."""
    return {
        "message": "Système d'extraction et prétraitement de données",
        "version": settings.app_version,
    }


@app.get("/health")
async def health() -> dict:
    """Endpoint de santé."""
    return {"status": "healthy"}

