#!/usr/bin/env python3
"""
Custom MCP Server for Excel POI Parser
Provides tools for interacting with the two-layer architecture
"""

import asyncio
import logging
import os
from typing import Any, Dict
import httpx
from mcp.server import Server, Tool
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
JAVA_LAYER_URL = os.getenv("JAVA_LAYER_URL", "http://localhost:8080")
PYTHON_LAYER_URL = os.getenv("PYTHON_LAYER_URL", "http://localhost:8000")

# Initialize MCP server
server = Server("excel-parser")

# HTTP client
http_client = httpx.AsyncClient(timeout=300.0)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Excel parsing tools"""
    return [
        Tool(
            name="parse_excel_file",
            description="Parse Excel file and return JSON format via Python aggregation layer",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to Excel file"
                    },
                    "sheet_name": {
                        "type": "string",
                        "description": "Optional: specific sheet name to parse"
                    },
                    "region": {
                        "type": "string",
                        "description": "Optional: cell region (e.g., A1:D10)"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="parse_excel_arrow",
            description="Parse Excel file and return Apache Arrow format",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "sheet_name": {"type": "string"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="get_workbook_metadata",
            description="Extract workbook metadata without full parse",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="list_sheets",
            description="Get list of sheet names from workbook",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="extract_sheet",
            description="Extract specific sheet data",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "sheet_name": {"type": "string"}
                },
                "required": ["file_path", "sheet_name"]
            }
        ),
        Tool(
            name="extract_region",
            description="Extract specific cell range from a sheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "sheet_name": {"type": "string"},
                    "region": {
                        "type": "string",
                        "description": "Cell range (e.g., A1:D10)"
                    }
                },
                "required": ["file_path", "sheet_name", "region"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tool calls"""
    logger.info(f"Tool called: {name} with args: {arguments}")

    try:
        if name == "parse_excel_file":
            return await parse_excel_file_impl(arguments)
        elif name == "parse_excel_arrow":
            return await parse_excel_arrow_impl(arguments)
        elif name == "get_workbook_metadata":
            return await get_workbook_metadata_impl(arguments)
        elif name == "list_sheets":
            return await list_sheets_impl(arguments)
        elif name == "extract_sheet":
            return await extract_sheet_impl(arguments)
        elif name == "extract_region":
            return await extract_region_impl(arguments)
        else:
            return {"error": f"Unknown tool: {name}"}

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return {"error": str(e)}


async def parse_excel_file_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Excel file via Python aggregation layer"""
    file_path = args["file_path"]
    sheet_name = args.get("sheet_name")
    region = args.get("region")

    payload = {
        "file_path": file_path,
        "sheet_name": sheet_name,
        "region": region,
        "output_format": "json",
        "aggregate": True
    }

    response = await http_client.post(
        f"{PYTHON_LAYER_URL}/api/v1/process/excel-from-path",
        json=payload
    )
    response.raise_for_status()

    return response.json()


async def parse_excel_arrow_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Excel file and return Arrow format"""
    file_path = args["file_path"]
    sheet_name = args.get("sheet_name")

    payload = {
        "file_path": file_path,
        "sheet_name": sheet_name,
        "output_format": "arrow",
        "aggregate": True
    }

    response = await http_client.post(
        f"{PYTHON_LAYER_URL}/api/v1/process/excel-from-path",
        json=payload
    )
    response.raise_for_status()

    # Arrow binary data
    return {
        "format": "arrow",
        "size_bytes": len(response.content),
        "message": "Arrow data received (binary format not shown in text)"
    }


async def get_workbook_metadata_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get workbook metadata via Java layer"""
    file_path = args["file_path"]

    payload = {
        "filePath": file_path
    }

    response = await http_client.post(
        f"{JAVA_LAYER_URL}/api/v1/excel/parse-from-path",
        json=payload
    )
    response.raise_for_status()

    data = response.json()
    return {
        "metadata": data.get("metadata"),
        "timestamp": data.get("timestamp")
    }


async def list_sheets_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """List sheet names from workbook"""
    metadata = await get_workbook_metadata_impl(args)

    sheets = metadata.get("metadata", {}).get("sheets", {})
    return {
        "sheets": list(sheets.keys()),
        "count": len(sheets)
    }


async def extract_sheet_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Extract specific sheet"""
    file_path = args["file_path"]
    sheet_name = args["sheet_name"]

    payload = {
        "file_path": file_path,
        "sheet_name": sheet_name,
        "output_format": "json",
        "aggregate": True
    }

    response = await http_client.post(
        f"{PYTHON_LAYER_URL}/api/v1/process/excel-from-path",
        json=payload
    )
    response.raise_for_status()

    return response.json()


async def extract_region_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Extract specific cell range"""
    file_path = args["file_path"]
    sheet_name = args["sheet_name"]
    region = args["region"]

    payload = {
        "file_path": file_path,
        "sheet_name": sheet_name,
        "region": region,
        "output_format": "json",
        "aggregate": True
    }

    response = await http_client.post(
        f"{PYTHON_LAYER_URL}/api/v1/process/excel-from-path",
        json=payload
    )
    response.raise_for_status()

    return response.json()


async def main():
    """Run the MCP server"""
    logger.info("Starting Excel Parser MCP Server")
    logger.info(f"Java Layer URL: {JAVA_LAYER_URL}")
    logger.info(f"Python Layer URL: {PYTHON_LAYER_URL}")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
