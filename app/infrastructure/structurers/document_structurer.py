"""Structurateur de document complet."""

from uuid import UUID
from typing import Any

from app.core.logging import get_logger
from app.domain.entities.content_block import ContentBlock
from app.domain.entities.structured_data import StructuredData
from app.infrastructure.structurers.base import BaseStructurer


class DocumentStructurer(BaseStructurer):
    """Structurateur pour organiser un document complet."""

    def __init__(self, logger: Any = None) -> None:
        """Initialiser le structurateur."""
        super().__init__(logger or get_logger(__name__))

    async def structure(
        self, content_blocks: list[ContentBlock], document_id: UUID | str, metadata: dict[str, Any]
    ) -> StructuredData:
        """
        Structurer un document complet.

        Args:
            content_blocks: Blocs de contenu structurés
            document_id: ID du document
            metadata: Métadonnées du document

        Returns:
            Données structurées du document
        """
        # Organiser hiérarchiquement
        structure = self._organize_hierarchically(content_blocks)

        # Créer l'index pour recherche rapide
        index = self._create_index(content_blocks)

        # Convertir document_id en string si nécessaire
        doc_id_str = str(document_id) if isinstance(document_id, UUID) else document_id
        
        # Construire le document structuré
        structured_data = {
            "document_id": doc_id_str,
            "metadata": metadata,
            "structure": structure,
            "content_blocks": [self._block_to_dict(block) for block in content_blocks],
            "index": index,
            "statistics": self._calculate_statistics(content_blocks),
        }

        # Créer l'entité StructuredData (convertir string en UUID si nécessaire)
        doc_id_uuid = UUID(doc_id_str) if isinstance(doc_id_str, str) else doc_id_str
        structured = StructuredData(
            document_id=doc_id_uuid,
            data=structured_data,
        )

        self.logger.info(f"Document structuré: {len(content_blocks)} blocs organisés")
        return structured

    def _organize_hierarchically(
        self, content_blocks: list[ContentBlock]
    ) -> dict[str, Any]:
        """Organiser les blocs de manière hiérarchique."""
        structure = {"sections": []}

        current_section: dict[str, Any] | None = None
        current_level = 0

        for block in content_blocks:
            # Nouvelle section si c'est un titre
            if block.content_type.value == "heading":
                # Fermer la section précédente si elle existe
                if current_section:
                    structure["sections"].append(current_section)

                # Créer une nouvelle section
                current_section = {
                    "id": str(block.id),
                    "level": block.metadata.section_level or 1,
                    "title": block.metadata.section_title or "",
                    "content_blocks": [],
                }
                current_level = block.metadata.section_level or 1

            # Ajouter le bloc à la section courante
            if current_section:
                current_section["content_blocks"].append(str(block.id))
            else:
                # Bloc sans section parente
                if "orphan_blocks" not in structure:
                    structure["orphan_blocks"] = []
                structure["orphan_blocks"].append(str(block.id))

        # Ajouter la dernière section
        if current_section:
            structure["sections"].append(current_section)

        return structure

    def _create_index(self, content_blocks: list[ContentBlock]) -> dict[str, Any]:
        """Créer un index pour recherche rapide."""
        index = {
            "by_type": {},
            "by_page": {},
            "by_entity": {},
        }

        for block in content_blocks:
            # Index par type
            block_type = block.content_type.value
            if block_type not in index["by_type"]:
                index["by_type"][block_type] = []
            index["by_type"][block_type].append(str(block.id))

            # Index par page
            page = block.metadata.page_number
            if page:
                if page not in index["by_page"]:
                    index["by_page"][page] = []
                index["by_page"][page].append(str(block.id))

            # Index par entité
            for entity in block.entities:
                entity_label = entity.get("label", "")
                if entity_label:
                    if entity_label not in index["by_entity"]:
                        index["by_entity"][entity_label] = []
                    index["by_entity"][entity_label].append(str(block.id))

        return index

    def _block_to_dict(self, block: ContentBlock) -> dict[str, Any]:
        """Convertir un bloc en dictionnaire."""
        return {
            "id": str(block.id),
            "type": block.content_type.value,
            "content": block.content,
            "metadata": {
                "page_number": block.metadata.page_number,
                "order": block.metadata.order,
                "section_title": block.metadata.section_title,
                "section_level": block.metadata.section_level,
                **block.metadata.additional_metadata,
            },
            "entities": block.entities,
            "relevance_score": block.relevance_score,
        }

    def _calculate_statistics(
        self, content_blocks: list[ContentBlock]
    ) -> dict[str, Any]:
        """Calculer les statistiques du document."""
        stats = {
            "total_blocks": len(content_blocks),
            "by_type": {},
            "total_entities": 0,
            "total_pages": 0,
        }

        pages = set()

        for block in content_blocks:
            # Compter par type
            block_type = block.content_type.value
            stats["by_type"][block_type] = stats["by_type"].get(block_type, 0) + 1

            # Compter les entités
            stats["total_entities"] += len(block.entities)

            # Compter les pages
            if block.metadata.page_number:
                pages.add(block.metadata.page_number)

        stats["total_pages"] = len(pages)

        return stats

