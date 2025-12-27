"""Configuration de la connexion à la base de données."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import get_settings

settings = get_settings()

# Créer le moteur async
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base pour les modèles
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Obtenir une session de base de données."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialiser la base de données (créer les tables)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Fermer les connexions à la base de données."""
    await engine.dispose()

