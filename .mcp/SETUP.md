# Development Setup Guide

Complete guide for setting up the Excel POI Parser Service development environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Java Layer Setup](#java-layer-setup)
4. [Python Layer Setup](#python-layer-setup)
5. [Docker Setup](#docker-setup)
6. [IDE Configuration](#ide-configuration)
7. [Testing Setup](#testing-setup)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

| Software | Version | Purpose |
| -------- | ------- | ------- |
| **Node.js** | >= 18.x | pnpm runtime & monorepo scripts |
| **pnpm** | >= 8.x | Monorepo package manager |
| **Java** | 17 (LTS) | Java layer runtime |
| **Maven** | >= 3.8.x | Java dependency management |
| **Python** | >= 3.11 | Python layer runtime |
| **pip** | Latest | Python package manager |
| **Docker** | >= 24.x | Container runtime (optional) |
| **Docker Compose** | >= 2.x | Multi-container orchestration (optional) |

### Installation

#### Windows

```powershell
# Install Node.js (via winget or download from nodejs.org)
winget install OpenJS.NodeJS.LTS

# Install pnpm
npm install -g pnpm

# Install Java 17 (via winget or download from adoptium.net)
winget install EclipseAdoptium.Temurin.17.JDK

# Install Maven
winget install Apache.Maven

# Install Python 3.11
winget install Python.Python.3.11

# Install Docker Desktop
winget install Docker.DockerDesktop
```

#### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Node.js
brew install node@18

# Install pnpm
npm install -g pnpm

# Install Java 17
brew install openjdk@17

# Install Maven
brew install maven

# Install Python 3.11
brew install python@3.11

# Install Docker Desktop
brew install --cask docker
```

#### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install pnpm
npm install -g pnpm

# Install Java 17
sudo apt install -y openjdk-17-jdk

# Install Maven
sudo apt install -y maven

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose-plugin
```

### Verify Installations

```bash
# Node.js
node --version  # Should output v18.x.x or higher

# pnpm
pnpm --version  # Should output 8.x.x or higher

# Java
java -version   # Should output openjdk version "17.x.x"

# Maven
mvn --version   # Should output Apache Maven 3.8.x or higher

# Python
python3 --version  # Should output Python 3.11.x or higher

# Docker
docker --version  # Should output Docker version 24.x.x or higher

# Docker Compose
docker compose version  # Should output Docker Compose version v2.x.x or higher
```

## Environment Setup

### Clone Repository

```bash
git clone https://github.com/Ai-Whisperers/excel-parsing-service.git
cd excel-parsing-service
```

### Project Structure

```
excel-poi-parser/
├── .mcp/                         # Documentation
├── package.json                  # Root pnpm scripts
├── pnpm-workspace.yaml           # pnpm workspace config
├── docker-compose.yml            # Multi-container setup
│
├── java-layer/                   # Java parsing layer
│   ├── package.json              # pnpm scripts for Maven
│   ├── pom.xml                   # Maven dependencies
│   ├── Dockerfile
│   └── src/main/
│       ├── java/                 # Java source code
│       └── resources/            # Configuration files
│
└── python-layer/                 # Python aggregation layer
    ├── package.json              # pnpm scripts for Python
    ├── requirements.txt          # Python dependencies
    ├── Dockerfile
    ├── .env.example              # Example environment variables
    └── app/
        ├── main.py               # FastAPI app
        ├── config.py             # Configuration
        ├── models/               # Pydantic models
        └── services/             # Business logic
```

## Java Layer Setup

### Step 1: Navigate to Java Layer

```bash
cd java-layer
```

### Step 2: Install Dependencies

```bash
# Using Maven directly
mvn clean install

# OR using pnpm (from root)
cd ..
pnpm install:java
```

### Step 3: Configure Application

Edit `src/main/resources/application.yml`:

```yaml
server:
  port: 8080

parser:
  max-rows: 100000
  max-columns: 1000
  enable-formula-evaluation: true
  temp-directory: ${java.io.tmpdir}/excel-parser

logging:
  level:
    com.customeranalysis: DEBUG
    org.apache.poi: INFO
```

### Step 4: Run Java Layer

```bash
# Using Maven
mvn spring-boot:run

# OR using pnpm (from root)
pnpm dev:java
```

**Expected output:**
```
  .   ____          _            __ _ _
 /\\ / ___'_ __ _ _(_)_ __  __ _ \ \ \ \
( ( )\___ | '_ | '_| | '_ \/ _` | \ \ \ \
 \\/  ___)| |_)| | | | | || (_| |  ) ) ) )
  '  |____| .__|_| |_|_| |_\__, | / / / /
 =========|_|==============|___/=/_/_/_/
 :: Spring Boot ::                (v3.2.0)

