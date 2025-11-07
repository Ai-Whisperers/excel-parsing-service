# Architecture Quick Reference

Quick architecture guide for Claude instances working on this codebase.

## System Architecture (Bird's Eye View)

```
┌──────────────────────────────────────────────────────────────┐
│                      CLIENT APPLICATION                       │
│            (Python, JavaScript, Java, curl, etc.)            │
└───────────────────┬─────────────────┬────────────────────────┘
                    │                 │
           CONTROL PLANE        DATA PLANE
           (Lightweight)        (Heavy Lifting)
                    │                 │
                    ▼                 ▼
        ┌──────────────────┐  ┌─────────────────────┐
        │  REST API        │  │  Arrow Flight       │
        │  Port: 8000      │  │  Port: 8815         │
        │  FastAPI         │  │  gRPC Streaming     │
        │                  │  │  Zero-Copy          │
        │  • /health       │  │  • DoGet (stream)   │
        │  • /prepare      │  │  • DoPut (upload)   │
        │  • /list         │  │  • ListFlights      │
        │  • /process      │  │  • GetFlightInfo    │
        └────────┬─────────┘  └──────────┬──────────┘
                 │                       │
                 └───────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Python Layer        │
                  │  • JavaLayerClient   │
                  │  • DataAggregator    │
                  │  • ArrowFormatter    │
                  │  • JSONFormatter     │
                  └──────────┬───────────┘
                             │
                             │ HTTP/JSON
                             ▼
                  ┌──────────────────────┐
                  │  Java Layer          │
                  │  Port: 8080          │
                  │  Spring Boot         │
                  │                      │
                  │  • Apache POI        │
                  │  • Cell Extraction   │
                  │  • Formula Eval      │
                  │  • Metadata Extract  │
                  └──────────────────────┘
```

## Component Layers

### Layer 1: Client Layer
**Who:** End users, applications, scripts
**What:** Consume parsed Excel data
**How:** REST API or Arrow Flight gRPC

### Layer 2: Python Aggregation Layer (Port 8000 + 8815)
**Location:** `python-layer/`
**Responsibilities:**
- Expose REST API (control plane)
- Run Arrow Flight server (data plane)
- Aggregate data from Java layer
- Format output (JSON or Arrow)
- Manage flight registry

**Key Components:**

```
python-layer/app/
├── main.py                    # Entry point - starts both servers
├── config.py                  # Settings (ports, URLs, etc.)
├── models/schemas.py          # Pydantic data models
└── services/
    ├── java_client.py         # HTTP client → Java layer
    ├── aggregator.py          # Transform Java response → tables
    ├── arrow_formatter.py     # Convert to Arrow format
    ├── json_formatter.py      # Convert to JSON format
    ├── flight_server.py       # Arrow Flight server (gRPC)
    └── flight_rest_bridge.py  # REST endpoints for Flight
```

### Layer 3: Java Parsing Layer (Port 8080)
**Location:** `java-layer/`
**Responsibilities:**
- Parse Excel files with Apache POI
- Extract cells, formulas, styles
- Handle .xls and .xlsx formats
- Return structured JSON

**Key Components:**

```
java-layer/src/main/java/com/customeranalysis/excel/
├── ExcelParserApplication.java      # Spring Boot main
├── controller/
│   └── ExcelParserController.java   # REST endpoints
├── service/
│   ├── ExcelParserService.java      # Orchestrator
│   └── extractor/
│       ├── WorkbookLoaderService.java    # Load Excel file
│       ├── SheetEnumeratorService.java   # Iterate sheets
│       ├── CellExtractorService.java     # Extract cells
│       ├── MetadataExtractorService.java # Extract metadata
│       ├── DataNormalizerService.java    # Normalize data
│       └── OutputFormatterService.java   # Format JSON
├── dto/       # Data transfer objects
└── model/     # Domain models
```

## Data Flow Patterns

### Pattern 1: Small File via REST (< 10 MB)

