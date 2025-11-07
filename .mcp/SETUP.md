# MCP Setup Guide

Complete setup guide for integrating MCP with the Excel POI Parser service.

## Quick Start

### Prerequisites

1. **Docker Desktop** - Required for running MCP servers
2. **OpenAI API Key** - Required for custom feedback analyzer tools
3. **Environment File** - Copy `.env.example` to `.env` and add your API key

```bash
# Ensure your .env file has:
OPENAI_API_KEY=sk-your-actual-key-here
```

## Installation Options

### Option 1: Docker AI (Gordon) - Recommended

Docker Desktop's built-in AI automatically detects the `gordon-mcp.yml` configuration.

#### Setup Steps

1. **Build Custom MCP Server**
```bash
docker-compose -f gordon-mcp.yml build feedback-analyzer
```

2. **Pull Built-in MCP Images**
```bash
docker pull mcp/filesystem
docker pull mcp/fetch
docker pull mcp/time
```

3. **Start Services (Automatic)**
Docker AI will automatically start services when you use them:
```bash
docker ai "List files in the data directory"
```

#### Usage Examples

```bash
# Filesystem access
docker ai "Show me the contents of data/samples/feedback.csv"
docker ai "What Python files are in the api/app directory?"

# API testing
docker ai "Check the health status at http://localhost:10000/health"

# Time operations
docker ai "What's the current timestamp in ISO format?"

# Custom feedback analysis
docker ai "Use feedback-analyzer to calculate NPS from ratings: 9, 10, 8, 7, 6"
docker ai "Analyze sentiment of: 'Great product, very satisfied!'"
```

### Option 2: MCP Gateway - For Multiple AI Clients

Run a persistent MCP gateway that Claude Desktop, Cursor, VSCode, and other AI tools can connect to.

#### Setup Steps

1. **Build Custom Server**
```bash
docker-compose -f docker-compose.mcp-gateway.yml build feedback-analyzer
```

2. **Start Gateway**
```bash
docker-compose -f docker-compose.mcp-gateway.yml up -d
```

3. **Verify Running**
```bash
docker-compose -f docker-compose.mcp-gateway.yml ps
```

You should see:
- `customer-feedback-mcp-gateway`
- `feedback-mcp-filesystem`
- `feedback-mcp-fetch`
- `feedback-mcp-time`
- `feedback-mcp-analyzer`

4. **View Logs**
```bash
# All services
docker-compose -f docker-compose.mcp-gateway.yml logs -f

# Specific service
docker logs feedback-mcp-analyzer -f
```

#### Connect AI Clients

**Claude Desktop**

Edit `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac):

```json
{
  "mcpServers": {
    "customer-feedback": {
      "url": "http://localhost:8080",
      "transport": "sse"
    }
  }
}
```

Restart Claude Desktop.

**Cursor IDE**

1. Open Settings → Extensions → MCP
2. Add new connection:
   - Name: Customer Feedback Analyzer
   - URL: http://localhost:8080
   - Transport: SSE

**VSCode with Continue.dev**

Add to Continue configuration:

```json
{
  "mcpServers": [
    {
      "name": "customer-feedback",
      "url": "http://localhost:8080"
    }
  ]
}
```

## Available Tools

### Built-in MCP Servers

1. **filesystem** - Read project files and datasets
   - Read CSV, Excel, JSON, Parquet files
   - List directory contents
   - Search for files

2. **fetch** - Make HTTP requests
   - Test API endpoints
   - Check health status
   - Query external services

3. **time** - Time utilities
   - Get current timestamps
   - Format dates
   - Calculate durations

### Custom Feedback Analyzer Tools

4. **analyze_sentiment** - Sentiment analysis
   - Single or batch text analysis
   - Emotion detection (optional)
   - Confidence scores

5. **calculate_nps** - Net Promoter Score
   - 0-10 rating scale
   - Promoter/Passive/Detractor breakdown
   - Percentage calculations

6. **identify_themes** - Theme extraction
   - AI-powered topic detection
   - Frequency analysis
   - Sentiment per theme

7. **detect_pain_points** - Issue identification
   - Problem detection
   - Severity classification
   - Actionable recommendations

8. **analyze_csv_file** - CSV analysis
   - Automatic data loading
   - Statistical summaries
   - NPS calculation from ratings column

9. **generate_summary** - Executive summaries
   - Brief/Detailed/Executive formats
   - Key findings and metrics
   - Recommendations

## Testing the Setup

### Test Built-in Servers

```bash
# Test filesystem
docker ai "List all CSV files in the data directory"

# Test fetch
docker ai "Make a GET request to http://localhost:10000/health"

# Test time
docker ai "What's the current date and time?"
```

### Test Custom Analyzer

```bash
# Test sentiment analysis
docker ai "Analyze the sentiment of: 'This product exceeded my expectations!'"

# Test NPS calculation
docker ai "Calculate NPS score from these ratings: 10, 9, 8, 9, 10, 7, 6, 9"