INFO  Starting ExcelParserApplication...
INFO  Started ExcelParserApplication in 3.456 seconds
```

### Step 5: Verify Java Layer

```bash
curl http://localhost:8080/api/v1/excel/health
```

**Expected:** `"Java Layer: Excel Parser Service is running"`

## Python Layer Setup

### Step 1: Navigate to Python Layer

```bash
cd python-layer
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
.\venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# OR using pnpm (from root)
cd ..
pnpm install:python
```

**Dependencies installed:**
- fastapi - REST API framework
- uvicorn - ASGI server
- pyarrow - Arrow data structures
- grpcio - gRPC for Arrow Flight
- pandas - Data manipulation
- httpx/aiohttp - HTTP clients
- pydantic - Data validation

### Step 4: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env (optional - defaults are fine for development)
nano .env
```

**.env configuration:**
```bash
# Java Layer
JAVA_LAYER_URL=http://localhost:8080

# File Processing
MAX_FILE_SIZE_MB=100

# Arrow Configuration
ARROW_COMPRESSION=zstd

# Control Plane (REST API)
API_HOST=0.0.0.0
API_PORT=8000

# Data Plane (Arrow Flight gRPC)
FLIGHT_HOST=0.0.0.0
FLIGHT_PORT=8815
```

### Step 5: Run Python Layer

**Make sure Java layer is running first!**

```bash
# Using Python directly
python -m app.main

# OR using pnpm (from root)
cd ..
pnpm dev:python
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Starting Arrow Flight server on grpc://0.0.0.0:8815
INFO:     Arrow Flight server thread started
```

### Step 6: Verify Python Layer

```bash
# Health check
curl http://localhost:8000/health

# Flight availability
curl http://localhost:8000/api/v1/flight/list
```

## Docker Setup

### Step 1: Build Images

```bash
# Build both services
docker-compose build

# OR using pnpm
pnpm docker:build
```

### Step 2: Start Services

```bash
# Start in foreground (see logs)
docker-compose up

# Start in background (detached)
docker-compose up -d

# OR using pnpm
pnpm docker:up
```

### Step 3: View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker logs -f excel-parser-python
docker logs -f excel-parser-java
```

### Step 4: Stop Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# OR using pnpm
pnpm docker:down
```

## IDE Configuration

### Visual Studio Code

**Recommended Extensions:**
- Python (ms-python.python)
- Java Extension Pack (vscjava.vscode-java-pack)
- Docker (ms-azuretools.vscode-docker)
- REST Client (humao.rest-client)

**Workspace Settings (.vscode/settings.json):**
```json
{
  "python.defaultInterpreterPath": "./python-layer/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "java.configuration.runtimes": [
    {
      "name": "JavaSE-17",
      "path": "/path/to/jdk-17"
    }
  ],
  "files.exclude": {
    "**/target": true,
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### IntelliJ IDEA

**Project Setup:**
1. Open as Maven project
2. Set Project SDK to Java 17
3. Enable Spring Boot support
4. Configure Python plugin for python-layer

**Run Configurations:**

**Java Layer:**
- Main class: `com.customeranalysis.excel.ExcelParserApplication`
- VM options: `-Xmx2g`
- Working directory: `java-layer`

**Python Layer:**
- Script path: `python-layer/app/main.py`
- Python interpreter: `python-layer/venv/bin/python`
- Working directory: `python-layer`

## Testing Setup

### Java Layer Tests

```bash
cd java-layer

# Run all tests
mvn test

