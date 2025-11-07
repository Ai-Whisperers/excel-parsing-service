"""
Data Aggregator
Aggregates and transforms parsed Excel data from Java layer
"""

import logging
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict
import pandas as pd

logger = logging.getLogger(__name__)


class DataAggregator:
    def aggregate(self, parse_response: dict) -> dict:
        """
        Aggregate parsed Excel data:
        - Convert cell data to tabular format per sheet
        - Extract rich metadata (formulas, styles, comments)
        - Compute advanced statistics
        - Detect data quality issues
        """
        logger.info("Aggregating parsed data")

        try:
            aggregated = {
                "metadata": parse_response["metadata"],
                "sheets": {},
                "statistics": parse_response.get("data", {}).get("statistics", {}),
                "timestamp": parse_response["timestamp"]
            }

            sheet_data = parse_response.get("data", {}).get("sheetData", {})

            for sheet_name, cells in sheet_data.items():
                logger.debug(f"Aggregating sheet: {sheet_name}")

                # Convert to enhanced tabular format
                table = self._cells_to_table(cells)

                # Extract rich metadata
                rich_metadata = self._extract_rich_metadata(cells)

                # Compute aggregated statistics
                agg_stats = self._compute_aggregated_statistics(table, cells)

                # Combine table with metadata
                sheet_result = {
                    **table,
                    "richMetadata": rich_metadata,
                    "aggregatedStats": agg_stats
                }

                aggregated["sheets"][sheet_name] = sheet_result

            logger.info(f"Aggregated {len(aggregated['sheets'])} sheets")
            return aggregated

        except Exception as e:
            logger.error(f"Error aggregating data: {e}", exc_info=True)
            raise

    def _cells_to_table(self, cells: List[dict]) -> dict:
        """
        Convert cell list to enhanced tabular structure
        Handles merged cells, preserves formulas, and detects headers
        """
        if not cells:
            return {
                "columns": [],
                "rows": [],
                "rowCount": 0,
                "columnCount": 0
            }

        # Find actual data dimensions
        max_row = max((cell.get("rowIndex", 0) for cell in cells), default=0)
        max_col = max((cell.get("columnIndex", 0) for cell in cells), default=0)

        # Initialize grid for values and metadata
        value_grid = [[None] * (max_col + 1) for _ in range(max_row + 1)]
        cell_meta_grid = [[{} for _ in range(max_col + 1)] for _ in range(max_row + 1)]

        # Fill grids
        for cell in cells:
            row_idx = cell.get("rowIndex", 0)
            col_idx = cell.get("columnIndex", 0)

            # Store value
            value_grid[row_idx][col_idx] = cell.get("value")

            # Store cell metadata
            meta = {}
            if cell.get("formula"):
                meta["formula"] = cell["formula"]
            if cell.get("comment"):
                meta["comment"] = cell["comment"]
            if cell.get("hyperlink"):
                meta["hyperlink"] = cell["hyperlink"]
            if cell.get("merged"):
                meta["merged"] = True
                meta["mergeRegion"] = cell.get("mergeRegion")
            if cell.get("cellType"):
                meta["type"] = cell["cellType"]
            if cell.get("error"):
                meta["error"] = cell["error"]

            cell_meta_grid[row_idx][col_idx] = meta

        # Detect if first row is header
        has_header = self._detect_header_row(value_grid, cells)

        if has_header and len(value_grid) > 0:
            # Use first row as column names
            columns = [
                str(val) if val is not None else f"Column_{i}"
                for i, val in enumerate(value_grid[0])
            ]
            data_rows = value_grid[1:]
            header_row_index = 0
        else:
            # Generate column names
            columns = [f"Column_{i}" for i in range(max_col + 1)]
            data_rows = value_grid
            header_row_index = None

        return {
            "columns": columns,
            "rows": data_rows,
            "rowCount": len(data_rows),
            "columnCount": len(columns),
            "hasHeader": has_header,
            "headerRowIndex": header_row_index,
            "cellMetadata": cell_meta_grid
        }

    def _detect_header_row(self, grid: List[List], cells: List[dict]) -> bool:
        """
        Detect if first row is likely a header row
        Based on:
        - All string values
        - Different from subsequent rows
        - No duplicate values
        """
        if not grid or len(grid) < 2:
            return False

        first_row = grid[0]
        if not first_row or all(v is None for v in first_row):
            return False

        # Check if all non-null values in first row are strings/text
        non_null_values = [v for v in first_row if v is not None]
        if not non_null_values:
            return False

        # Get cell types for first row
        first_row_cells = [c for c in cells if c.get("rowIndex") == 0]
        types = [c.get("cellType") for c in first_row_cells]

        # Most values should be STRING type
        string_count = sum(1 for t in types if t == "STRING")
        if string_count / len(types) < 0.7:  # At least 70% strings
            return False

        # Check for uniqueness (no duplicate column names)
        unique_values = set(v for v in non_null_values if isinstance(v, str))
        if len(unique_values) < len(non_null_values) * 0.8:  # Allow some duplicates
            return False

        return True

    def _extract_rich_metadata(self, cells: List[dict]) -> dict:
        """
        Extract rich metadata from cells:
        - Formulas
        - Comments
        - Hyperlinks
        - Merged regions
        - Styles
        """
        rich_meta = {
            "formulas": [],
            "comments": [],
            "hyperlinks": [],
            "mergedRegions": [],
            "errorCells": []
        }

        for cell in cells:
            cell_ref = cell.get("cellReference", f"R{cell.get('rowIndex')}C{cell.get('columnIndex')}")

            # Formulas
            if cell.get("formula"):
                rich_meta["formulas"].append({
                    "cellReference": cell_ref,
                    "formula": cell["formula"],
                    "result": cell.get("value"),
                    "resultType": cell.get("formulaResultType")
                })

            # Comments
            if cell.get("comment"):
                rich_meta["comments"].append({
                    "cellReference": cell_ref,
                    "comment": cell["comment"],
                    "author": cell.get("commentAuthor")
                })

            # Hyperlinks
            if cell.get("hyperlink"):
                rich_meta["hyperlinks"].append({
                    "cellReference": cell_ref,
                    "url": cell["hyperlink"],
                    "type": cell.get("hyperlinkType")
                })

            # Merged regions (only master cells)
            if cell.get("merged") and cell.get("mergedCellMaster"):
                rich_meta["mergedRegions"].append({
                    "masterCell": cell_ref,
                    "region": cell.get("mergeRegion")
                })

            # Error cells
            if cell.get("error"):
                rich_meta["errorCells"].append({
                    "cellReference": cell_ref,
                    "error": cell["error"],
                    "value": cell.get("value")
                })

        # Add counts
        rich_meta["counts"] = {
            "formulas": len(rich_meta["formulas"]),
            "comments": len(rich_meta["comments"]),
            "hyperlinks": len(rich_meta["hyperlinks"]),
            "mergedRegions": len(rich_meta["mergedRegions"]),
            "errorCells": len(rich_meta["errorCells"])
        }

        return rich_meta

    def _compute_aggregated_statistics(self, table: dict, cells: List[dict]) -> dict:
        """
        Compute aggregated statistics for the table
        """
        stats = {
            "rowCount": table["rowCount"],
            "columnCount": table["columnCount"],
            "totalCells": table["rowCount"] * table["columnCount"]
        }

        # Count cell types
        type_counts = defaultdict(int)
        for cell in cells:
            cell_type = cell.get("cellType", "UNKNOWN")
            type_counts[cell_type] += 1

        stats["cellTypeCounts"] = dict(type_counts)

        # Null/empty analysis
        null_count = sum(1 for cell in cells if cell.get("value") is None)
        stats["nullCells"] = null_count
        stats["nullPercentage"] = (null_count / len(cells) * 100) if cells else 0

        # Numeric summary (if available from Java layer statistics)
        numeric_cells = [
            cell for cell in cells
            if cell.get("cellType") == "NUMERIC" and cell.get("value") is not None
        ]

        if numeric_cells:
            numeric_values = [cell["value"] for cell in numeric_cells]
            stats["numericSummary"] = {
                "count": len(numeric_values),
                "min": min(numeric_values),
                "max": max(numeric_values),
                "avg": sum(numeric_values) / len(numeric_values) if numeric_values else 0
            }

        return stats
