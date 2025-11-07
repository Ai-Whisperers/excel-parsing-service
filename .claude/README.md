# Claude Project Context - Excel POI Parser Service

Welcome! This file provides essential context for any Claude instance working on this project.

## Project Identity

**Name:** Excel POI Parser Service
**Type:** Hybrid REST + Arrow Flight microservice
**Purpose:** High-performance Excel file parsing with real-time streaming capabilities
**Architecture:** Two-plane (Control + Data)
**Performance:** 10-100x faster than traditional REST APIs for large datasets

## What This Project Does

This service parses Excel files (.xls/.xlsx) and streams the data using Apache Arrow Flight for maximum performance. It's designed to handle files from 1MB to 1GB+ without timeouts or memory issues.

**Key Innovation:** Separates control operations (REST) from data streaming (gRPC) to achieve massive performance gains while maintaining ease of use.

## Quick Architecture Overview

```
Client → REST API (8000) → Prepare Flight → Get ticket
       ↓
Client → gRPC (8815) → Stream Arrow batches → Process data
       ↓
Python Layer → Java Layer (8080) → Apache POI → Parse Excel
```

**Three Services:**
1. **Python Layer** (Port 8000 + 8815): FastAPI + Arrow Flight server
2. **Java Layer** (Port 8080): Apache POI Excel parsing
3. **Client**: Any application using REST or Arrow Flight

## Technology Stack

### Java Layer (Port 8080)
- **Language:** Java 17
- **Framework:** Spring Boot 3.2.x
- **Parser:** Apache POI 5.x
- **Build Tool:** Maven 3.8+
- **Key Library:** Apache POI for .xls/.xlsx parsing

### Python Layer (Port 8000 + 8815)
- **Language:** Python 3.11+
- **Web Framework:** FastAPI 0.109+
- **Data Plane:** Apache Arrow Flight (gRPC)
- **Data Processing:** PyArrow 15.x, Pandas 2.2
- **HTTP Client:** httpx, aiohttp
- **Server:** Uvicorn

### Orchestration
- **Monorepo:** pnpm workspace
- **Containers:** Docker + Docker Compose
- **CI/CD:** GitHub Actions (if configured)

## Project Structure

```
excel-poi-parser/
├── .claude/              # ← You are here (Claude context)
├── .mcp/                 # User-facing documentation
├── java-layer/           # Java parsing engine
│   ├── src/main/java/com/customeranalysis/excel/
│   │   ├── controller/   # REST endpoints
│   │   ├── service/      # Business logic
│   │   │   └── extractor/ # POI parsing services
│   │   ├── dto/          # Data transfer objects
│   │   └── model/        # Domain models
│   └── pom.xml           # Maven dependencies
│
└── python-layer/         # Python aggregation layer
    ├── app/
    │   ├── main.py              # FastAPI app entry
    │   ├── config.py            # Settings
    │   ├── models/schemas.py    # Pydantic models
    │   └── services/
    │       ├── java_client.py        # HTTP → Java
    │       ├── aggregator.py         # Data aggregation
    │       ├── arrow_formatter.py    # Arrow conversion
    │       ├── json_formatter.py     # JSON formatting
    │       ├── flight_server.py      # Arrow Flight server
    │       └── flight_rest_bridge.py # REST/Flight bridge
    └── requirements.txt         # Python deps
```

## Critical Files to Understand

### Python Layer
1. **`python-layer/app/main.py`** - FastAPI app + Flight server startup (dual-server architecture)
2. **`python-layer/app/services/flight_server.py`** - Arrow Flight server implementation (DATA PLANE)
3. **`python-layer/app/services/flight_rest_bridge.py`** - REST endpoints for Flight operations (CONTROL PLANE)
4. **`python-layer/app/config.py`** - Configuration (ports, URLs, settings)

