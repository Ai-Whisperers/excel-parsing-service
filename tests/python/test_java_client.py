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
    with patch.object(java_client.client, 'get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "healthy"
        mock_get.return_value = mock_response

        result = await java_client.health_check()
        assert result == "healthy"


@pytest.mark.asyncio
async def test_health_check_failure(java_client):
    with patch.object(java_client.client, 'get') as mock_get:
        mock_get.side_effect = Exception("Connection failed")

        result = await java_client.health_check()
        assert result == "unhealthy"


@pytest.mark.asyncio
async def test_parse_excel_success(java_client):
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.xlsx"
    mock_file.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    mock_file.read = AsyncMock(return_value=b"test data")

    mock_response_data = {
        "metadata": {},
        "data": {"sheetData": {}},
        "timestamp": "2025-11-08T00:00:00"
    }

    with patch.object(java_client.client, 'post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = await java_client.parse_excel(mock_file)

        assert result == mock_response_data


@pytest.mark.asyncio
async def test_parse_excel_from_path_success(java_client):
    mock_response_data = {
        "metadata": {},
        "data": {"sheetData": {}},
        "timestamp": "2025-11-08T00:00:00"
    }

    with patch.object(java_client.client, 'post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = await java_client.parse_excel_from_path("/path/to/file.xlsx")

        assert result == mock_response_data


@pytest.mark.asyncio
async def test_parse_excel_http_error(java_client):
    import httpx

    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.xlsx"
    mock_file.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    mock_file.read = AsyncMock(return_value=b"test data")

    with patch.object(java_client.client, 'post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.raise_for_status = Mock(side_effect=httpx.HTTPStatusError("Internal error", request=Mock(), response=mock_response))
        mock_post.return_value = mock_response

        with pytest.raises(Exception):
            await java_client.parse_excel(mock_file)
