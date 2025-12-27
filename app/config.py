"""Configuration centralisée avec Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration de l'application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Extracteur de Données"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Base de données
    database_url: str = Field(
        default="sqlite+aiosqlite:///./extracteur.db",
        description="URL de connexion à la base de données",
    )
    database_echo: bool = False

    # Stockage fichiers
    upload_dir: Path = Field(default=Path("./uploads"), description="Répertoire d'upload")
    max_file_size: int = Field(
        default=100 * 1024 * 1024,  # 100 MB
        description="Taille maximale de fichier en bytes",
    )

    # SpaCy
    spacy_model: str = Field(
        default="fr_core_news_md",
        description="Modèle SpaCy à utiliser (version 3.8.0 installée)",
    )

    # Tesseract
    tesseract_cmd: Optional[str] = Field(
        default=None,
        description="Chemin vers l'exécutable Tesseract (auto-détecté si None)",
    )

    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
        default=["*"],
        description="Origines CORS autorisées",
    )

    # Workers
    enable_async_workers: bool = True
    worker_concurrency: int = 4

    def __init__(self, **kwargs) -> None:
        """Initialiser les settings."""
        super().__init__(**kwargs)
        # Créer le répertoire d'upload s'il n'existe pas
        self.upload_dir.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Obtenir les settings (cached)."""
    return Settings()

