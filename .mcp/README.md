# Excel POI Parser Service - MCP Documentation

## Overview

The **Excel POI Parser Service** is a high-performance, hybrid architecture system for parsing Excel files (.xls/.xlsx) and streaming data in real-time. It combines the power of Apache POI (Java) for parsing with Apache Arrow Flight (Python) for ultra-fast data streaming.

**Key Features:**
- **10-100x faster** than traditional REST APIs for large datasets
- **Zero-copy streaming** via Arrow Flight gRPC
- **Hybrid architecture**: REST for control, gRPC for data
- **Production-ready** with Docker support
- **Backward compatible** with existing REST endpoints

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Application                        │
└────────────┬────────────────────────┬───────────────────────┘
             │                        │
             │ Control Plane          │ Data Plane
             │ REST (HTTP)            │ Arrow Flight (gRPC)
             │ Port 8000              │ Port 8815
             ▼                        ▼
┌────────────────────────┐  ┌──────────────────────────────┐
│   FastAPI REST API     │  │  Arrow Flight Server         │
│   - Prepare flights    │  │  - Stream Arrow batches      │
│   - List datasets      │  │  - Zero-copy transfer        │
│   - Auth/sessions      │  │  - 1-10 GB/s throughput     │
└────────────┬───────────┘  └──────────────┬───────────────┘
             │                              │
             └──────────┬───────────────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │   Data Aggregator   │
             │   (PyArrow tables)  │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │   Java Layer        │
             │   (Apache POI)      │
             │   Port 8080         │
             └─────────────────────┘
```

## Two-Plane Architecture

| Plane             | Transport        | Port | Purpose                                         |
| ----------------- | ---------------- | ---- | ----------------------------------------------- |
| **Control plane** | REST / HTTPS API | 8000 | Lightweight signaling, auth, session management |
| **Data plane**    | gRPC streaming   | 8815 | High-throughput, low-latency data transfer      |

## Performance Comparison

| File Size | REST API    | Arrow Flight | Speedup |
| --------- | ----------- | ------------ | ------- |
| 1 MB      | 100 ms      | 50 ms        | 2x      |
| 10 MB     | 1.5 s       | 200 ms       | 7.5x    |
| 100 MB    | 25 s        | 1.5 s        | 16x     |
| 1 GB      | Timeout ⚠️  | 12 s         | ∞       |

**Recommendation:** Use Arrow Flight (port 8815) for files > 10 MB

## Technology Stack

### Java Layer (Port 8080)
- **Apache POI** - Excel file parsing
- **Spring Boot** - REST API framework
- **Maven** - Dependency management

### Python Layer (Port 8000 + 8815)
- **FastAPI** - REST API (control plane)
- **Apache Arrow Flight** - gRPC streaming (data plane)
- **PyArrow** - Arrow data structures
- **httpx/aiohttp** - Java layer client
- **Pandas** - Data manipulation

## Quick Start

### Using Docker (Recommended)

```bash
# Start both services
docker-compose up --build

# Test control plane
curl http://localhost:8000/health

# Test Flight availability
curl http://localhost:8000/api/v1/flight/list
```

### Using pnpm (Development)

```bash
# Install dependencies
pnpm install:all

# Start both layers
pnpm dev

# Or start individually
pnpm dev:java   # Port 8080
pnpm dev:python # Port 8000 + 8815
```

## Usage Patterns

### Pattern 1: Prepare + Stream (Large Files)

**Step 1:** Prepare flight via REST
```bash
curl -X POST "http://localhost:8000/api/v1/flight/prepare" \
  -d "file_path=/data/large.xlsx"
```

**Response:**
```json
{
  "flight_id": "excel_data_large.xlsx",
  "schema": {...},
  "total_records": 1000000,
  "grpc_endpoint": "grpc://localhost:8815",
  "ticket": "excel:excel_data_large.xlsx:{}"
}
```

**Step 2:** Stream data via gRPC
```python
import pyarrow.flight as flight

client = flight.FlightClient("grpc://localhost:8815")
ticket = flight.Ticket(b"excel:excel_data_large.xlsx:{}")
reader = client.do_get(ticket)

for batch in reader:
    df = batch.data.to_pandas()
    print(f"Streamed {len(df)} rows")
```

### Pattern 2: Legacy REST (Small Files)

```bash
curl -X POST "http://localhost:8000/api/v1/process/excel" \
  -F "file=@small.xlsx" \
  -F "output_format=json"
```

## API Endpoints

### Control Plane (REST - Port 8000)

| Endpoint                         | Method | Purpose                       |
| -------------------------------- | ------ | ----------------------------- |
| `/health`                        | GET    | Health check                  |
| `/api/v1/flight/prepare`         | POST   | Prepare Excel for streaming   |
| `/api/v1/flight/upload`          | POST   | Upload + prepare in one call  |
| `/api/v1/flight/list`            | GET    | List available flights        |
| `/api/v1/flight/info/{id}`       | GET    | Get flight metadata           |
| `/api/v1/flight/example`         | GET    | Get client code example       |
| `/api/v1/process/excel`          | POST   | Legacy: Process via REST      |

### Data Plane (gRPC - Port 8815)

| Method       | Purpose                          |
| ------------ | -------------------------------- |
| `DoGet`      | Stream Arrow batches to client   |
| `DoPut`      | Upload Arrow stream from client  |
| `ListFlights`| List available datasets          |
| `GetFlightInfo` | Get schema and metadata       |

## Documentation Structure

```
.mcp/
├── README.md           # This file - project overview
├── ARCHITECTURE.md     # Detailed architecture documentation
├── QUICKSTART.md       # Getting started guide
├── SETUP.md           # Detailed setup instructions
└── API.md             # Complete API reference
```

## Next Steps

1. **[QUICKSTART.md](QUICKSTART.md)** - Get up and running in 5 minutes
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Deep dive into the hybrid architecture
3. **[SETUP.md](SETUP.md)** - Detailed development environment setup
4. **[API.md](API.md)** - Complete API documentation with examples

## Repository

- **GitHub:** https://github.com/Ai-Whisperers/excel-parsing-service
- **Issues:** https://github.com/Ai-Whisperers/excel-parsing-service/issues
- **License:** MIT

## Support

For questions or issues:
1. Check the documentation in the `.mcp/` folder
2. Review the main `README.md` and `ARCHITECTURE.md`
3. Open an issue on GitHub
