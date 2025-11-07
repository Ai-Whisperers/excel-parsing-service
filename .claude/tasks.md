# Common Tasks Guide

Step-by-step guides for common development tasks. Use these as templates when working on this project.

## Table of Contents

1. [Adding a New REST Endpoint](#adding-a-new-rest-endpoint)
2. [Adding a New Flight Operation](#adding-a-new-flight-operation)
3. [Modifying Java Parsing Logic](#modifying-java-parsing-logic)
4. [Adding a New Dependency](#adding-a-new-dependency)
5. [Debugging Issues](#debugging-issues)
6. [Running Tests](#running-tests)
7. [Building and Deploying](#building-and-deploying)
8. [Performance Optimization](#performance-optimization)

---

## Adding a New REST Endpoint

### Task: Add a new endpoint to the Python REST API

**Files to modify:**
- `python-layer/app/main.py` OR create new router file
- `python-layer/app/models/schemas.py` (if new models needed)

**Steps:**

1. **Define Pydantic model (if needed)**

```python
# python-layer/app/models/schemas.py

class NewFeatureRequest(BaseModel):
    file_path: str
    option1: str
    option2: Optional[int] = None

class NewFeatureResponse(BaseModel):
    success: bool
    result: Dict[str, Any]
    timestamp: int
```

2. **Add endpoint to main.py**

```python
# python-layer/app/main.py

@app.post("/api/v1/new-feature", response_model=NewFeatureResponse)
async def new_feature_endpoint(
    request: NewFeatureRequest
):
    """
    Description of what this endpoint does.

    Args:
        request: Request parameters

    Returns:
        NewFeatureResponse with results
    """
    try:
        # 1. Validate input
        if not request.file_path:
            raise HTTPException(status_code=400, detail="file_path required")

        # 2. Process request
        result = await process_new_feature(request)

        # 3. Return response
        return NewFeatureResponse(
            success=True,
            result=result,
            timestamp=int(time.time())
        )

    except Exception as e:
        logger.error(f"Error in new feature: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

3. **Test endpoint**

```bash
curl -X POST "http://localhost:8000/api/v1/new-feature" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/data/test.xlsx", "option1": "value"}'
```

4. **Add tests**

```python
# python-layer/tests/test_new_feature.py

def test_new_feature_success():
    response = client.post(
        "/api/v1/new-feature",
        json={"file_path": "/data/test.xlsx", "option1": "value"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
```

---

## Adding a New Flight Operation

### Task: Add a new Arrow Flight method (e.g., DoPut, DoAction)

**Files to modify:**
- `python-layer/app/services/flight_server.py`
- `python-layer/app/services/flight_rest_bridge.py` (if REST endpoint needed)

**Steps:**

1. **Implement Flight method**

```python
# python-layer/app/services/flight_server.py

class ExcelFlightServer(flight.FlightServerBase):
    # ... existing code ...

    def do_put(self, context, descriptor, reader, writer):
        """
        Upload data from client to server.

        Args:
            context: Flight call context
            descriptor: Flight descriptor
            reader: FlightStreamReader
            writer: FlightMetadataWriter
        """
        try:
            # Read incoming data
            table = reader.read_all()

            # Store flight
            flight_id = descriptor.path[0].decode()
            self.register_flight(flight_id, table)

            # Write metadata back to client
            metadata = {
                'status': 'success',
                'records': len(table)
            }
            writer.write(json.dumps(metadata).encode())

            logger.info(f"Stored flight: {flight_id} ({len(table)} records)")

        except Exception as e:
            logger.error(f"DoPut failed: {str(e)}", exc_info=True)
            raise flight.FlightError(str(e))
```

2. **Add REST endpoint (if needed)**

```python
# python-layer/app/services/flight_rest_bridge.py

@router.post("/api/v1/flight/upload-table")
async def upload_table(
    flight_id: str = Query(...),
    data: Dict[str, List[Any]] = Body(...)
):
    """Upload Arrow table via REST + Flight."""
    try:
        # Convert dict to Arrow table
        table = pa.table(data)

        # Register with Flight server
        _flight_server.register_flight(flight_id, table)

        return {
            "success": True,
            "flight_id": flight_id,
            "records": len(table)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

3. **Test Flight operation**

```python
# Client code
import pyarrow.flight as flight
import pyarrow as pa

# Create data
data = {'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']}
table = pa.table(data)

# Upload via DoPut
client = flight.FlightClient("grpc://localhost:8815")
descriptor = flight.FlightDescriptor.for_path("my_data")

writer, metadata_reader = client.do_put(descriptor, table.schema)
writer.write_table(table)
writer.close()

# Read metadata
metadata = metadata_reader.read()
print(metadata)
```

---

## Modifying Java Parsing Logic

### Task: Change how Excel cells are extracted or processed

**Files to modify:**
- `java-layer/src/main/java/.../service/extractor/CellExtractorService.java`
- Or relevant extractor service

**Steps:**

1. **Locate the extractor service**

```bash
cd java-layer/src/main/java/com/customeranalysis/excel/service/extractor/
ls
# CellExtractorService.java - Cell extraction
# MetadataExtractorService.java - Metadata
# DataNormalizerService.java - Data normalization
```

2. **Modify extraction logic**

```java
// CellExtractorService.java

@Service
@Slf4j
public class CellExtractorService {

    public SheetData extractCells(Sheet sheet, String region) {
        List<List<Object>> data = new ArrayList<>();

        // NEW: Add custom logic
        int startRow = 0;
        int endRow = sheet.getLastRowNum();

        if (region != null) {
            // Parse region (e.g., "A1:D10")
            int[] bounds = parseRegion(region);
            startRow = bounds[0];
            endRow = bounds[1];
        }

        for (int rowNum = startRow; rowNum <= endRow; rowNum++) {
            Row row = sheet.getRow(rowNum);
            if (row == null) continue;

            List<Object> rowData = extractRow(row);
            data.add(rowData);
        }

        return new SheetData(data, ...);
    }

    private List<Object> extractRow(Row row) {
        List<Object> rowData = new ArrayList<>();

        for (Cell cell : row) {
            // NEW: Add custom cell processing
            Object value = getCellValue(cell);

            // Example: Convert all strings to uppercase
            if (value instanceof String) {
                value = ((String) value).toUpperCase();
            }

            rowData.add(value);
        }

        return rowData;
    }
}
```

3. **Rebuild and test**

```bash
cd java-layer
mvn clean install
mvn spring-boot:run

# In another terminal
curl -X POST "http://localhost:8080/api/v1/excel/parse" \
  -F "file=@test.xlsx"
```

4. **Add unit tests**

```java
// CellExtractorServiceTest.java

@Test
void shouldExtractCellsWithCustomLogic() {
    // Given
    Sheet sheet = createTestSheet();

    // When
    SheetData result = cellExtractor.extractCells(sheet, null);

    // Then
    assertThat(result.getData()).isNotEmpty();
    // Add assertions for custom logic
}
```

---

## Adding a New Dependency

### Python Dependency

**Steps:**

1. **Add to requirements.txt**

```bash
cd python-layer

# Add new package
echo "new-package==1.2.3" >> requirements.txt

# Or edit manually
nano requirements.txt
```

2. **Install and test**

```bash
# Activate venv
source venv/bin/activate

# Install new package
pip install new-package==1.2.3

# Update requirements
pip freeze > requirements.txt

# Test import
python -c "import new_package; print(new_package.__version__)"
```

3. **Rebuild Docker image**

```bash
docker-compose build python-layer
docker-compose up -d python-layer
```

### Java Dependency

**Steps:**

1. **Add to pom.xml**

```xml
<!-- java-layer/pom.xml -->

<dependencies>
    <!-- Existing dependencies -->

    <!-- NEW: Add dependency -->
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>new-library</artifactId>
        <version>1.2.3</version>
    </dependency>
</dependencies>
```

2. **Reload Maven dependencies**

```bash
cd java-layer

# Download and install
mvn clean install

# Or in IDE: Right-click pom.xml → Maven → Reload Project
```

3. **Test import**

```java
import com.example.newlibrary.SomeClass;

// Use in code
SomeClass instance = new SomeClass();
```

4. **Rebuild Docker image**

```bash
docker-compose build java-layer
docker-compose up -d java-layer
```

---

## Debugging Issues

### Python Layer Debugging

**1. Check logs**

```bash
# Docker logs
docker logs -f excel-parser-python

# Look for errors
docker logs excel-parser-python 2>&1 | grep ERROR
```

**2. Enable debug logging**

```python
# python-layer/app/main.py

logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**3. Add breakpoints (local development)**

```python
# Add to code
import pdb; pdb.set_trace()

# Run in debug mode
python -m app.main
```

**4. Test endpoints manually**

```bash
# Health check
curl http://localhost:8000/health

# Test specific endpoint
curl -X POST "http://localhost:8000/api/v1/process/excel" \
  -F "file=@test.xlsx" \
  -v  # Verbose output
```

### Java Layer Debugging

**1. Check logs**

```bash
# Docker logs
docker logs -f excel-parser-java

# Look for exceptions
docker logs excel-parser-java 2>&1 | grep Exception
```

**2. Enable debug logging**

```yaml
# java-layer/src/main/resources/application.yml

logging:
  level:
    com.customeranalysis: DEBUG  # Changed from INFO
    org.apache.poi: DEBUG
```

**3. Test Java layer directly**

```bash
# Health check
curl http://localhost:8080/api/v1/excel/health

# Parse Excel
curl -X POST "http://localhost:8080/api/v1/excel/parse" \
  -F "file=@test.xlsx" \
  -v
```

### Flight Server Debugging

**1. Check if Flight server started**

```bash
# Look for Flight server startup message
docker logs excel-parser-python | grep "Arrow Flight"

# Should see: "Starting Arrow Flight server on grpc://0.0.0.0:8815"
```

**2. List active flights**

```bash
curl http://localhost:8000/api/v1/flight/list
```

**3. Test Flight connection**

```python
import pyarrow.flight as flight

try:
    client = flight.FlightClient("grpc://localhost:8815")
    flights = list(client.list_flights())
    print(f"Connected! Found {len(flights)} flights")
except Exception as e:
    print(f"Connection failed: {e}")
```

---

## Running Tests

### Python Tests

```bash
cd python-layer

# Activate venv
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_flight_server.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run in verbose mode
pytest -v

# Run specific test
pytest tests/test_flight_server.py::test_register_flight -v
```

### Java Tests

```bash
cd java-layer

# Run all tests
mvn test

# Run specific test class
mvn test -Dtest=ExcelParserServiceTest

# Run specific test method
mvn test -Dtest=ExcelParserServiceTest#shouldParseExcelWhenValidFile

# With coverage
mvn test jacoco:report

# View coverage report
open target/site/jacoco/index.html
```

### Integration Tests

```bash
# Start services
docker-compose up -d

# Wait for startup
sleep 10

# Run integration tests
python tests/integration/test_end_to_end.py

# Or use pytest
pytest tests/integration/
```

---

## Building and Deploying

### Local Development Build

```bash
# Build both layers
pnpm build

# Or individually
pnpm build:java
pnpm build:python
```

### Docker Build

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build python-layer
docker-compose build java-layer

# Build with no cache
docker-compose build --no-cache
```

### Start Services

```bash
# Start in foreground (see logs)
docker-compose up

# Start in background
docker-compose up -d

# Restart specific service
docker-compose restart python-layer

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Deploy to Production

**1. Build production images**

```bash
# Tag images
docker tag excel-parser-python:latest your-registry/excel-parser-python:v1.0.0
docker tag excel-parser-java:latest your-registry/excel-parser-java:v1.0.0

# Push to registry
docker push your-registry/excel-parser-python:v1.0.0
docker push your-registry/excel-parser-java:v1.0.0
```

**2. Deploy with docker-compose (production)**

```yaml
# docker-compose.prod.yml

version: '3.8'

services:
  python-layer:
    image: your-registry/excel-parser-python:v1.0.0
    environment:
      - JAVA_LAYER_URL=http://java-layer:8080
      - API_PORT=8000
      - FLIGHT_PORT=8815
    ports:
      - "8000:8000"
      - "8815:8815"
    restart: always

  java-layer:
    image: your-registry/excel-parser-java:v1.0.0
    ports:
      - "8080:8080"
    restart: always
```

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## Performance Optimization

### Task: Improve streaming performance

**1. Increase batch size**

```python
# python-layer/app/services/flight_server.py

# Default batch size
BATCH_SIZE = 10000

# Increase for more throughput (uses more memory)
BATCH_SIZE = 50000

# Or make it configurable
class ExcelFlightServer(flight.FlightServerBase):
    def __init__(self, location, batch_size=10000):
        self.batch_size = batch_size

    def do_get(self, context, ticket):
        # Use self.batch_size when streaming
        ...
```

**2. Enable compression**

```python
# python-layer/app/config.py

class Settings(BaseSettings):
    arrow_compression: str = "zstd"  # or "lz4" for faster compression
```

**3. Optimize Java parsing**

```java
// java-layer/.../service/ExcelParserService.java

// Use read-only mode for better performance
WorkbookFactory.create(file.getInputStream(), null, true);  // read-only

// Disable formula evaluation if not needed
FormulaEvaluator evaluator = null;  // Skip formula evaluation
```

**4. Profile performance**

```python
# Add timing logs
import time

start = time.time()
result = await process_excel(file)
elapsed = time.time() - start

logger.info(f"Processing took {elapsed:.2f}s")
```

**5. Monitor memory**

```python
import psutil
import os

process = psutil.Process(os.getpid())
memory_mb = process.memory_info().rss / 1024 / 1024
logger.info(f"Memory usage: {memory_mb:.2f} MB")
```

---

## Quick Task Checklist

When implementing a new feature:

- [ ] Update code (Python or Java)
- [ ] Add type hints/annotations
- [ ] Add error handling
- [ ] Add logging
- [ ] Write unit tests
- [ ] Test manually
- [ ] Update documentation
- [ ] Commit with proper message
- [ ] Include Claude attribution in commit

When fixing a bug:

- [ ] Reproduce the bug
- [ ] Write failing test
- [ ] Fix the code
- [ ] Verify test passes
- [ ] Test manually
- [ ] Add logging if needed
- [ ] Commit with fix message

When deploying:

- [ ] Run tests
- [ ] Build Docker images
- [ ] Test in staging
- [ ] Tag version
- [ ] Deploy to production
- [ ] Verify health checks
- [ ] Monitor logs

---

## Useful Command Snippets

```bash
# Watch logs in real-time
docker-compose logs -f python-layer

# Execute command in container
docker-compose exec python-layer bash

# Restart service
docker-compose restart python-layer

# View resource usage
docker stats

# Clean up Docker
docker system prune -a

# Rebuild and restart
docker-compose up --build -d

# View environment variables
docker-compose exec python-layer env

# Check port bindings
docker ps
```