```
1. Client uploads Excel file
   POST /api/v1/process/excel
   Content-Type: multipart/form-data

2. Python Layer receives file
   → Calls Java Layer via HTTP

3. Java Layer parses with POI
   → Returns JSON with all cells

4. Python Layer aggregates
   → Converts to tabular format
   → Formats as JSON or Arrow

5. Client receives response
   JSON or Arrow IPC stream
```

**Files Involved:**
- `python-layer/app/main.py:87` - `/api/v1/process/excel` endpoint
- `python-layer/app/services/java_client.py` - `parse_excel()` method
- `java-layer/.../controller/ExcelParserController.java` - `parseExcel()` method
- `java-layer/.../service/ExcelParserService.java` - Main parsing logic

### Pattern 2: Large File via Flight (> 10 MB)

```
1. Client prepares flight
   POST /api/v1/flight/prepare
   params: file_path=/data/large.xlsx

2. Python Layer processes
   → Calls Java Layer
   → Aggregates data
   → Converts to Arrow table
   → Registers flight
   → Returns ticket

3. Client connects to gRPC
   FlightClient("grpc://localhost:8815")
   do_get(ticket)

4. Flight Server streams batches
   Batch 1: 10,000 rows
   Batch 2: 10,000 rows
   ...
   Batch N: remaining rows

5. Client processes incrementally
   for batch in reader:
       df = batch.data.to_pandas()
       process(df)
```

**Files Involved:**
- `python-layer/app/services/flight_rest_bridge.py:30` - `/api/v1/flight/prepare`
- `python-layer/app/services/flight_server.py:50` - `do_get()` method
- `python-layer/app/services/flight_server.py:25` - `register_flight()`
- Same Java layer files as Pattern 1

## Critical Code Sections

### 1. Dual Server Startup

**File:** `python-layer/app/main.py`

```python
# Lines 44-47: Initialize Flight server
flight_location = f"grpc://{settings.flight_host}:{settings.flight_port}"
flight_server = ExcelFlightServer(flight_location)
set_flight_server(flight_server)

# Lines 172-188: Start both servers
def start_flight_server_background():
    """Start Arrow Flight server in background thread"""
    logger.info(f"Starting Arrow Flight server on {flight_location}")
    flight_server.serve()

if __name__ == "__main__":
    # Start Flight server in background thread (data plane)
    flight_thread = threading.Thread(target=start_flight_server_background, daemon=True)
    flight_thread.start()

    # Start FastAPI server (control plane)
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
```

**Why This Matters:** Both servers run concurrently in one process. FastAPI handles REST, Flight handles streaming.

### 2. Flight Registration

**File:** `python-layer/app/services/flight_server.py`

```python
# Lines 25-35: Register flight
def register_flight(self, flight_id: str, table: pa.Table, metadata: dict = None):
    """Register Arrow table as flight"""
    self.flights[flight_id] = {
        'table': table,
        'schema': table.schema,
        'total_records': len(table),
        'metadata': metadata or {},
        'created_at': time.time()
    }
    logger.info(f"Registered flight: {flight_id} ({len(table)} records)")
```

**Why This Matters:** In-memory registry maps flight_id → Arrow table. This is what clients stream from.

### 3. Streaming Implementation

**File:** `python-layer/app/services/flight_server.py`

```python
# Lines 50-70: Stream data to client
def do_get(self, context, ticket: flight.Ticket):
    """Stream data (server → client) - Data plane"""
    # Parse ticket
    ticket_str = ticket.ticket.decode()
    parts = ticket_str.split(':', 2)
    flight_id = parts[1]

    # Get flight data
    flight_data = self.flights.get(flight_id)
    if not flight_data:
        raise KeyError(f"Flight not found: {flight_id}")

    # Stream table
    table = flight_data['table']
    return flight.RecordBatchStream(table)
```

**Why This Matters:** This is the core streaming logic. RecordBatchStream handles batching automatically.

### 4. Java → Python Communication

**File:** `python-layer/app/services/java_client.py`