### Java Layer
1. **`java-layer/src/main/java/.../ExcelParserApplication.java`** - Spring Boot entry point
2. **`java-layer/src/main/java/.../controller/ExcelParserController.java`** - REST API endpoints
3. **`java-layer/src/main/java/.../service/ExcelParserService.java`** - Main orchestrator
4. **`java-layer/src/main/java/.../service/extractor/*.java`** - POI parsing logic

### Configuration
1. **`docker-compose.yml`** - Multi-container setup
2. **`python-layer/.env.example`** - Environment variables template
3. **`java-layer/src/main/resources/application.yml`** - Spring Boot config
4. **`pnpm-workspace.yaml`** - Monorepo configuration

## Common Tasks

### Starting Services

```bash
# Docker (recommended)
docker-compose up --build

# Local development
pnpm dev                # Both layers
pnpm dev:java          # Java only
pnpm dev:python        # Python only
```

### Testing

```bash
# Health check
curl http://localhost:8000/health

# Flight availability
curl http://localhost:8000/api/v1/flight/list

# Process small file
curl -X POST http://localhost:8000/api/v1/process/excel \
  -F "file=@test.xlsx"
```

### Code Changes

**Python Layer:**
1. Edit `python-layer/app/**/*.py`
2. Server auto-reloads (FastAPI debug mode)
3. Test endpoint with curl

**Java Layer:**
1. Edit `java-layer/src/main/java/**/*.java`
2. Rebuild: `mvn clean install` or `pnpm build:java`
3. Restart: `pnpm dev:java`

**Docker:**
```bash
# Rebuild specific service
docker-compose build python-layer
docker-compose up -d python-layer
```

## Key Concepts to Remember

### Two-Plane Architecture

**Control Plane (REST - Port 8000):**
- Lightweight operations
- Authentication, sessions
- Flight preparation
- Metadata queries
- Small file processing

**Data Plane (gRPC - Port 8815):**
- High-throughput streaming
- Zero-copy Arrow transfer
- Batch processing
- Large file handling

### Data Flow

**Small Files (< 10 MB):**
```
Client → POST /api/v1/process/excel → JSON/Arrow response
```

**Large Files (> 10 MB):**
```
1. Client → POST /api/v1/flight/prepare → Get ticket
2. Client → gRPC DoGet(ticket) → Stream batches
3. Process batches incrementally
```

### Performance Characteristics

| File Size | Method | Time | Notes |
|-----------|--------|------|-------|
| < 10 MB   | REST   | < 2s | Simple, easy to use |
| 10-100 MB | Flight | 1-2s | Recommended |
| > 100 MB  | Flight | 2-15s | Only option that works |

### Important Ports

- **8000** - REST API (Control Plane)
- **8080** - Java Layer (Internal)
- **8815** - Arrow Flight (Data Plane)

## Dependencies Management

### Python Layer
```bash
cd python-layer

# Install
pip install -r requirements.txt

# Add new package
pip install <package>
pip freeze > requirements.txt
```

**Key Dependencies:**
- `fastapi` - Web framework
- `pyarrow` - Arrow data structures
- `grpcio` - gRPC for Flight
- `pandas` - Data manipulation
- `httpx` - Async HTTP client

### Java Layer
```bash
cd java-layer

# Install
mvn clean install

# Add new dependency (edit pom.xml)
# Then run: mvn clean install
```

**Key Dependencies:**
- `spring-boot-starter-web` - REST API
- `poi` + `poi-ooxml` - Excel parsing
- `lombok` - Boilerplate reduction
- `jackson` - JSON processing

## Environment Variables

### Python Layer (.env)
```bash
JAVA_LAYER_URL=http://localhost:8080    # Or http://java-layer:8080 in Docker
MAX_FILE_SIZE_MB=100
ARROW_COMPRESSION=zstd
API_HOST=0.0.0.0
API_PORT=8000
FLIGHT_HOST=0.0.0.0
FLIGHT_PORT=8815
```

### Java Layer (application.yml)
```yaml
server.port: 8080
parser.max-rows: 100000
parser.max-columns: 1000
```

## Error Handling Patterns

### Python Layer
```python
try:
    result = await some_operation()
except HTTPException as e:
    # Let FastAPI handle it
    raise
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
```

