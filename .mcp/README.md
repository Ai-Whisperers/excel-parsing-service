# MCP (Model Context Protocol) Integration

This directory contains MCP server configurations for the Excel POI Parser microservice, enabling AI agents to interact with the two-layer architecture through standardized interfaces.

## What is MCP?

Model Context Protocol (MCP) is an open protocol that standardizes how AI applications interact with external tools and data sources. This enables AI agents to parse Excel files, query parsing results, and manage the service.

## Architecture Overview

The Excel POI Parser uses a **two-layer architecture**:

1. **Java Layer (Port 8080)**: Apache POI engine for Excel parsing
2. **Python Layer (Port 8000)**: Data aggregation and Arrow/JSON formatting

MCP integration allows AI agents to interact with both layers seamlessly.

## Setup Options

### Option 1: Docker AI (Gordon) - Recommended for Development

Docker Desktop's built-in AI assistant automatically detects MCP configurations.

**File:** `configs/gordon-mcp.yml`

**Usage:**
```bash
# Parse Excel files
docker ai "Parse the Excel file at data/sample.xlsx and return JSON"

# Check service health
docker ai "Check the health status of both Java and Python layers"

# Query API capabilities
docker ai "List all available Excel parsing endpoints"
```

**Available Tools:**
- **filesystem**: Access Excel files and project code
- **fetch**: Test Java/Python layer APIs
- **excel-parser**: Custom MCP server for Excel operations

### Option 2: MCP Gateway - For Production/Advanced Use

Full-featured MCP gateway supporting multiple AI clients (Claude Desktop, Cursor, VSCode).

**File:** `configs/docker-compose.mcp-gateway.yml`

**Start Gateway:**
```bash
docker-compose -f .mcp/configs/docker-compose.mcp-gateway.yml up -d
```

**Gateway URL:** `http://localhost:9090`

## Available MCP Servers

### 1. Filesystem Server
**Image:** `mcp/filesystem`

**Capabilities:**
- Read Excel files (.xls, .xlsx)
- Access Java source code
- Access Python application code
- Read configuration files

**Example Queries:**
- "Read the Excel file at data/sample.xlsx"
- "Show me the Java POI extractor implementation"
- "What Python packages are installed?"

### 2. Fetch Server
**Image:** `mcp/fetch`

**Capabilities:**
- Test Java layer endpoints (Port 8080)
- Test Python layer endpoints (Port 8000)
- Upload Excel files for parsing
- Retrieve parsing results

**Example Queries:**
- "Check Java layer health at http://localhost:8080/api/v1/excel/health"
- "Test Python layer at http://localhost:8000/health"
- "Upload sample.xlsx and get JSON output"

### 3. Excel Parser Server (Custom)
**Location:** `servers/excel-parser/`

**Capabilities:**
- Parse Excel files via Java layer
- Aggregate results via Python layer
- Format output (JSON/Arrow)
- Query metadata and statistics

**Example Queries:**
- "Parse sheet 'Sales' from Q1-2024.xlsx"
- "Extract cells A1:D10 from the first sheet"
- "Get metadata for workbook.xlsx"

## Configuration Files

### gordon-mcp.yml
Docker AI auto-detection configuration.
- **Location:** `.mcp/configs/gordon-mcp.yml`
- **Auto-detected:** Yes (by Docker AI)
- **Services:** Filesystem, Fetch, Custom Excel Parser

### docker-compose.mcp-gateway.yml
Full MCP Gateway orchestration.
- **Location:** `.mcp/configs/docker-compose.mcp-gateway.yml`
- **Manual start:** Required
- **Port:** 9090
- **Supports:** Claude Desktop, Cursor, VSCode

### mcp-catalog.yaml
Catalog of available tools and capabilities.
- **Location:** `.mcp/configs/mcp-catalog.yaml`
- **Used by:** MCP Gateway
- **Format:** YAML

## Integration with AI Clients

### Claude Desktop

**Config Location:** `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

**Add MCP Gateway:**
```json
{
  "mcpServers": {
    "excel-poi-parser": {
      "url": "http://localhost:9090",
      "transport": "sse",
      "description": "Excel POI Parser two-layer service"
    }
  }
}
```

### Cursor / VSCode

**Settings → Extensions → MCP**

Add connection:
- Name: Excel POI Parser
- URL: http://localhost:9090
- Transport: SSE

## Security Considerations

### Filesystem Access
- MCP filesystem server has **read-only** access
- Limited to project directory
- Allowed extensions: `.xlsx`, `.xls`, `.java`, `.py`, `.json`, `.yml`

### Network Access
- Java layer: localhost:8080 only
- Python layer: localhost:8000 only
- No external network access

### File Upload
- Max file size: 100MB (configurable)
- Virus scanning recommended
- Temporary files auto-deleted

## Troubleshooting

### MCP Gateway connection refused

**Solution:**
```bash
# Check if gateway is running
docker ps | grep mcp-gateway

# View logs
docker-compose -f .mcp/configs/docker-compose.mcp-gateway.yml logs

# Restart gateway
docker-compose -f .mcp/configs/docker-compose.mcp-gateway.yml restart
```

### Java layer not responding

**Solution:**
```bash
# Check Java layer health
curl http://localhost:8080/api/v1/excel/health

# Check logs
docker logs excel-parser-java

# Restart Java layer
docker restart excel-parser-java
```

### Python layer not responding

**Solution:**
```bash
# Check Python layer health
curl http://localhost:8000/health

# Check logs
docker logs excel-parser-python

# Restart Python layer
docker restart excel-parser-python
```

## Examples

### Parse Excel File via MCP

```bash
# Using Docker AI
docker ai "Parse data/sample.xlsx and return JSON format"

# Using MCP Gateway (via Claude Desktop)
"Parse the Excel file at /app/data/sample.xlsx, extract all sheets, and format as Arrow"
```

### Query Service Status

```bash
docker ai "Check the status of both Java and Python layers"
```

### Extract Specific Sheet

```bash
docker ai "Extract only the 'Sales' sheet from Q1-2024.xlsx and return statistics"
```

## Resources

- [Docker MCP Documentation](https://docs.docker.com/ai/mcp-catalog-and-toolkit/)
- [Model Context Protocol Spec](https://github.com/anthropics/mcp)
- [Apache POI Documentation](https://poi.apache.org/)
- [PyArrow Documentation](https://arrow.apache.org/docs/python/)

---

**Questions?** Check the [main documentation](../README.md) or [Architecture Guide](ARCHITECTURE.md).
