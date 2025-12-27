"""Structurateur de tableaux."""

from typing import Any

from app.core.logging import get_logger
from app.domain.value_objects.extraction_result import TableBlock
from app.infrastructure.structurers.base import BaseStructurer


class TableStructurer(BaseStructurer):
    """Structurateur spécialisé pour les tableaux."""

    def __init__(self, logger: Any = None) -> None:
        """Initialiser le structurateur."""
        super().__init__(logger or get_logger(__name__))

    async def structure(self, table_block: TableBlock) -> dict[str, Any]:
        """
        Structurer un tableau en format JSON.

        Args:
            table_block: Tableau à structurer

        Returns:
            Dictionnaire structuré du tableau
        """
        # Générer le schéma automatique
        schema = self._generate_schema(table_block)

        # Convertir en format structuré
        structured_table = {
            "id": str(table_block.metadata.order) if table_block.metadata.order else None,
            "headers": table_block.headers,
            "schema": schema,
            "rows": self._structure_rows(table_block.rows, schema),
            "row_count": len(table_block.rows),
            "column_count": len(table_block.headers),
            "metadata": {
                "page_number": table_block.metadata.page_number,
                "extraction_method": table_block.metadata.extraction_method,
                **table_block.metadata.additional_metadata,
            },
        }

        return structured_table

    def _generate_schema(self, table_block: TableBlock) -> dict[str, Any]:
        """Générer le schéma automatique du tableau."""
        schema = {
            "columns": [],
        }

        column_types = table_block.metadata.additional_metadata.get("column_types", [])

        for i, header in enumerate(table_block.headers):
            col_type = column_types[i] if i < len(column_types) else "text"
            schema["columns"].append(
                {
                    "name": header,
                    "type": col_type,
                    "index": i,
                }
            )

        return schema

    def _structure_rows(
        self, rows: list[list[Any]], schema: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Structurer les lignes en dictionnaires."""
        structured_rows = []

        for row in rows:
            row_dict = {}
            for i, col in enumerate(schema["columns"]):
                col_name = col["name"]
                if i < len(row):
                    row_dict[col_name] = row[i]
                else:
                    row_dict[col_name] = None

            structured_rows.append(row_dict)

        return structured_rows

    def to_csv_format(self, table_block: TableBlock) -> str:
        """Convertir un tableau en format CSV-ready."""
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Écrire les en-têtes
        writer.writerow(table_block.headers)

        # Écrire les lignes
        for row in table_block.rows:
            writer.writerow(row)

        return output.getvalue()

