"""Normaliseur de tableaux."""

from datetime import datetime
from typing import Any

from app.core.exceptions import ProcessingError
from app.core.logging import get_logger
from app.domain.value_objects.extraction_result import TableBlock
from app.infrastructure.processors.base import BaseProcessor


class TableNormalizer(BaseProcessor):
    """Normaliseur de tableaux avec détection automatique d'en-têtes et typage."""

    def __init__(self, logger: Any = None) -> None:
        """Initialiser le normaliseur."""
        super().__init__(logger or get_logger(__name__))

    async def normalize(self, table_block: TableBlock) -> TableBlock:
        """
        Normaliser un tableau.

        Args:
            table_block: Tableau à normaliser

        Returns:
            Tableau normalisé avec en-têtes détectés et colonnes typées
        """
        try:
            normalized = self._normalize_sync(table_block)
            return normalized
        except Exception as e:
            self.logger.exception(f"Erreur lors de la normalisation: {e}")
            raise ProcessingError(f"Échec de la normalisation: {str(e)}")

    def _normalize_sync(self, table_block: TableBlock) -> TableBlock:
        """Normalisation synchrone."""
        # Détecter les en-têtes
        headers = self._detect_headers(table_block)

        # Nettoyer les données
        cleaned_rows = self._clean_rows(table_block.rows)

        # Typer les colonnes
        column_types = self._detect_column_types(headers, cleaned_rows)

        # Valider la cohérence
        validated_rows = self._validate_rows(cleaned_rows, column_types)

        # Mettre à jour les métadonnées
        table_block.metadata.additional_metadata.update(
            {
                "column_types": column_types,
                "row_count": len(validated_rows),
                "column_count": len(headers),
                "normalized": True,
            }
        )

        # Mettre à jour le tableau
        table_block.headers = headers
        table_block.rows = validated_rows

        return table_block

    def _detect_headers(self, table_block: TableBlock) -> list[str]:
        """Détecter automatiquement les en-têtes."""
        # Si des en-têtes existent déjà, les utiliser
        if table_block.headers:
            return [self._clean_cell(h) for h in table_block.headers]

        # Sinon, utiliser la première ligne
        if table_block.rows:
            first_row = table_block.rows[0]
            # Vérifier si la première ligne ressemble à des en-têtes
            # (texte, pas de nombres majoritaires)
            if self._looks_like_headers(first_row):
                headers = [self._clean_cell(cell) for cell in first_row]
                # Retirer la première ligne des données
                table_block.rows = table_block.rows[1:]
                return headers

        # Générer des en-têtes par défaut
        if table_block.rows:
            num_cols = len(table_block.rows[0])
            return [f"Colonne_{i+1}" for i in range(num_cols)]

        return []

    def _looks_like_headers(self, row: list[Any]) -> bool:
        """Vérifier si une ligne ressemble à des en-têtes."""
        if not row:
            return False

        text_count = sum(1 for cell in row if isinstance(cell, str) and cell.strip())
        return text_count > len(row) / 2

    def _clean_cell(self, cell: Any) -> str:
        """Nettoyer une cellule."""
        if cell is None:
            return ""
        return str(cell).strip()

    def _clean_rows(self, rows: list[list[Any]]) -> list[list[Any]]:
        """Nettoyer les lignes du tableau."""
        cleaned = []
        for row in rows:
            cleaned_row = [self._clean_cell(cell) for cell in row]
            # Ignorer les lignes complètement vides
            if any(cell for cell in cleaned_row):
                cleaned.append(cleaned_row)
        return cleaned

    def _detect_column_types(
        self, headers: list[str], rows: list[list[Any]]
    ) -> list[str]:
        """Détecter le type de chaque colonne."""
        if not rows:
            return ["text"] * len(headers)

        column_types: list[str] = []
        num_cols = len(headers) if headers else (len(rows[0]) if rows else 0)

        for col_idx in range(num_cols):
            col_values = [row[col_idx] if col_idx < len(row) else None for row in rows]

            # Analyser les valeurs de la colonne
            type_ = self._infer_type(col_values)
            column_types.append(type_)

        return column_types

    def _infer_type(self, values: list[Any]) -> str:
        """Inférer le type d'une colonne depuis ses valeurs."""
        if not values:
            return "text"

        non_empty = [v for v in values if v is not None and str(v).strip()]

        if not non_empty:
            return "text"

        # Vérifier si ce sont des dates
        date_count = sum(1 for v in non_empty if self._is_date(str(v)))
        if date_count > len(non_empty) * 0.7:
            return "date"

        # Vérifier si ce sont des nombres
        number_count = sum(1 for v in non_empty if self._is_number(str(v)))
        if number_count > len(non_empty) * 0.7:
            return "number"

        # Vérifier si ce sont des booléens
        bool_count = sum(1 for v in non_empty if self._is_boolean(str(v)))
        if bool_count > len(non_empty) * 0.7:
            return "boolean"

        return "text"

    def _is_date(self, value: str) -> bool:
        """Vérifier si une valeur ressemble à une date."""
        # Formats de date communs
        date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
        for fmt in date_formats:
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue
        return False

    def _is_number(self, value: str) -> bool:
        """Vérifier si une valeur est un nombre."""
        try:
            float(value.replace(",", ".").replace(" ", ""))
            return True
        except ValueError:
            return False

    def _is_boolean(self, value: str) -> bool:
        """Vérifier si une valeur est un booléen."""
        return value.lower() in ["true", "false", "oui", "non", "yes", "no", "1", "0"]

    def _validate_rows(
        self, rows: list[list[Any]], column_types: list[str]
    ) -> list[list[Any]]:
        """Valider et convertir les lignes selon les types."""
        validated = []
        for row in rows:
            validated_row = []
            for i, cell in enumerate(row):
                if i < len(column_types):
                    validated_cell = self._convert_cell(cell, column_types[i])
                    validated_row.append(validated_cell)
                else:
                    validated_row.append(cell)
            validated.append(validated_row)
        return validated

    def _convert_cell(self, cell: Any, target_type: str) -> Any:
        """Convertir une cellule selon le type cible."""
        if cell is None or (isinstance(cell, str) and not cell.strip()):
            return None

        if target_type == "number":
            try:
                return float(str(cell).replace(",", ".").replace(" ", ""))
            except ValueError:
                return cell

        if target_type == "boolean":
            val = str(cell).lower()
            if val in ["true", "oui", "yes", "1"]:
                return True
            if val in ["false", "non", "no", "0"]:
                return False
            return cell

        if target_type == "date":
            # La conversion de date sera faite plus tard si nécessaire
            return str(cell)

        return str(cell)

    async def normalize_batch(self, table_blocks: list[TableBlock]) -> list[TableBlock]:
        """Normaliser plusieurs tableaux."""
        return [await self.normalize(block) for block in table_blocks]

    async def process(self, *args: Any, **kwargs: Any) -> Any:
        """Implémentation de la méthode abstraite process."""
        # Si un TableBlock est passé, utiliser normalize
        if args and isinstance(args[0], TableBlock):
            return await self.normalize(args[0])
        # Sinon, passer à normalize_batch si c'est une liste
        if args and isinstance(args[0], list):
            return await self.normalize_batch(args[0])
        raise ValueError("TableNormalizer.process() attend un TableBlock ou une liste de TableBlock")

