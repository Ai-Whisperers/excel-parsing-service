# Excel POI Parser - MCP Architecture

Visual guide to understand how MCP servers integrate with the two-layer Excel POI Parser architecture.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Clients                                │
│  • Docker AI (Gordon)                                            │
│  • Claude Desktop                                                │
│  • Cursor IDE                                                    │
│  • VSCode with Continue.dev                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ MCP Protocol
                         │ (stdio or SSE)
                         │
        ┌────────────────┴───────────────┐
        │                                │
        ▼                                ▼
┌───────────────┐              ┌──────────────────┐
│  gordon-mcp   │              │  MCP Gateway     │
│  (Docker AI)  │              │  (Port 8080)     │
└───────┬───────┘              └────────┬─────────┘
        │                               │
        │ Docker Compose                │ Docker Network
        │                               │ (mcp-network)
        └───────────┬───────────────────┘
                    │
        ┌───────────┴──────────────────────────────────┐
        │                                              │
        ▼                                              ▼
┌─────────────────┐                         ┌──────────────────────┐
│  Built-in MCP   │                         │  Custom MCP Server   │
│    Servers      │                         │  feedback-analyzer   │
│                 │                         │                      │
│ • filesystem    │                         │ Tools:               │
│ • fetch         │                         │ • analyze_sentiment  │
│ • time          │                         │ • calculate_nps      │
└────────┬────────┘                         │ • identify_themes    │
         │                                  │ • detect_pain_points │
         │ Read-only access                 │ • analyze_csv_file   │
         │                                  │ • generate_summary   │
         │                                  └──────────┬───────────┘
         │                                             │
         │                                             │ Calls
         │                                             │
         ▼                                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               Customer Feedback Analyzer Project                │
│                                                                  │
│  ├── data/              (CSV, Excel files)                      │
│  ├── api/               (Python analysis code)                  │
│  ├── docs/              (Documentation)                         │
│  └── .env               (OpenAI API key)                        │
│                                                                  │
│  External:                                                       │
│  └── OpenAI API         (gpt-4o-mini)                           │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow: Sentiment Analysis Example

```
User Query: "Analyze sentiment of feedback in data/samples/feedback.csv"
    │
    ├─► 1. AI Client → MCP Gateway (or Docker AI)
    │
    ├─► 2. Gateway routes to appropriate servers:
    │      ├─► filesystem server → reads CSV file
    │      └─► feedback-analyzer → analyzes text
    │
    ├─► 3. feedback-analyzer:
    │      ├─► Reads feedback text from CSV
    │      ├─► Calls OpenAI API (gpt-4o-mini)
    │      ├─► Processes AI response
    │      └─► Returns sentiment + confidence scores
    │
    └─► 4. Results returned to user through AI client
```

## MCP Server Communication

### Stdio Transport (Docker AI)

```
Docker AI
    ↓ stdin/stdout
    ↓
MCP Server (Container)
    ↓ Function calls
    ↓
Tool Implementations
```

### SSE Transport (MCP Gateway)

```
AI Client
    ↓ HTTP/SSE (Port 8080)
    ↓
MCP Gateway
    ↓ Docker network
    ↓
MCP Servers (Containers)
    ↓ Function calls
    ↓
Tool Implementations
```

## Security Boundaries

```
┌─────────────────────────────────────────────────────────┐
│                    Security Zones                       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Filesystem Server (Read-Only)                  │  │
│  │  • Can: Read project files                      │  │
│  │  • Cannot: Write, execute, delete               │  │
│  │  • Restricted: CSV, JSON, Excel, Parquet only   │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Fetch Server (Network Limited)                 │  │
│  │  • Can: HTTP requests to localhost              │  │
│  │  • Can: Requests to api.openai.com              │  │
│  │  • Cannot: Arbitrary internet access            │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Custom Analyzer (API Key Required)             │  │
│  │  • Uses: OpenAI API with user's key             │  │
│  │  • Source: Environment variable from .env       │  │
│  │  • Never: Stored in Docker images or logs       │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Configuration Flow

```
Source of Truth: .mcp/configs/
    │
    ├─► gordon-mcp.yml
    ├─► docker-compose.mcp-gateway.yml
    └─► mcp-catalog.yaml
    │
    ├─► Copied to project root (for Docker compatibility)
    │
    └─► Loaded by Docker AI or MCP Gateway
```

## Custom Server Architecture

```
┌────────────────────────────────────────────────────────┐
│         feedback-analyzer MCP Server                   │
│                                                        │
│  ┌──────────────────────────────────────────────┐    │
│  │  MCP Server Framework                        │    │
│  │  • list_tools() - Advertise capabilities    │    │
│  │  • call_tool() - Route requests              │    │
│  └─────────────────┬────────────────────────────┘    │
│                    │                                  │
│  ┌─────────────────┴────────────────────────────┐    │
│  │  Tool Implementations                        │    │
│  │                                              │    │
│  │  ├─ analyze_sentiment_impl()                │    │
│  │  ├─ calculate_nps_impl()                    │    │
│  │  ├─ identify_themes_impl()                  │    │
│  │  ├─ detect_pain_points_impl()               │    │
│  │  ├─ analyze_csv_file_impl()                 │    │
│  │  └─ generate_summary_impl()                 │    │
│  └─────────────────┬────────────────────────────┘    │
│                    │                                  │
│  ┌─────────────────┴────────────────────────────┐    │
│  │  External Dependencies                       │    │
│  │  • OpenAI AsyncClient (gpt-4o-mini)         │    │
│  │  • pandas (CSV processing)                   │    │
│  │  • Python standard library                   │    │
│  └──────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────┘
```

## Deployment Models

### Model 1: Docker AI (Development)

```
Developer Workflow:
    │
    ├─► 1. Edit code in IDE
    │
    ├─► 2. Ask Docker AI questions:
    │      "Analyze sentiment in feedback.csv"
    │      "Calculate NPS from recent data"
    │
    ├─► 3. Docker AI auto-starts MCP servers
    │      (from gordon-mcp.yml)
    │
    └─► 4. Get instant results in terminal
