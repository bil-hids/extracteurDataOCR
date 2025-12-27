"""Formateur Markdown pour convertir les données structurées en Markdown."""

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class MarkdownFormatter:
    """Formateur pour convertir les données de document en Markdown."""

    def __init__(self) -> None:
        """Initialiser le formateur."""
        self.logger = logger

    def format_document(
        self,
        document_info: dict[str, Any],
        content_blocks: dict[str, Any],
        structured_data: dict[str, Any] | None = None,
    ) -> str:
        """
        Formater un document complet en Markdown.

        Args:
            document_info: Informations sur le document
            content_blocks: Blocs de contenu (text_blocks, tables, images)
            structured_data: Données structurées optionnelles

        Returns:
            Contenu Markdown formaté
        """
        markdown_lines: list[str] = []

        # En-tête du document
        markdown_lines.append(f"# {document_info.get('filename', 'Document')}")
        markdown_lines.append("")
        markdown_lines.append("---")
        markdown_lines.append("")

        # Métadonnées du document
        if document_info:
            markdown_lines.append("## Métadonnées")
            markdown_lines.append("")
            if document_info.get("file_type"):
                markdown_lines.append(f"- **Type de fichier:** {document_info['file_type']}")
            if document_info.get("file_size"):
                size_mb = document_info["file_size"] / (1024 * 1024)
                markdown_lines.append(f"- **Taille:** {size_mb:.2f} MB")
            if document_info.get("status"):
                markdown_lines.append(f"- **Statut:** {document_info['status']}")
            if document_info.get("created_at"):
                markdown_lines.append(f"- **Créé le:** {document_info['created_at']}")
            markdown_lines.append("")
            markdown_lines.append("---")
            markdown_lines.append("")

        # Contenu principal
        markdown_lines.append("## Contenu")
        markdown_lines.append("")

        # Trier les blocs par ordre (si disponible)
        all_blocks: list[dict[str, Any]] = []

        # Ajouter les blocs de texte
        text_blocks = content_blocks.get("text_blocks", [])
        for block in text_blocks:
            all_blocks.append({**block, "type": "text"})

        # Ajouter les tableaux
        tables = content_blocks.get("tables", [])
        for block in tables:
            all_blocks.append({**block, "type": "table"})

        # Ajouter les images
        images = content_blocks.get("images", [])
        for block in images:
            all_blocks.append({**block, "type": "image"})

        # Trier par page_number et order si disponibles
        all_blocks.sort(
            key=lambda b: (
                b.get("metadata", {}).get("page_number", 0),
                b.get("metadata", {}).get("order", 0),
            )
        )

        # Formater chaque bloc
        for block in all_blocks:
            block_type = block.get("type", block.get("content_type", "text"))
            content = block.get("content", {})
            metadata = block.get("metadata", {})

            if block_type in ("text", "heading"):
                markdown_lines.extend(self._format_text_block(content, metadata))
            elif block_type == "table":
                markdown_lines.extend(self._format_table_block(content, metadata))
            elif block_type == "image":
                markdown_lines.extend(self._format_image_block(content, metadata))

            markdown_lines.append("")

        return "\n".join(markdown_lines)

    def _format_text_block(self, content: dict[str, Any], metadata: dict[str, Any]) -> list[str]:
        """Formater un bloc de texte en Markdown."""
        lines: list[str] = []

        # Récupérer le texte - peut être dans différents champs
        text = (
            content.get("text")
            or content.get("content")
            or (content.get("text") if isinstance(content.get("text"), str) else "")
            or str(content) if content else ""
        )
        
        # Si content est directement une string
        if isinstance(content, str):
            text = content
        
        if not text or (isinstance(text, dict) and not text):
            return lines

        # Nettoyer le texte
        if isinstance(text, dict):
            # Essayer de trouver du texte dans le dict
            text = text.get("text", text.get("content", ""))
        
        text = str(text).strip()
        if not text:
            return lines

        # Vérifier si c'est un titre
        heading_level = (
            metadata.get("heading_level")
            or metadata.get("section_level")
            or metadata.get("additional_metadata", {}).get("heading_level")
        )
        
        # Vérifier aussi le content_type dans metadata
        content_type = metadata.get("content_type", "")
        if content_type == "heading" and not heading_level:
            heading_level = 2  # Par défaut niveau 2

        if heading_level:
            # C'est un titre
            level = min(int(heading_level), 6)  # Markdown supporte jusqu'à 6 niveaux
            lines.append(f"{'#' * level} {text}")
        else:
            # C'est du texte normal
            lines.append(text)

        # Ajouter des métadonnées en commentaire si disponibles (optionnel, commenté pour garder le Markdown propre)
        # if metadata.get("extraction_method"):
        #     lines.append(f"<!-- Méthode: {metadata['extraction_method']} -->")

        return lines

    def _format_table_block(self, content: dict[str, Any], metadata: dict[str, Any]) -> list[str]:
        """Formater un tableau en Markdown."""
        lines: list[str] = []

        # Récupérer headers et rows
        headers = content.get("headers", [])
        rows = content.get("rows", [])

        # Si content est directement une liste (tableau brut)
        if isinstance(content, list) and not headers and not rows:
            if content and isinstance(content[0], list):
                headers = content[0] if content else []
                rows = content[1:] if len(content) > 1 else []

        if not headers and not rows:
            return lines

        # Si pas de headers mais des rows, utiliser la première row comme header
        if not headers and rows:
            headers = rows[0] if rows else []
            rows = rows[1:] if len(rows) > 1 else []

        if not headers:
            return lines

        # Nettoyer les headers (s'assurer qu'ils sont des strings)
        headers = [str(h).strip() if h else "" for h in headers]

        # Créer le tableau Markdown
        # Headers
        header_row = "| " + " | ".join(headers) + " |"
        lines.append(header_row)

        # Séparateur
        separator = "| " + " | ".join("---" for _ in headers) + " |"
        lines.append(separator)

        # Rows
        for row in rows:
            if not isinstance(row, list):
                continue
            # S'assurer que la row a le même nombre de colonnes que les headers
            while len(row) < len(headers):
                row.append("")
            row_data = row[: len(headers)]  # Tronquer si trop long
            # Nettoyer les cellules
            row_data = [str(cell).strip() if cell else "" for cell in row_data]
            row_markdown = "| " + " | ".join(row_data) + " |"
            lines.append(row_markdown)

        return lines

    def _format_image_block(self, content: dict[str, Any], metadata: dict[str, Any]) -> list[str]:
        """Formater un bloc d'image en Markdown."""
        lines: list[str] = []

        # Récupérer les informations de l'image
        image_path = content.get("image_path", "")
        ocr_text = content.get("ocr_text", metadata.get("ocr_text", ""))

        # Créer le texte alternatif
        alt_text = metadata.get("alt_text", "Image")
        if ocr_text:
            alt_text = f"{alt_text} (Texte OCR: {ocr_text[:100]}...)" if len(ocr_text) > 100 else f"{alt_text} (Texte OCR: {ocr_text})"

        # Format Markdown pour l'image
        if image_path:
            lines.append(f"![{alt_text}]({image_path})")
        else:
            lines.append(f"![{alt_text}]")

        # Ajouter le texte OCR si disponible
        if ocr_text:
            lines.append("")
            lines.append(f"**Texte extrait (OCR):**")
            lines.append("")
            lines.append(f"> {ocr_text}")
            lines.append("")

        # Ajouter des métadonnées
        if metadata.get("width") and metadata.get("height"):
            lines.append(f"*Dimensions: {metadata['width']}x{metadata['height']}*")

        return lines