### Java Layer
```java
try {
    // Parse Excel
} catch (IOException e) {
    throw new ExcelParsingException("Failed to read file", e);
} catch (Exception e) {
    log.error("Unexpected error", e);
    throw new InternalServerException(e.getMessage());
}
```

## Testing Strategy

### Unit Tests
- **Python:** `pytest` in `python-layer/tests/`
- **Java:** JUnit in `java-layer/src/test/java/`

### Integration Tests
- Test REST → Java communication
- Test Flight streaming end-to-end
- Test with real Excel files

### Manual Testing
```bash
# Small file
curl -X POST http://localhost:8000/api/v1/process/excel \
  -F "file=@test.xlsx"

# Flight streaming
python examples/flight_client.py
```

## Common Issues & Solutions

### Issue: Port already in use
```bash
# Find process
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill or change port in .env
```

### Issue: Java layer not responding
```bash
# Check Java layer health
curl http://localhost:8080/api/v1/excel/health

# Check logs
docker logs excel-parser-java
```

### Issue: Flight connection refused
```bash
# Verify Flight server started
curl http://localhost:8000/api/v1/flight/list

# Check Python logs for "Arrow Flight server"
```

### Issue: Out of memory
```python
# Don't do this (loads all data)
table = reader.read_all()

# Do this (stream batches)
for batch in reader:
    df = batch.data.to_pandas()
    process(df)
    del df
```

## Code Style & Conventions

### Python
- **Formatter:** Black
- **Linter:** Ruff
- **Style:** PEP 8
- **Type Hints:** Encouraged
- **Docstrings:** Google style

### Java
- **Style:** Spring Boot conventions
- **Lombok:** Use for DTOs and entities
- **Naming:** camelCase for methods, PascalCase for classes

## Git Workflow

```bash
# Feature development
git checkout -b feature/description
# ... make changes ...
git add .
git commit -m "Description"
git push origin feature/description

# Always include in commit message:
🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

## Documentation Locations

- **User Docs:** `.mcp/` folder (README, QUICKSTART, API, etc.)
- **Claude Context:** `.claude/` folder (this file + others)
- **Code Docs:** Inline comments and docstrings
- **API Docs:** Auto-generated at `/docs` (FastAPI)

## Performance Optimization Tips

1. **Use Flight for files > 10 MB** - Don't use REST
2. **Stream batches incrementally** - Don't load entire dataset
3. **Configure batch size** - Default 10,000 rows, adjust as needed
4. **Use Arrow compression** - zstd is default, very efficient
5. **Monitor memory** - Large files can consume significant RAM

## Security Considerations

**Current State:** No authentication (development only)

**Production TODO:**
- Add JWT authentication on REST endpoints
- Implement Flight authentication headers
- Add rate limiting
- Enable HTTPS/TLS
- Implement RBAC

## Next Steps for New Claude Instances

1. **Read this file** - Get project context
2. **Check `.claude/architecture.md`** - Understand design
3. **Review `.claude/conventions.md`** - Follow patterns
4. **See `.claude/tasks.md`** - Common operations
5. **Start coding!**

## Useful Commands Reference

```bash
# Start everything
docker-compose up --build

# Health checks
curl http://localhost:8000/health
curl http://localhost:8080/api/v1/excel/health

# View logs
docker logs -f excel-parser-python
docker logs -f excel-parser-java

# Rebuild
pnpm build

# Clean
pnpm clean
docker-compose down -v

# Test
pnpm test
```

## Repository Info

- **GitHub:** https://github.com/Ai-Whisperers/excel-parsing-service
- **License:** MIT
- **Maintainers:** Ai-Whisperers team

## Questions?

Check these files in order:
1. `.claude/` - Claude-specific context (you're here)
2. `.mcp/QUICKSTART.md` - Getting started
3. `.mcp/API.md` - API reference
4. `.mcp/ARCHITECTURE.md` - Deep dive
5. Main `README.md` - Project overview
