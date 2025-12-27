"""Pipeline d'extraction et de traitement complet."""

from typing import Any, Callable
from uuid import UUID

from app.core.exceptions import ExtractionError, ProcessingError
from app.core.logging import get_logger
from app.domain.entities.document import Document
from app.domain.entities.structured_data import StructuredData
from app.domain.value_objects.extraction_result import ExtractionResult
from app.infrastructure.extractors.base import BaseExtractor
from app.infrastructure.processors.image_processor import ImageProcessor
from app.infrastructure.processors.table_normalizer import TableNormalizer
from app.infrastructure.processors.text_enricher import TextEnricher
from app.infrastructure.structurers.content_structurer import ContentStructurer
from app.infrastructure.structurers.document_structurer import DocumentStructurer

logger = get_logger(__name__)


class ExtractionPipeline:
    """Pipeline complet d'extraction et de traitement."""

    def __init__(
        self,
        extractor: BaseExtractor,
        text_enricher: TextEnricher,
        table_normalizer: TableNormalizer,
        image_processor: ImageProcessor,
        content_structurer: ContentStructurer,
        document_structurer: DocumentStructurer,
        logger: Any = None,
    ) -> None:
        """Initialiser le pipeline."""
        self.extractor = extractor
        self.text_enricher = text_enricher
        self.table_normalizer = table_normalizer
        self.image_processor = image_processor
        self.content_structurer = content_structurer
        self.document_structurer = document_structurer
        self.logger = logger or get_logger(__name__)

    async def process(
        self,
        file_path: str,
        document: Document,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> StructuredData:
        """
        Traiter un document complet.

        Args:
            file_path: Chemin vers le fichier
            document: Document à traiter
            progress_callback: Callback pour suivre la progression

        Returns:
            Données structurées du document
        """
        try:
            # 1. Extraction
            self._update_progress(progress_callback, "Extraction en cours...", 0.1)
            extraction_result = await self.extractor.extract(file_path)
            self.logger.info(f"Extraction terminée: {extraction_result.has_content()}")

            if not extraction_result.has_content():
                raise ExtractionError("Aucun contenu extrait du fichier")

            # 2. Traitement des images avec OCR (avant enrichissement)
            self._update_progress(
                progress_callback, "Traitement des images avec OCR...", 0.25
            )

            # Traiter les images (avec OCR si disponible)
            processed_images, ocr_text_blocks = await self.image_processor.process_batch(
                extraction_result.images
            )

            # Ajouter les TextBlocks créés depuis l'OCR aux text_blocks existants
            # pour qu'ils soient enrichis par TextEnricher
            if ocr_text_blocks:
                self.logger.info(
                    f"Texte OCR extrait de {len(ocr_text_blocks)} image(s), "
                    f"ajout aux text_blocks pour enrichissement"
                )
                extraction_result.text_blocks.extend(ocr_text_blocks)

            # Mettre à jour les images traitées
            extraction_result.images = processed_images

            # 3. Enrichissement parallèle
            self._update_progress(progress_callback, "Enrichissement en cours...", 0.4)

            # Enrichir les textes (incluant maintenant le texte OCR)
            enriched_texts = await self.text_enricher.enrich_batch(
                extraction_result.text_blocks
            )

            # Normaliser les tableaux
            normalized_tables = await self.table_normalizer.normalize_batch(
                extraction_result.tables
            )

            # Mettre à jour les résultats
            extraction_result.text_blocks = enriched_texts
            extraction_result.tables = normalized_tables

            self.logger.info(
                f"Enrichissement terminé: {len(enriched_texts)} textes, "
                f"{len(normalized_tables)} tableaux, {len(processed_images)} images"
            )

            # 4. Structuration
            self._update_progress(progress_callback, "Structuration en cours...", 0.7)

            # Structurer le contenu en blocs
            # Convertir UUID en string pour compatibilité SQLite
            doc_id = str(document.id) if hasattr(document.id, '__str__') else document.id
            content_blocks = await self.content_structurer.structure(
                extraction_result, doc_id
            )

            # Structurer le document complet
            metadata = {
                "filename": document.file_metadata.filename,
                "file_type": document.file_metadata.file_type,
                "file_size": document.file_metadata.file_size,
            }

            structured_data = await self.document_structurer.structure(
                content_blocks, doc_id, metadata
            )

            self._update_progress(progress_callback, "Traitement terminé", 1.0)

            return structured_data

        except ExtractionError:
            raise
        except Exception as e:
            self.logger.exception(f"Erreur dans le pipeline: {e}")
            raise ProcessingError(f"Échec du traitement: {str(e)}")

    def _update_progress(
        self,
        callback: Callable[[str, float], None] | None,
        message: str,
        progress: float,
    ) -> None:
        """Mettre à jour la progression."""
        if callback:
            try:
                callback(message, progress)
            except Exception as e:
                self.logger.warning(f"Erreur dans le callback de progression: {e}")

