"""Tâches de traitement asynchrone."""

import asyncio
from typing import Any, Callable
from uuid import UUID

from app.core.logging import get_logger
from app.domain.entities.document import Document
from app.infrastructure.database.repositories.document_repo import DocumentRepository
from app.infrastructure.database.repositories.content_repo import ContentRepository
from app.application.pipelines.extraction_pipeline import ExtractionPipeline

logger = get_logger(__name__)


class AsyncProcessingQueue:
    """Queue asynchrone pour le traitement de documents."""

    def __init__(self, max_concurrent: int = 4) -> None:
        """Initialiser la queue."""
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.tasks: dict[UUID, asyncio.Task] = {}

    async def process_document(
        self,
        document_id: UUID,
        file_path: str,
        document: Document,
        pipeline: ExtractionPipeline,
        document_repo: DocumentRepository,
        content_repo: ContentRepository,
        progress_callback: Callable[[UUID, str, float], None] | None = None,
    ) -> None:
        """
        Traiter un document de manière asynchrone.

        Args:
            document_id: ID du document
            file_path: Chemin vers le fichier
            document: Document à traiter
            pipeline: Pipeline de traitement
            document_repo: Repository pour documents
            content_repo: Repository pour contenu
            progress_callback: Callback pour suivre la progression
        """
        async with self.semaphore:
            try:
                # Mettre à jour le statut
                document_model = await document_repo.get_by_id(document_id)
                if document_model:
                    document_model.status = "extracting"
                    await document_repo.update(document_model)

                # Callback de progression interne
                def internal_callback(message: str, progress: float) -> None:
                    if progress_callback:
                        progress_callback(document_id, message, progress)

                # Traiter le document
                structured_data = await pipeline.process(
                    file_path, document, internal_callback
                )

                # Sauvegarder les résultats (simplifié)
                # TODO: Sauvegarder les content blocks et structured data

                # Mettre à jour le statut
                if document_model:
                    document_model.status = "completed"
                    await document_repo.update(document_model)

                logger.info(f"Traitement terminé pour document {document_id}")

            except Exception as e:
                logger.exception(f"Erreur lors du traitement du document {document_id}: {e}")
                # Mettre à jour le statut en erreur
                document_model = await document_repo.get_by_id(document_id)
                if document_model:
                    document_model.status = "failed"
                    document_model.error_message = str(e)
                    await document_repo.update(document_model)

    def add_task(
        self,
        document_id: UUID,
        file_path: str,
        document: Document,
        pipeline: ExtractionPipeline,
        document_repo: DocumentRepository,
        content_repo: ContentRepository,
        progress_callback: Callable[[UUID, str, float], None] | None = None,
    ) -> asyncio.Task:
        """Ajouter une tâche de traitement à la queue."""
        task = asyncio.create_task(
            self.process_document(
                document_id,
                file_path,
                document,
                pipeline,
                document_repo,
                content_repo,
                progress_callback,
            )
        )
        self.tasks[document_id] = task
        return task

    async def wait_for_task(self, document_id: UUID) -> None:
        """Attendre qu'une tâche soit terminée."""
        if document_id in self.tasks:
            await self.tasks[document_id]
            del self.tasks[document_id]


# Instance globale de la queue
processing_queue = AsyncProcessingQueue(max_concurrent=4)