# Run specific test
mvn test -Dtest=ExcelParserServiceTest

# Generate coverage report
mvn test jacoco:report
```

### Python Layer Tests

```bash
cd python-layer

# Activate venv
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_flight_server.py -v
```

### Integration Tests

```bash
# From root directory
pnpm test

# Individual layers
pnpm test:java
pnpm test:python
```

## Development Workflow

### Local Development (Both Layers)

```bash
# Terminal 1: Start Java layer
pnpm dev:java

# Terminal 2: Start Python layer
pnpm dev:python

# Terminal 3: Test endpoints
curl http://localhost:8000/health
```

### Docker Development

```bash
# Build and start
docker-compose up --build

# Rebuild specific service
docker-compose build python-layer
docker-compose up -d python-layer

# View logs
docker-compose logs -f python-layer
```

### Code Quality

```bash
# Python formatting
cd python-layer
black app/
ruff check app/

# Python type checking
mypy app/

# Java formatting (if configured)
cd java-layer
mvn spotless:apply
```

## Troubleshooting

### Issue: Port already in use

```bash
# Find process using port
# Linux/macOS
lsof -i :8000
lsof -i :8080
lsof -i :8815

# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :8080
netstat -ano | findstr :8815

# Kill process
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows
```

### Issue: Java layer not starting

```bash
# Check Java version
java -version  # Must be 17

# Clean Maven cache
cd java-layer
mvn clean
rm -rf ~/.m2/repository  # Nuclear option

# Rebuild
mvn clean install -U
```

### Issue: Python dependencies failing

```bash
# Upgrade pip
pip install --upgrade pip

# Clear pip cache
pip cache purge

# Reinstall dependencies
pip install -r requirements.txt --no-cache-dir

# If still failing, check Python version
python3 --version  # Must be 3.11+
```

### Issue: Docker build failing

```bash
# Clear Docker cache
docker system prune -a

# Rebuild with no cache
docker-compose build --no-cache

# Check disk space
docker system df
```

### Issue: Arrow Flight connection refused

```bash
# Check if Flight server started
docker logs excel-parser-python | grep "Flight"

# Verify port binding
docker ps  # Check port mapping

# Test Flight availability
curl http://localhost:8000/api/v1/flight/list
```

## Performance Tuning

### Java Layer

**application.yml:**
```yaml
server:
  tomcat:
    threads:
      max: 200
      min-spare: 10
    max-connections: 10000
```

**JVM Options:**
```bash
-Xmx4g              # Max heap 4GB
-Xms2g              # Initial heap 2GB
-XX:+UseG1GC        # Use G1 garbage collector
```

### Python Layer

**Uvicorn workers:**
```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop
```

**Flight server batch size:**
```python
# app/config.py
class Settings(BaseSettings):
    flight_batch_size: int = 10000  # Increase for more throughput
```

## Next Steps

1. **[QUICKSTART.md](QUICKSTART.md)** - Try your first requests
2. **[API.md](API.md)** - Explore API endpoints
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Understand the architecture
4. **Main README.md** - Full project documentation

## Useful Commands Reference

### pnpm Commands (from root)

```bash
pnpm install:all      # Install all dependencies
pnpm dev              # Start both layers
pnpm dev:java         # Start Java layer only
pnpm dev:python       # Start Python layer only
pnpm test             # Run all tests
pnpm test:java        # Run Java tests
pnpm test:python      # Run Python tests
pnpm build            # Build both layers
pnpm clean            # Clean build artifacts
pnpm docker:build     # Build Docker images
pnpm docker:up        # Start Docker containers
pnpm docker:down      # Stop Docker containers
```

### Docker Commands

```bash
docker-compose up --build       # Build and start
docker-compose up -d            # Start in background
docker-compose down             # Stop services
docker-compose logs -f          # Follow logs
docker-compose ps               # List containers
docker-compose restart          # Restart services
docker-compose exec python-layer bash  # Shell into container
```

### Health Check Commands

```bash
# Python layer
curl http://localhost:8000/health

# Java layer
curl http://localhost:8080/api/v1/excel/health

# Flight server
curl http://localhost:8000/api/v1/flight/list
```
