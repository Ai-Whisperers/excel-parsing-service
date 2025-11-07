# Excel Parser MCP Server

Custom MCP server providing tools for interacting with the Excel POI Parser two-layer architecture.

## Overview

This MCP server acts as a bridge between AI agents and the Excel POI Parser service, providing high-level tools for Excel file operations.

## Architecture

```
AI Agent
    ↓
MCP Server (this)
    ↓
Python Layer (Port 8000) ← Aggregation & Formatting
    ↓
Java Layer (Port 8080) ← Apache POI Parsing
```

## Available Tools

### 1. parse_excel_file
Parse an Excel file and return JSON format.

**Parameters:**
- `file_path` (required): Path to Excel file
- `sheet_name` (optional): Specific sheet to parse
- `region` (optional): Cell region (e.g., "A1:D10")

**Example:**
```python
{
  "file_path": "/data/sample.xlsx",
  "sheet_name": "Sales",
  "region": "A1:D100"
}
```

### 2. parse_excel_arrow
Parse an Excel file and return Apache Arrow format.

**Parameters:**
- `file_path` (required): Path to Excel file
- `sheet_name` (optional): Specific sheet to parse

### 3. get_workbook_metadata
Extract workbook metadata without full parse (faster).

**Parameters:**
- `file_path` (required): Path to Excel file

**Returns:**
```json
{
  "metadata": {
    "numberOfSheets": 3,
    "sheets": {"Sheet1": 0, "Sheet2": 1}
  }
}
```

### 4. list_sheets
Get list of sheet names.

**Parameters:**
- `file_path` (required): Path to Excel file

**Returns:**
```json
{
  "sheets": ["Sheet1", "Sheet2", "Sheet3"],
  "count": 3
}
```

### 5. extract_sheet
Extract data from a specific sheet.

**Parameters:**
- `file_path` (required): Path to Excel file
- `sheet_name` (required): Sheet name

### 6. extract_region
Extract data from a specific cell range.

**Parameters:**
- `file_path` (required): Path to Excel file
- `sheet_name` (required): Sheet name
- `region` (required): Cell range (e.g., "A1:D10")

## Configuration

Environment variables:
- `JAVA_LAYER_URL`: Java layer endpoint (default: http://localhost:8080)
- `PYTHON_LAYER_URL`: Python layer endpoint (default: http://localhost:8000)
- `LOG_LEVEL`: Logging level (default: INFO)

## Building

```bash
docker build -t excel-parser-mcp .
```

## Running Standalone

```bash
docker run -it \
  -e JAVA_LAYER_URL=http://java-layer:8080 \
  -e PYTHON_LAYER_URL=http://python-layer:8000 \
  excel-parser-mcp
```

## Development

### Adding New Tools

1. Add tool definition in `list_tools()`:
```python
Tool(
    name="your_tool_name",
    description="What it does",
    inputSchema={...}
)
```

2. Implement the tool function:
```python
async def your_tool_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    # Implementation
    return result
```

3. Add handler in `call_tool()`:
```python
elif name == "your_tool_name":
    return await your_tool_impl(arguments)
```

### Testing

```bash
# Test with MCP client
python test_server.py

# Or use Docker AI
docker ai "List sheets in sample.xlsx"
```

## Error Handling

The server handles these errors:
- File not found
- Invalid Excel format
- Java/Python layer unavailable
- Network timeouts (5 minutes)

Errors are logged and returned in response:
```json
{
  "error": "Error message details"
}
```

## Performance

- **Metadata extraction**: < 1 second
- **Sheet listing**: < 1 second
- **Full parse**: 1-30 seconds (depends on file size)
- **Timeout**: 5 minutes for large files

## Integration

Used by:
- Docker AI (via gordon-mcp.yml)
- MCP Gateway (via docker-compose.mcp-gateway.yml)
- Claude Desktop (via MCP protocol)
- Cursor IDE (via MCP protocol)

## Troubleshooting

### Server won't start

```bash
# Check logs
docker logs excel-parser-mcp-server

# Verify dependencies
docker exec -it excel-parser-mcp-server pip list
```

### Can't connect to layers

```bash
# Test Java layer
curl http://localhost:8080/api/v1/excel/health

# Test Python layer
curl http://localhost:8000/health

# Check network
docker network inspect excel-parser-network
```

### Tools not responding

```bash
# Check server logs
docker logs excel-parser-mcp-server -f

# Verify environment variables
docker exec excel-parser-mcp-server env | grep LAYER
```

## Resources

- [MCP Protocol Spec](https://github.com/anthropics/mcp)
- [Main Documentation](../../../README.md)
- [API Documentation](../../../QUICKSTART.md)
