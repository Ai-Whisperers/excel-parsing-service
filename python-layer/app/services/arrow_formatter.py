"""
Arrow Formatter
Formats aggregated data to Apache Arrow format
"""

import logging
import pyarrow as pa
import pyarrow.ipc as ipc
from io import BytesIO
from typing import Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


class ArrowFormatter:
    def format(self, aggregated_data: dict) -> bytes:
        """
        Format aggregated data to Arrow IPC stream
        """
        logger.info("Formatting data to Arrow")

        try:
            # Create Arrow tables for each sheet
            tables = {}

            for sheet_name, sheet_data in aggregated_data["sheets"].items():
                logger.debug(f"Converting sheet to Arrow: {sheet_name}")
                table = self._create_arrow_table(sheet_name, sheet_data)
                tables[sheet_name] = table

            # Write to Arrow IPC stream
            arrow_bytes = self._write_arrow_stream(tables)

            logger.info(f"Formatted {len(tables)} sheets to Arrow ({len(arrow_bytes)} bytes)")
            return arrow_bytes

        except Exception as e:
            logger.error(f"Error formatting to Arrow: {e}")
            raise

    def _create_arrow_table(self, sheet_name: str, sheet_data: dict) -> pa.Table:
        """Create Arrow table from sheet data"""
        columns = sheet_data["columns"]
        rows = sheet_data["rows"]

        # Transpose rows to columns
        arrays = []
        for col_idx, col_name in enumerate(columns):
            col_values = [row[col_idx] if col_idx < len(row) else None for row in rows]
            arrays.append(pa.array(col_values))

        return pa.table(arrays, names=columns)

    def _write_arrow_stream(self, tables: Dict[str, pa.Table]) -> bytes:
        """Write Arrow tables to IPC stream"""
        buffer = BytesIO()

        if not tables:
            return buffer.getvalue()

        # For single sheet, write directly without sheet_name column
        if len(tables) == 1:
            table = list(tables.values())[0]
            writer = ipc.new_stream(buffer, table.schema)
            writer.write_table(table)
            writer.close()
            return buffer.getvalue()

        # For multiple sheets, concatenate them with a sheet_name column
        combined_tables = []
        for sheet_name, table in tables.items():
            # Add sheet_name column to track origin
            sheet_col = pa.array([sheet_name] * table.num_rows)
            table_with_sheet = table.append_column("_sheet_name", sheet_col)
            combined_tables.append(table_with_sheet)

        # Concatenate all tables vertically with schema promotion for different columns
        final_table = pa.concat_tables(combined_tables, promote_options="default")

        writer = ipc.new_stream(buffer, final_table.schema)
        writer.write_table(final_table)
        writer.close()

        return buffer.getvalue()