```

**Pros:**
- Zero configuration
- Auto-detects gordon-mcp.yml
- Perfect for quick queries
- No persistent services

**Cons:**
- Only works with Docker AI
- Servers restart each time
- No multi-client support

### Model 2: MCP Gateway (Production)

```
Team Workflow:
    │
    ├─► 1. Start MCP Gateway once:
    │      docker-compose -f docker-compose.mcp-gateway.yml up -d
    │
    ├─► 2. Multiple team members connect:
    │      • Claude Desktop
    │      • Cursor IDE
    │      • VSCode
    │
    ├─► 3. Persistent service runs 24/7
    │
    └─► 4. All clients share same tools
```

**Pros:**
- Multiple AI clients
- Persistent connections
- Production-ready
- Centralized logging

**Cons:**
- Manual startup required
- More resource intensive
- Requires configuration per client

## File Organization

```
Project Root
├── gordon-mcp.yml                  (Active - used by Docker AI)
├── docker-compose.mcp-gateway.yml  (Active - used by Gateway)
├── mcp-catalog.yaml                (Active - tool definitions)
│
└── .mcp/                           (Source directory)
    ├── README.md                   (Overview + examples)
    ├── SETUP.md                    (Installation guide)
    ├── QUICKSTART.md               (30-second setup)
    ├── ARCHITECTURE.md             (This file)
    │
    ├── configs/                    (Configuration sources)
    │   ├── gordon-mcp.yml
    │   ├── docker-compose.mcp-gateway.yml
    │   └── mcp-catalog.yaml
    │
    └── servers/                    (Custom implementations)
        └── feedback-analyzer/
            ├── Dockerfile
            ├── requirements.txt
            ├── server.py
            └── README.md
```

## Tool Capability Matrix

| Tool | Read Files | Write Files | HTTP Requests | AI Analysis | Database |
|------|------------|-------------|---------------|-------------|----------|
| **filesystem** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **fetch** | ❌ | ❌ | ✅ | ❌ | ❌ |
| **time** | ❌ | ❌ | ❌ | ❌ | ❌ |
| **feedback-analyzer** | ✅ | ❌ | ✅ (OpenAI) | ✅ | ❌ |

## Performance Characteristics

### Built-in Servers

- **Startup:** < 1 second
- **Memory:** ~20 MB each
- **Latency:** < 10 ms (local operations)

### Custom Analyzer

- **Startup:** ~3-5 seconds (Python + dependencies)
- **Memory:** ~100-200 MB
- **Latency:**
  - Local ops (NPS, CSV): < 100 ms
  - AI ops (sentiment, themes): 1-3 seconds (OpenAI API)

## Cost Considerations

### Free Resources

- Built-in MCP servers (filesystem, fetch, time)
- Docker compute for containers
- Local data processing

### Paid Resources

- OpenAI API calls from feedback-analyzer
- Approximately $0.0000375 per feedback analyzed
- Example: 1,000 feedbacks ≈ $0.04

## Extensibility

### Adding New Built-in Servers

```yaml
# In gordon-mcp.yml
services:
  postgres:
    image: mcp/postgres
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

### Adding Custom Tools

```python
# In .mcp/servers/feedback-analyzer/server.py
@app.call_tool()
async def your_new_tool_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    # Your implementation
    return {"result": "..."}
```

## Monitoring and Observability

### View Logs

```bash
# All services
docker-compose -f docker-compose.mcp-gateway.yml logs -f

# Specific server
docker logs feedback-mcp-analyzer -f

# Last 100 lines
docker logs --tail=100 feedback-mcp-analyzer
```

### Health Checks

```bash
# Check running containers
docker-compose -f docker-compose.mcp-gateway.yml ps

# Gateway health
curl http://localhost:8080/health

# View resource usage
docker stats feedback-mcp-analyzer
```

## Troubleshooting Decision Tree

```
Issue: MCP not working
    │
    ├─► Is Docker Desktop running?
    │   ├─ No → Start Docker Desktop
    │   └─ Yes → Continue
    │
    ├─► Using Docker AI or Gateway?
    │   ├─ Docker AI → Is gordon-mcp.yml in root?
    │   │             └─ No → Copy from .mcp/configs/
    │   └─ Gateway → Is gateway container running?
    │                └─ No → docker-compose up -d
    │
    ├─► Are containers built?
    │   └─ No → docker-compose build feedback-analyzer
    │
    ├─► Is OPENAI_API_KEY set in .env?
    │   └─ No → Add OPENAI_API_KEY=sk-... to .env
    │
    └─► Check logs for errors
        └─ docker logs feedback-mcp-analyzer
```

## Resources

- [MCP Protocol Spec](https://github.com/anthropics/mcp)
- [Docker MCP Docs](https://docs.docker.com/ai/mcp-catalog-and-toolkit/)
- [Setup Guide](SETUP.md)
- [Quick Start](QUICKSTART.md)

---

**Need Help?** Check [SETUP.md](SETUP.md) for detailed troubleshooting or open an issue.