# Test CSV analysis
docker ai "Analyze the feedback data in data/samples/feedback.csv"
```

## Troubleshooting

### Docker AI Not Detecting gordon-mcp.yml

**Solution:**
```bash
# Ensure file is in project root
ls gordon-mcp.yml

# Restart Docker Desktop
# Right-click Docker icon → Restart
```

### Custom Server Build Fails

**Solution:**
```bash
# Check build logs
docker-compose -f gordon-mcp.yml build feedback-analyzer --no-cache

# Verify Dockerfile exists
ls .mcp/servers/feedback-analyzer/Dockerfile
```

### OpenAI API Errors

**Check API Key:**
```bash
# Verify in .env
grep OPENAI_API_KEY .env

# Test with curl
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Gateway Connection Refused

**Solution:**
```bash
# Check if gateway is running
docker ps | grep mcp-gateway

# Check gateway logs
docker logs customer-feedback-mcp-gateway

# Restart gateway
docker-compose -f docker-compose.mcp-gateway.yml restart
```

### MCP Server Not Responding

**Solution:**
```bash
# Check server status
docker ps -a | grep feedback

# View server logs
docker logs feedback-mcp-analyzer

# Restart specific server
docker-compose -f docker-compose.mcp-gateway.yml restart feedback-analyzer
```

## Configuration Files

### File Locations

```
.mcp/
├── README.md                     # General MCP documentation
├── SETUP.md                      # This file
├── configs/
│   ├── gordon-mcp.yml           # Docker AI configuration (copied to root)
│   ├── docker-compose.mcp-gateway.yml  # Gateway configuration (copied to root)
│   └── mcp-catalog.yaml         # Tool catalog (copied to root)
└── servers/
    └── feedback-analyzer/        # Custom MCP server
        ├── Dockerfile
        ├── requirements.txt
        ├── server.py
        └── README.md
```

### Why Files Are in Root

Docker AI and MCP Gateway expect configuration files in the project root. The source files are in `.mcp/configs/` but are copied to root for compatibility.

To update configurations:
1. Edit files in `.mcp/configs/`
2. Copy to root: `cp .mcp/configs/*.yml .` and `cp .mcp/configs/*.yaml .`

## Advanced Usage

### Custom Server Development

To modify the feedback analyzer:

1. Edit [.mcp/servers/feedback-analyzer/server.py](.mcp/servers/feedback-analyzer/server.py)
2. Rebuild: `docker-compose -f gordon-mcp.yml build feedback-analyzer`
3. Restart: `docker-compose -f gordon-mcp.yml restart feedback-analyzer`

### Adding New Tools

To add a new analysis tool:

1. Add tool definition in `list_tools()` function
2. Implement `your_tool_impl()` function
3. Add handler in `call_tool()` function
4. Update [mcp-catalog.yaml](../mcp-catalog.yaml)
5. Rebuild and restart server

### Environment Variables

MCP servers support these environment variables:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-key        # Required for custom analyzer
AI_MODEL=gpt-4o-mini              # Optional, defaults in code

# Logging
LOG_LEVEL=info                     # debug, info, warning, error

# Rate Limiting (if using project API)
MAX_RPS=5
ENABLE_BUDGET_ENFORCEMENT=true
```

## Security Notes

### Filesystem Access

- MCP filesystem server has **read-only** access
- Cannot modify or delete files
- Limited to project directory only

### Network Access

- Fetch server restricted to:
  - localhost (API testing)
  - api.openai.com (AI features)
- No arbitrary internet access

### API Keys

- Never commit `.env` file
- Use `.env.example` as template
- MCP Gateway can use Docker Desktop credential storage

## Maintenance

### Updating MCP Servers

```bash
# Update built-in servers
docker pull mcp/filesystem:latest
docker pull mcp/fetch:latest
docker pull mcp/time:latest

# Rebuild custom server
docker-compose -f gordon-mcp.yml build feedback-analyzer --no-cache

# Restart all
docker-compose -f docker-compose.mcp-gateway.yml restart
```

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose.mcp-gateway.yml logs -f

# Last 100 lines
docker-compose -f docker-compose.mcp-gateway.yml logs --tail=100

# Specific service
docker logs feedback-mcp-analyzer -f
```

### Stopping Services

```bash
# Stop Gateway (keeps data)
docker-compose -f docker-compose.mcp-gateway.yml stop

# Stop and remove (cleanup)
docker-compose -f docker-compose.mcp-gateway.yml down

# Remove with volumes
docker-compose -f docker-compose.mcp-gateway.yml down -v
```

## Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [Docker MCP Integration](https://docs.docker.com/ai/mcp-catalog-and-toolkit/)
- [Claude Desktop MCP Guide](https://docs.anthropic.com/claude/docs/model-context-protocol)
- [Custom MCP Server README](.mcp/servers/feedback-analyzer/README.md)
- [Main Documentation](../docs/README.md)

## Getting Help

If you encounter issues:

1. Check this guide's troubleshooting section
2. Review server logs
3. Verify environment variables
4. Check [.mcp/README.md](.mcp/README.md) for general MCP info
5. Review [.mcp/servers/feedback-analyzer/README.md](.mcp/servers/feedback-analyzer/README.md) for custom server details
