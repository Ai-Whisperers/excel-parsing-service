"""
Client for communicating with Java layer
"""

import httpx
import logging
from typing import Optional
from fastapi import UploadFile

logger = logging.getLogger(__name__)


class JavaLayerClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout

    async def health_check(self) -> str:
        """Check Java layer health"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/excel/health")
            return response.text if response.status_code == 200 else "unhealthy"
        except Exception as e:
            logger.error(f"Java layer health check failed: {e}")
            return "unhealthy"

    async def parse_excel(
        self,
        file: UploadFile,
        sheet_name: Optional[str] = None,
        region: Optional[str] = None
    ) -> dict:
        """
        Send Excel file to Java layer for parsing
        """
        logger.info(f"Sending Excel file to Java layer: {file.filename}")

        # Prepare multipart form data
        files = {"file": (file.filename, await file.read(), file.content_type)}
        params = {}
        if sheet_name:
            params["sheetName"] = sheet_name
        if region:
            params["region"] = region

        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/excel/parse",
                files=files,
                params=params
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error calling Java layer: {e}")
            raise Exception(f"Java layer error: {str(e)}")

    async def parse_excel_from_path(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        region: Optional[str] = None
    ) -> dict:
        """
        Request Java layer to parse Excel from file path
        """
        logger.info(f"Requesting Java layer to parse: {file_path}")

        payload = {
            "filePath": file_path,
            "sheetName": sheet_name,
            "region": region
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/excel/parse-from-path",
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error calling Java layer: {e}")
            raise Exception(f"Java layer error: {str(e)}")

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
