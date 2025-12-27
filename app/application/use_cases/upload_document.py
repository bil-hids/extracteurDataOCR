"""Use case pour l'upload de document."""

from pathlib import Path
from typing import Any
from uuid import UUID

from app.core.exceptions import StorageError
from app.core.logging import get_logger
from app.domain.entities.document import Document, DocumentStatus
from app.domain.value_objects.file_metadata import FileMetadata
from app.infrastructure.database.repositories.document_repo import DocumentRepository
from app.infrastructure.storage.local_storage import LocalStorage

logger = get_logger(__name__)


class UploadDocumentUseCase:
    """Use case pour uploader un document."""

    def __init__(
        self,
        storage: LocalStorage,
        document_repo: DocumentRepository,
    ) -> None:
        """Initialiser le use case."""
        self.storage = storage
        self.document_repo = document_repo

    async def execute(self, file_content: bytes, filename: str) -> Document:
        """
        Uploader un document.

        Args:
            file_content: Contenu du fichier
            filename: Nom du fichier

        Returns:
            Document créé
        """
        try:
            # Sauvegarder le fichier
            file_path = await self.storage.save_file(file_content, filename)

            # Créer les métadonnées
            file_metadata = FileMetadata(
                filename=filename,
                file_path=file_path,
                file_type=self._guess_file_type(filename),
                file_size=len(file_content),
            )

            # Créer le document
            document = Document(file_metadata=file_metadata, status=DocumentStatus.UPLOADED)

            # Sauvegarder en base
            document_model = await self._document_to_model(document)
            saved_model = await self.document_repo.create(document_model)

            # Convertir en entité
            document = await self._model_to_document(saved_model)

            logger.info(f"Document uploadé: {document.id}")
            return document

        except Exception as e:
            logger.exception(f"Erreur lors de l'upload: {e}")
            raise StorageError(f"Échec de l'upload: {str(e)}")

    def _guess_file_type(self, filename: str) -> str:
        """Deviner le type de fichier depuis l'extension."""
        import mimetypes

        file_type, _ = mimetypes.guess_type(filename)
        return file_type or "application/octet-stream"

    async def _document_to_model(self, document: Document) -> Any:
        """Convertir une entité Document en modèle."""
        from app.infrastructure.database.models.document import DocumentModel

        return DocumentModel(
            id=str(document.id),  # Convertir UUID en string pour SQLite
            filename=document.file_metadata.filename,
            file_path=str(document.file_metadata.file_path),
            file_type=document.file_metadata.file_type,
            file_size=document.file_metadata.file_size,
            status=document.status.value,
            meta_data={
                "author": document.file_metadata.author,
                "title": document.file_metadata.title,
            },
        )

    async def _model_to_document(self, model: Any) -> Document:
        """Convertir un modèle en entité Document."""
        from app.domain.value_objects.file_metadata import FileMetadata
        from uuid import UUID

        file_metadata = FileMetadata(
            filename=model.filename,
            file_path=Path(model.file_path),
            file_type=model.file_type,
            file_size=model.file_size,
        )

        # Convertir string en UUID si nécessaire
        doc_id = UUID(model.id) if isinstance(model.id, str) else model.id

        document = Document(
            id=doc_id,
            file_metadata=file_metadata,
            status=DocumentStatus(model.status),
        )

        return document

