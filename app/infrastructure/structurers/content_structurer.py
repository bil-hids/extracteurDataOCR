"""Structurateur de contenu."""

from uuid import UUID, uuid4
from typing import Any

from app.core.logging import get_logger
from app.domain.entities.content_block import ContentBlock, ContentType
from app.domain.value_objects.extraction_result import ExtractionResult
from app.infrastructure.structurers.base import BaseStructurer


class ContentStructurer(BaseStructurer):
    """Structurateur de contenu pour organiser les blocs par type."""

    def __init__(self, logger: Any = None) -> None:
        """Initialiser le structurateur."""
        super().__init__(logger or get_logger(__name__))

    async def structure(
        self, extraction_result: ExtractionResult, document_id: UUID | str
    ) -> list[ContentBlock]:
        """
        Structurer le contenu en blocs organisés.

        Args:
            extraction_result: Résultat d'extraction
            document_id: ID du document

        Returns:
            Liste de blocs de contenu structurés
        """
        content_blocks: list[ContentBlock] = []

        # Structurer les blocs de texte
        text_blocks = await self._structure_text_blocks(
            extraction_result.text_blocks, document_id
        )
        content_blocks.extend(text_blocks)

        # Structurer les tableaux
        table_blocks = await self._structure_table_blocks(
            extraction_result.tables, document_id
        )
        content_blocks.extend(table_blocks)

        # Structurer les images
        image_blocks = await self._structure_image_blocks(
            extraction_result.images, document_id
        )
        content_blocks.extend(image_blocks)

        # Établir les relations entre blocs
        content_blocks = self._establish_relations(content_blocks)

        self.logger.info(f"Structuration terminée: {len(content_blocks)} blocs créés")
        return content_blocks

    async def _structure_text_blocks(
        self, text_blocks: list, document_id: UUID | str
    ) -> list[ContentBlock]:
        """Structurer les blocs de texte."""
        content_blocks: list[ContentBlock] = []

        for text_block in text_blocks:
            # Déterminer le type de contenu
            content_type = ContentType.TEXT
            if text_block.metadata.section_level:
                if text_block.metadata.section_level <= 3:
                    content_type = ContentType.HEADING

            # Extraire les entités
            entities = text_block.metadata.additional_metadata.get("entities", [])

            # Convertir document_id en UUID si c'est une string
            doc_id_uuid = UUID(document_id) if isinstance(document_id, str) else document_id

            content_block = ContentBlock(
                id=uuid4(),
                document_id=doc_id_uuid,
                content_type=content_type,
                content={"text": text_block.content},
                metadata=text_block.metadata,
                entities=entities,
                relevance_score=text_block.metadata.confidence,
            )

            content_blocks.append(content_block)

        return content_blocks

    async def _structure_table_blocks(
        self, table_blocks: list, document_id: UUID | str
    ) -> list[ContentBlock]:
        """Structurer les blocs de tableaux."""
        content_blocks: list[ContentBlock] = []

        for table_block in table_blocks:
            # Convertir document_id en UUID si c'est une string
            doc_id_uuid = UUID(document_id) if isinstance(document_id, str) else document_id
            
            content_block = ContentBlock(
                id=uuid4(),
                document_id=doc_id_uuid,
                content_type=ContentType.TABLE,
                content={
                    "headers": table_block.headers,
                    "rows": table_block.rows,
                    "row_count": len(table_block.rows),
                    "column_count": len(table_block.headers),
                },
                metadata=table_block.metadata,
            )

            content_blocks.append(content_block)

        return content_blocks

    async def _structure_image_blocks(
        self, image_blocks: list, document_id: UUID | str
    ) -> list[ContentBlock]:
        """Structurer les blocs d'images."""
        content_blocks: list[ContentBlock] = []

        for image_block in image_blocks:
            # Convertir document_id en UUID si c'est une string
            doc_id_uuid = UUID(document_id) if isinstance(document_id, str) else document_id
            content_block = ContentBlock(
                id=uuid4(),
                document_id=doc_id_uuid,
                content_type=ContentType.IMAGE,
                content={
                    "image_path": image_block.image_path,
                    "ocr_text": image_block.ocr_text,
                    "metadata": image_block.metadata.additional_metadata,
                },
                metadata=image_block.metadata,
            )

            content_blocks.append(content_block)

        return content_blocks

    def _establish_relations(
        self, content_blocks: list[ContentBlock]
    ) -> list[ContentBlock]:
        """Établir les relations entre blocs (précédent/suivant, parent)."""
        # Trier par ordre
        sorted_blocks = sorted(
            content_blocks, key=lambda b: (b.metadata.order, b.metadata.page_number or 0)
        )

        # Établir les relations précédent/suivant
        for i, block in enumerate(sorted_blocks):
            if i > 0:
                block.previous_block_id = sorted_blocks[i - 1].id
            if i < len(sorted_blocks) - 1:
                block.next_block_id = sorted_blocks[i + 1].id

            # Établir les relations parent (basées sur les sections)
            if block.metadata.section_id:
                # Trouver le bloc parent (section)
                for parent_block in sorted_blocks:
                    if (
                        parent_block.content_type == ContentType.HEADING
                        and parent_block.metadata.section_title == block.metadata.section_title
                    ):
                        block.parent_block_id = parent_block.id
                        break

        return sorted_blocks