```python
async def parse_excel(self, file: UploadFile, sheet_name: str = None, region: str = None):
    """Parse Excel file via Java layer"""
    url = f"{self.base_url}/api/v1/excel/parse"

    # Prepare multipart upload
    files = {'file': (file.filename, file.file, file.content_type)}
    data = {}
    if sheet_name:
        data['sheetName'] = sheet_name
    if region:
        data['region'] = region

    # Call Java layer
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(url, files=files, data=data)
        response.raise_for_status()
        return response.json()
```

**Why This Matters:** All Excel parsing happens in Java. Python just orchestrates and formats.

### 5. Apache POI Parsing

**File:** `java-layer/src/main/java/.../service/ExcelParserService.java`

```java
public ParseResponse parseExcel(MultipartFile file, String sheetName, String region) {
    // 1. Load workbook
    Workbook workbook = workbookLoader.loadWorkbook(file);

    // 2. Extract metadata
    Map<String, Object> metadata = metadataExtractor.extractMetadata(workbook);

    // 3. Extract sheets
    Map<String, SheetData> sheets = new HashMap<>();
    for (int i = 0; i < workbook.getNumberOfSheets(); i++) {
        Sheet sheet = workbook.getSheetAt(i);

        // Filter by sheet name if specified
        if (sheetName != null && !sheet.getSheetName().equals(sheetName)) {
            continue;
        }

        // Extract cells
        SheetData sheetData = cellExtractor.extractCells(sheet, region);
        sheets.put(sheet.getSheetName(), sheetData);
    }

    // 4. Return response
    return new ParseResponse(true, metadata, sheets, ...);
}
```

**Why This Matters:** This is where the actual Excel parsing happens using Apache POI.

## Communication Patterns

### REST Communication (Python ↔ Java)

```
Python Layer                    Java Layer
     |                              |
     |  POST /api/v1/excel/parse   |
     |  (Excel file)                |
     |----------------------------->|
     |                              | Parse with POI
     |                              | Extract cells
     |                              | Format JSON
     |                              |
     |  JSON Response               |
     |  (All cells + metadata)      |
     |<-----------------------------|
     |                              |
  Aggregate                         |
  Format Arrow/JSON                 |
```

### gRPC Communication (Client ↔ Python)

```
Client                         Flight Server
  |                                  |
  | POST /api/v1/flight/prepare     |
  |---------------------------------→| (REST)
  |                                  | Process Excel
  |                                  | Register flight
  |  {flight_id, ticket}             |
  |←---------------------------------|
  |                                  |
  | FlightClient.do_get(ticket)     |
  |---------------------------------→| (gRPC)
  |                                  |
  | Stream<RecordBatch>              |
  |←---------------------------------| Batch 1
  |←---------------------------------| Batch 2
  |←---------------------------------| Batch 3
  |                                  | ...
```

## Configuration Flow

```
Environment Variables (.env)
          ↓
python-layer/app/config.py (Settings class)
          ↓
python-layer/app/main.py (reads settings)
          ↓
Services use settings.* to access config
```

**Key Settings:**

```python
# python-layer/app/config.py
class Settings(BaseSettings):
    # Java layer
    java_layer_url: str = "http://localhost:8080"

    # Control plane
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Data plane
    flight_host: str = "0.0.0.0"
    flight_port: int = 8815

    # Processing
    max_file_size_mb: int = 100
    arrow_compression: str = "zstd"
```

## Service Dependencies

```
Python Layer depends on:
  ├─ Java Layer (HTTP) - MUST be running
  ├─ PyArrow - For Arrow tables
  ├─ gRPC - For Flight server
  └─ FastAPI - For REST API

Java Layer depends on:
  ├─ Apache POI - For Excel parsing
  ├─ Spring Boot - For REST framework
  └─ Nothing else (standalone)

Client depends on:
  ├─ Python Layer REST API
  └─ Python Layer Flight gRPC (optional, for large files)
```

## Performance Architecture

### Why It's Fast

1. **Zero-Copy Streaming**
   - Arrow IPC format is memory-mapped
   - No serialization/deserialization
   - Data goes directly from memory → network

2. **Columnar Format**
   - Arrow stores data column-wise
   - Highly compressible
   - Efficient for analytics

3. **Batch Processing**
   - Stream in 10,000-row batches
   - Client processes incrementally
   - No memory overflow

