import pytest
from unittest.mock import AsyncMock, patch, Mock
from app.services.java_client import JavaLayerClient
from fastapi import UploadFile
import io


@pytest.fixture
def java_client():
    return JavaLayerClient("http://localhost:8080")


@pytest.mark.asyncio
async def test_health_check_success(java_client):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="healthy")
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await java_client.health_check()
        assert result == "healthy"


@pytest.mark.asyncio
async def test_health_check_failure(java_client):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.side_effect = Exception("Connection failed")

        result = await java_client.health_check()
        assert "error" in result.lower()


@pytest.mark.asyncio
async def test_parse_excel_success(java_client):
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.xlsx"
    mock_file.read = AsyncMock(return_value=b"test data")

    mock_response_data = {
        "metadata": {},
        "data": {"sheetData": {}},
        "timestamp": "2025-11-08T00:00:00"
    }

    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_post.return_value.__aenter__.return_value = mock_response

        result = await java_client.parse_excel(mock_file)

        assert result == mock_response_data


@pytest.mark.asyncio
async def test_parse_excel_from_path_success(java_client):
    mock_response_data = {
        "metadata": {},
        "data": {"sheetData": {}},
        "timestamp": "2025-11-08T00:00:00"
    }

    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_post.return_value.__aenter__.return_value = mock_response

        result = await java_client.parse_excel_from_path("/path/to/file.xlsx")

        assert result == mock_response_data


@pytest.mark.asyncio
async def test_parse_excel_http_error(java_client):
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.xlsx"
    mock_file.read = AsyncMock(return_value=b"test data")

    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal error")
        mock_post.return_value.__aenter__.return_value = mock_response

        with pytest.raises(Exception):
            await java_client.parse_excel(mock_file)
