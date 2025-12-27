"""Endpoints pour les documents."""

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.document import (
    DocumentResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from app.api.schemas.content import (
    DocumentDataResponse,
    ContentBlockResponse,
    ContentResponse,
    StructuredDataResponse,
)
from app.core.logging import get_logger
from app.domain.entities.document import DocumentStatus
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.repositories.document_repo import DocumentRepository
from app.infrastructure.database.repositories.content_repo import ContentRepository
from app.infrastructure.database.repositories.structured_data_repo import StructuredDataRepository
from app.infrastructure.storage.local_storage import LocalStorage
from app.application.use_cases.upload_document import UploadDocumentUseCase
from app.application.pipelines.extraction_pipeline import ExtractionPipeline
from app.infrastructure.extractors import create_extractor_factory
from app.infrastructure.processors.text_enricher import TextEnricher
from app.infrastructure.processors.table_normalizer import TableNormalizer
from app.infrastructure.processors.image_processor import ImageProcessor
from app.infrastructure.services.ocr_service import OcrService
from app.infrastructure.structurers.content_structurer import ContentStructurer
from app.infrastructure.structurers.document_structurer import DocumentStructurer
from app.infrastructure.formatters.markdown_formatter import MarkdownFormatter
from app.config import get_settings
from fastapi.responses import FileResponse
from pathlib import Path
import tempfile
from fastapi.responses import FileResponse
from pathlib import Path
import tempfile

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


@router.post("/", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """Uploader un document."""
    try:
        # Lire le fichier
        file_content = await file.read()

        # Vérifier la taille
        if len(file_content) > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Fichier trop volumineux (max: {settings.max_file_size} bytes)",
            )

        # Uploader
        storage = LocalStorage()
        document_repo = DocumentRepository(db)
        use_case = UploadDocumentUseCase(storage, document_repo)

        document = await use_case.execute(file_content, file.filename or "unknown")

        return DocumentUploadResponse(
            document_id=document.id,
            filename=document.file_metadata.filename,
            status=document.status.value,
            message="Document uploadé avec succès",
        )

    except Exception as e:
        logger.exception(f"Erreur lors de l'upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'upload: {str(e)}",
        )


@router.get("/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentStatusResponse:
    """Obtenir le statut d'un document."""
    document_repo = DocumentRepository(db)
    document = await document_repo.get_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document non trouvé",
        )

    # Convertir l'ID en UUID si c'est une string
    from uuid import UUID
    doc_id = UUID(document.id) if isinstance(document.id, str) else document.id
    
    return DocumentStatusResponse(
        id=doc_id,
        status=document.status,
        error_message=document.error_message,
        processing_started_at=document.processing_started_at,
        processing_completed_at=document.processing_completed_at,
    )


@router.post("/{document_id}/extract", status_code=status.HTTP_202_ACCEPTED)
async def extract_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Extraire et traiter un document."""
    document_repo = DocumentRepository(db)
    document_model = await document_repo.get_by_id(document_id)

    if not document_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document non trouvé",
        )

    # Créer le pipeline
    factory = create_extractor_factory()
    extractor = factory.create(document_model.file_path)

    text_enricher = TextEnricher(settings.spacy_model)
    table_normalizer = TableNormalizer()
    # Créer le service OCR et l'injecter dans ImageProcessor
    ocr_service = OcrService(tesseract_cmd=settings.tesseract_cmd)
    image_processor = ImageProcessor(ocr_service=ocr_service)
    content_structurer = ContentStructurer()
    document_structurer = DocumentStructurer()

    pipeline = ExtractionPipeline(
        extractor=extractor,
        text_enricher=text_enricher,
        table_normalizer=table_normalizer,
        image_processor=image_processor,
        content_structurer=content_structurer,
        document_structurer=document_structurer,
    )

    # Convertir le modèle en entité (simplifié)
    from app.domain.entities.document import Document
    from app.domain.value_objects.file_metadata import FileMetadata
    from pathlib import Path

    from uuid import UUID
    
    file_metadata = FileMetadata(
        filename=document_model.filename,
        file_path=Path(document_model.file_path),
        file_type=document_model.file_type,
        file_size=document_model.file_size,
    )

    # Convertir string en UUID si nécessaire
    doc_id = UUID(document_model.id) if isinstance(document_model.id, str) else document_model.id
    
    document = Document(
        id=doc_id,
        file_metadata=file_metadata,
        status=DocumentStatus(document_model.status),
    )

    # Vérifier que le document n'est pas déjà en cours de traitement
    if document_model.status == DocumentStatus.EXTRACTING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Le document est déjà en cours de traitement",
        )
    
    # Mettre à jour le statut du document
    document_model.status = DocumentStatus.EXTRACTING.value
    document_model.processing_started_at = datetime.utcnow()
    document_model.error_message = None
    await document_repo.update(document_model)
    
    # Traiter le document
    try:
        structured_data = await pipeline.process(document_model.file_path, document)
        
        # Sauvegarder les blocs de contenu et les données structurées
        content_repo = ContentRepository(db)
        structured_data_repo = StructuredDataRepository(db)
        
        doc_id_str = str(document_id)
        
        try:
            # Supprimer les anciens blocs de contenu s'ils existent
            existing_blocks = await content_repo.get_by_document_id(document_id)
            for block in existing_blocks:
                await content_repo.delete(block.id)
            
            # Récupérer les content_blocks depuis structured_data.data
            content_blocks_data = structured_data.data.get("content_blocks", [])
            
            # Sauvegarder chaque bloc de contenu
            for block_data in content_blocks_data:
                from app.infrastructure.database.models.content_block import ContentBlockModel
                
                # Extraire les IDs des relations
                block_id = block_data.get("id")
                if isinstance(block_id, UUID):
                    block_id = str(block_id)
                elif not block_id:
                    block_id = str(uuid4())
                
                parent_id = block_data.get("parent_id") or block_data.get("metadata", {}).get("parent_block_id")
                previous_id = block_data.get("previous_id") or block_data.get("metadata", {}).get("previous_block_id")
                next_id = block_data.get("next_id") or block_data.get("metadata", {}).get("next_block_id")
                
                block_model = ContentBlockModel(
                    id=block_id,
                    document_id=doc_id_str,
                    content_type=block_data.get("type", "text"),
                    content=block_data.get("content", {}),
                    meta_data=block_data.get("metadata", {}),
                    entities=block_data.get("entities", []),
                    relevance_score=block_data.get("relevance_score"),
                    parent_block_id=str(parent_id) if parent_id else None,
                    previous_block_id=str(previous_id) if previous_id else None,
                    next_block_id=str(next_id) if next_id else None,
                )
                await content_repo.create(block_model)
            
            # Vérifier si des données structurées existent déjà
            existing_structured_data = await structured_data_repo.get_by_document_id(document_id)
            
            if existing_structured_data:
                # Mettre à jour les données existantes
                existing_structured_data.data = structured_data.data
                existing_structured_data.schema_version = structured_data.schema_version
                existing_structured_data.updated_at = datetime.utcnow()
                await structured_data_repo.update(existing_structured_data)
            else:
                # Créer de nouvelles données structurées
                from app.infrastructure.database.models.structured_data import StructuredDataModel
                
                structured_data_model = StructuredDataModel(
                    id=str(uuid4()),
                    document_id=doc_id_str,
                    data=structured_data.data,
                    schema_version=structured_data.schema_version,
                )
                await structured_data_repo.create(structured_data_model)
            
            # Mettre à jour le statut du document
            document_model.status = DocumentStatus.COMPLETED.value
            document_model.processing_completed_at = datetime.utcnow()
            document_model.error_message = None
            await document_repo.update(document_model)
            
            logger.info(
                f"Extraction terminée avec succès pour le document {document_id}",
                extra={
                    "document_id": str(document_id),
                    "blocks_count": len(content_blocks_data),
                },
            )
            
            return {
                "message": "Extraction terminée",
                "document_id": str(document_id),
                "blocks_count": len(content_blocks_data),
            }
        except Exception as db_error:
            # Rollback en cas d'erreur de base de données
            await db.rollback()
            logger.exception(f"Erreur lors de la sauvegarde: {db_error}")
            raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erreur lors de l'extraction: {e}")
        # Rollback en cas d'erreur
        try:
            await db.rollback()
        except Exception:
            pass
        # Mettre à jour le statut en erreur
        try:
            document_model.status = DocumentStatus.FAILED.value
            document_model.error_message = str(e)
            await document_repo.update(document_model)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'extraction: {str(e)}",
        )


@router.get("/{document_id}/data", response_model=DocumentDataResponse)
async def get_document_data(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    content_type: str | None = None,
    page_number: int | None = None,
) -> DocumentDataResponse:
    """
    Récupérer toutes les données traitées d'un document.
    
    Args:
        document_id: UUID du document
        content_type: Filtrer par type de contenu (text, table, image, heading)
        page_number: Filtrer par numéro de page
    
    Returns:
        DocumentDataResponse avec toutes les données structurées du document
    """
    # Vérifier que le document existe
    document_repo = DocumentRepository(db)
    document_model = await document_repo.get_by_id(document_id)

    if not document_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document non trouvé",
        )

    # Récupérer les données structurées
    structured_data_repo = StructuredDataRepository(db)
    structured_data_model = await structured_data_repo.get_by_document_id(document_id)

    # Récupérer les blocs de contenu avec filtres optionnels
    content_repo = ContentRepository(db)
    
    if content_type:
        # Filtrer par type de contenu
        from app.domain.entities.content_block import ContentType
        try:
            content_type_enum = ContentType(content_type)
            content_blocks_models = await content_repo.get_by_type(document_id, content_type_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Type de contenu invalide: {content_type}. Types valides: text, table, image, heading",
            )
    elif page_number is not None:
        # Filtrer par numéro de page
        content_blocks_models = await content_repo.get_by_page(document_id, page_number)
    else:
        # Récupérer tous les blocs
        content_blocks_models = await content_repo.get_by_document_id(document_id)

    # Convertir les blocs de contenu en schémas de réponse
    text_blocks = []
    table_blocks = []
    image_blocks = []

    for block_model in content_blocks_models:
        block_id = UUID(block_model.id) if isinstance(block_model.id, str) else block_model.id
        
        # Assurez-vous que meta_data est un dictionnaire
        meta_data_dict = block_model.meta_data if isinstance(block_model.meta_data, dict) else {}
        
        # Convertir les IDs de relations en UUID si nécessaire
        parent_id = UUID(block_model.parent_block_id) if block_model.parent_block_id and isinstance(block_model.parent_block_id, str) else (block_model.parent_block_id if block_model.parent_block_id else None)
        previous_id = UUID(block_model.previous_block_id) if block_model.previous_block_id and isinstance(block_model.previous_block_id, str) else (block_model.previous_block_id if block_model.previous_block_id else None)
        next_id = UUID(block_model.next_block_id) if block_model.next_block_id and isinstance(block_model.next_block_id, str) else (block_model.next_block_id if block_model.next_block_id else None)
        
        block_response = ContentBlockResponse(
            id=block_id,
            content_type=block_model.content_type,
            content=block_model.content,
            metadata=meta_data_dict,
            entities=block_model.entities or [],
            relevance_score=block_model.relevance_score,
            parent_block_id=parent_id,
            previous_block_id=previous_id,
            next_block_id=next_id,
        )

        if block_model.content_type == "text" or block_model.content_type == "heading":
            text_blocks.append(block_response)
        elif block_model.content_type == "table":
            table_blocks.append(block_response)
        elif block_model.content_type == "image":
            image_blocks.append(block_response)

    content_response = ContentResponse(
        document_id=UUID(document_model.id) if isinstance(document_model.id, str) else document_model.id,
        text_blocks=text_blocks,
        tables=table_blocks,
        images=image_blocks,
    )

    # Préparer les informations du document
    doc_id = UUID(document_model.id) if isinstance(document_model.id, str) else document_model.id
    document_info = {
        "id": str(doc_id),
        "filename": document_model.filename,
        "file_type": document_model.file_type,
        "file_size": document_model.file_size,
        "status": document_model.status,
        "created_at": document_model.created_at.isoformat() if document_model.created_at else None,
        "updated_at": document_model.updated_at.isoformat() if document_model.updated_at else None,
        "processing_started_at": document_model.processing_started_at.isoformat() if document_model.processing_started_at else None,
        "processing_completed_at": document_model.processing_completed_at.isoformat() if document_model.processing_completed_at else None,
    }

    # Préparer les données structurées
    structured_data_response = None
    statistics = None
    if structured_data_model:
        # Extraire les statistiques si elles existent
        if structured_data_model.data and "statistics" in structured_data_model.data:
            statistics = structured_data_model.data.get("statistics")
        
        # Créer le schéma StructuredDataResponse
        structured_data_doc_id = UUID(structured_data_model.document_id) if isinstance(structured_data_model.document_id, str) else structured_data_model.document_id
        structured_data_response = StructuredDataResponse(
            document_id=structured_data_doc_id,
            data=structured_data_model.data,
            schema_version=structured_data_model.schema_version,
        )

    return DocumentDataResponse(
        document_id=doc_id,
        document_info=document_info,
        structured_data=structured_data_response,
        content_blocks=content_response,
        statistics=statistics,
    )


@router.get("/{document_id}/markdown")
async def get_document_markdown(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """
    Récupérer les données d'un document et les convertir en fichier Markdown.
    
    Args:
        document_id: UUID du document
    
    Returns:
        Fichier Markdown téléchargeable
    """
    # Vérifier que le document existe
    document_repo = DocumentRepository(db)
    document_model = await document_repo.get_by_id(document_id)

    if not document_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document non trouvé",
        )

    # Vérifier que le document a été traité
    if document_model.status != DocumentStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le document n'a pas encore été traité. Veuillez d'abord lancer l'extraction.",
        )

    # Récupérer les données structurées
    structured_data_repo = StructuredDataRepository(db)
    structured_data_model = await structured_data_repo.get_by_document_id(document_id)

    # Récupérer les blocs de contenu
    content_repo = ContentRepository(db)
    content_blocks_models = await content_repo.get_by_document_id(document_id)

    # Convertir les blocs de contenu en schémas de réponse
    text_blocks = []
    table_blocks = []
    image_blocks = []

    for block_model in content_blocks_models:
        block_id = UUID(block_model.id) if isinstance(block_model.id, str) else block_model.id
        
        # Assurez-vous que meta_data est un dictionnaire
        meta_data_dict = block_model.meta_data if isinstance(block_model.meta_data, dict) else {}
        
        # Convertir les IDs de relations en UUID si nécessaire
        parent_id = UUID(block_model.parent_block_id) if block_model.parent_block_id and isinstance(block_model.parent_block_id, str) else (block_model.parent_block_id if block_model.parent_block_id else None)
        previous_id = UUID(block_model.previous_block_id) if block_model.previous_block_id and isinstance(block_model.previous_block_id, str) else (block_model.previous_block_id if block_model.previous_block_id else None)
        next_id = UUID(block_model.next_block_id) if block_model.next_block_id and isinstance(block_model.next_block_id, str) else (block_model.next_block_id if block_model.next_block_id else None)
        
        block_response = ContentBlockResponse(
            id=block_id,
            content_type=block_model.content_type,
            content=block_model.content,
            metadata=meta_data_dict,
            entities=block_model.entities or [],
            relevance_score=block_model.relevance_score,
            parent_block_id=parent_id,
            previous_block_id=previous_id,
            next_block_id=next_id,
        )

        if block_model.content_type == "text" or block_model.content_type == "heading":
            text_blocks.append(block_response)
        elif block_model.content_type == "table":
            table_blocks.append(block_response)
        elif block_model.content_type == "image":
            image_blocks.append(block_response)

    content_response = ContentResponse(
        document_id=UUID(document_model.id) if isinstance(document_model.id, str) else document_model.id,
        text_blocks=text_blocks,
        tables=table_blocks,
        images=image_blocks,
    )

    # Préparer les informations du document
    doc_id = UUID(document_model.id) if isinstance(document_model.id, str) else document_model.id
    document_info = {
        "id": str(doc_id),
        "filename": document_model.filename,
        "file_type": document_model.file_type,
        "file_size": document_model.file_size,
        "status": document_model.status,
        "created_at": document_model.created_at.isoformat() if document_model.created_at else None,
        "updated_at": document_model.updated_at.isoformat() if document_model.updated_at else None,
        "processing_started_at": document_model.processing_started_at.isoformat() if document_model.processing_started_at else None,
        "processing_completed_at": document_model.processing_completed_at.isoformat() if document_model.processing_completed_at else None,
    }

    # Préparer les données structurées
    structured_data_dict = None
    if structured_data_model:
        structured_data_dict = structured_data_model.data

    # Convertir en Markdown
    formatter = MarkdownFormatter()
    
    # Convertir les ContentBlockResponse en dict pour le formateur
    content_blocks_dict = {
        "text_blocks": [block.model_dump() for block in text_blocks],
        "tables": [block.model_dump() for block in table_blocks],
        "images": [block.model_dump() for block in image_blocks],
    }
    
    markdown_content = formatter.format_document(
        document_info=document_info,
        content_blocks=content_blocks_dict,
        structured_data=structured_data_dict,
    )

    # Créer un fichier temporaire
    temp_dir = Path(tempfile.gettempdir())
    filename_base = Path(document_model.filename).stem if document_model.filename else str(doc_id)
    markdown_filename = f"{filename_base}.md"
    markdown_path = temp_dir / markdown_filename

    # Écrire le contenu Markdown dans le fichier
    try:
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        logger.info(f"Fichier Markdown créé: {markdown_path}")

        # Retourner le fichier
        return FileResponse(
            path=str(markdown_path),
            filename=markdown_filename,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{markdown_filename}"'},
        )
    except Exception as e:
        logger.exception(f"Erreur lors de la création du fichier Markdown: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du fichier Markdown: {str(e)}",
        )

