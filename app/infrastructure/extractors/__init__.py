"""Extracteurs de contenu par type de fichier."""

from app.infrastructure.extractors.factory import ExtractorFactory
from app.infrastructure.extractors.pdf.pdf_extractor import PdfExtractor
from app.infrastructure.extractors.office.excel_extractor import ExcelExtractor
from app.infrastructure.extractors.office.word_extractor import WordExtractor
from app.infrastructure.extractors.image.ocr_extractor import OcrExtractor
from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def create_extractor_factory() -> ExtractorFactory:
    """Créer et configurer la factory d'extracteurs."""
    factory = ExtractorFactory()

    # Enregistrer les extracteurs
    factory.register(PdfExtractor())
    factory.register(ExcelExtractor())
    factory.register(WordExtractor())
    factory.register(OcrExtractor(tesseract_cmd=settings.tesseract_cmd))

    logger.info("Factory d'extracteurs initialisée")
    return factory