4. **gRPC Multiplexing**
   - HTTP/2 protocol
   - Parallel streams
   - Lower latency than HTTP/1.1

### Performance Bottlenecks

1. **Java Parsing** - POI is CPU-intensive
2. **Network** - Large files = more transfer time
3. **Memory** - Large Arrow tables consume RAM

### Optimization Strategies

1. **Increase batch size** for faster throughput (use more memory)
2. **Decrease batch size** for lower memory usage (slower throughput)
3. **Use compression** (zstd default, lz4 for speed)
4. **Parallel processing** (multiple workers)

## Error Propagation

```
Java Layer Exception
        ↓
HTTP 500 to Python Layer
        ↓
Python catches, logs, wraps
        ↓
HTTPException(status_code=500)
        ↓
FastAPI returns JSON error
        ↓
Client receives error response
```

## Thread Safety

### Python Layer
- **FastAPI:** Thread-safe (async/await)
- **Flight Server:** Runs in daemon thread, shares memory with FastAPI
- **flights dict:** Not thread-safe! Use locks if concurrent writes

### Java Layer
- **Spring Boot:** Thread-safe (request-scoped beans)
- **POI:** NOT thread-safe! Create new Workbook per request

## Scaling Considerations

### Horizontal Scaling

**Can scale:**
- Python REST API (stateless)
- Java parsing layer (stateless)

**Cannot scale easily:**
- Flight server (in-memory flight registry)

**Solution for Flight:**
- Use shared cache (Redis)
- Store flight metadata externally
- Reference Arrow files on disk/S3

### Vertical Scaling

**Memory:**
- Java heap: `-Xmx4g` (adjust as needed)
- Python: No specific limits

**CPU:**
- POI parsing is CPU-bound
- More cores = more concurrent requests

## Monitoring Points

### Health Checks
- `GET /health` - Python + Java health
- `GET /api/v1/flight/list` - Flight server alive
- `GET /api/v1/excel/health` - Java layer alive

### Metrics to Track
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (%)
- Active flights (count)
- Memory usage (MB)
- CPU usage (%)

### Logs to Watch
- Python: FastAPI startup, Flight server startup
- Java: Spring Boot startup, POI parsing errors
- Both: Exceptions and stack traces

## When to Edit What

**Add new REST endpoint:**
- Edit `python-layer/app/main.py` or create new router

**Add new Flight operation:**
- Edit `python-layer/app/services/flight_server.py`
- Override Flight methods (DoPut, DoAction, etc.)

**Change Java parsing logic:**
- Edit `java-layer/.../service/extractor/*.java`
- Don't modify controller unless changing API

**Add new dependency:**
- Python: Add to `requirements.txt`
- Java: Add to `pom.xml`

**Change configuration:**
- Edit `.env` (Python) or `application.yml` (Java)
- Update `python-layer/app/config.py` if adding new setting

## Security Model (Current)

**Authentication:** None (development only)
**Authorization:** None
**Encryption:** None (plain HTTP/gRPC)

**Production Requirements:**
- Add JWT authentication
- Enable HTTPS/TLS
- Implement rate limiting
- Add request validation
- Use secrets management

## Key Takeaways for Claude

1. **Two servers in one process** - FastAPI + Flight run concurrently
2. **Java does the parsing** - Python just orchestrates
3. **In-memory flight registry** - Not persistent
4. **Zero-copy is the magic** - Arrow IPC makes it fast
5. **Batch streaming** - 10,000 rows at a time (configurable)
6. **Thread safety matters** - Especially flight registry
7. **No auth yet** - Development only
8. **Ports matter** - 8000 (REST), 8080 (Java), 8815 (Flight)

## Quick Architecture Reference

| Component | Language | Port | Purpose | Key Files |
|-----------|----------|------|---------|-----------|
| REST API | Python | 8000 | Control plane | `main.py`, `flight_rest_bridge.py` |
| Flight Server | Python | 8815 | Data plane | `flight_server.py` |
| Java Parser | Java | 8080 | Excel parsing | `ExcelParserService.java` |
| Client | Any | - | Consume data | User code |
