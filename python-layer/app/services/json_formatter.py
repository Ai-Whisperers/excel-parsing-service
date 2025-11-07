"""
JSON Formatter
Formats aggregated data to JSON
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class JSONFormatter:
    def format(self, aggregated_data: dict) -> dict:
        """
        Format aggregated data to structured JSON
        """
        logger.info("Formatting data to JSON")

        try:
            formatted = {
                "success": True,
                "metadata": aggregated_data["metadata"],
                "sheets": {},
                "statistics": aggregated_data.get("statistics", {}),
                "timestamp": aggregated_data["timestamp"]
            }

            for sheet_name, sheet_data in aggregated_data["sheets"].items():
                formatted["sheets"][sheet_name] = {
                    "columns": sheet_data["columns"],
                    "data": sheet_data["rows"],
                    "rowCount": sheet_data["rowCount"],
                    "columnCount": sheet_data["columnCount"]
                }

            logger.info(f"Formatted {len(formatted['sheets'])} sheets to JSON")
            return formatted

        except Exception as e:
            logger.error(f"Error formatting to JSON: {e}")
            raise
