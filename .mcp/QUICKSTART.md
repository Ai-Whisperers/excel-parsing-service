# Quick Start Guide

Get up and running with the Excel POI Parser Service in **5 minutes**.

## Prerequisites

Choose one of the following:

**Option A: Docker (Recommended)**
- Docker Desktop or Docker Engine
- Docker Compose

**Option B: Local Development**
- Node.js >= 18.x
- pnpm >= 8.x
- Java 17
- Maven 3.x
- Python 3.11+

## Installation

### Option A: Docker (Fastest)

```bash
# 1. Clone the repository
git clone https://github.com/Ai-Whisperers/excel-parsing-service.git
cd excel-parsing-service

# 2. Start services
docker-compose up --build

# 3. Wait for services to start (~30 seconds)
# You'll see:
# ✓ java-layer started
# ✓ python-layer started
```

### Option B: Local Development

```bash
# 1. Clone the repository
git clone https://github.com/Ai-Whisperers/excel-parsing-service.git
cd excel-parsing-service

# 2. Install pnpm (if not installed)
npm install -g pnpm

# 3. Install all dependencies
pnpm install:all

# 4. Start both layers
pnpm dev
```

## Verify Installation

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

**Expected output:**
```json
{
  "python_layer": "healthy",
  "java_layer": "Java Layer: Excel Parser Service is running"
}
```

### Test 2: List Available Flights

```bash
curl http://localhost:8000/api/v1/flight/list
```

**Expected output:**
```json
{
  "flights": [],
  "count": 0,
  "grpc_endpoint": "grpc://localhost:8815"
}
```

### Test 3: Get Client Example

```bash
curl http://localhost:8000/api/v1/flight/example
```

**Expected output:** Python code example for Arrow Flight streaming

## First Request

### Example 1: Process Small Excel File (REST)

Create a test Excel file or use an existing one:

```bash
# Upload and process Excel file
curl -X POST "http://localhost:8000/api/v1/process/excel" \
  -F "file=@test.xlsx" \
  -F "output_format=json"
```

**Response:**
```json
{
  "success": true,
  "metadata": {
    "numberOfSheets": 1,
    "sheets": {
      "Sheet1": 0
    }
  },
  "sheets": {
    "Sheet1": {
      "columns": ["Column_0", "Column_1", "Column_2"],
      "data": [
        ["Value1", "Value2", "Value3"],
        ["Value4", "Value5", "Value6"]
      ],
      "rowCount": 2,
      "columnCount": 3
    }
  },
  "timestamp": 1234567890
}
```

### Example 2: Stream Large Excel File (Arrow Flight)

For files > 10 MB, use the high-performance Flight streaming:

**Step 1: Prepare Flight (via REST)**
```bash
curl -X POST "http://localhost:8000/api/v1/flight/prepare" \
  -d "file_path=/path/to/large.xlsx"
```

**Response:**
```json
{
  "flight_id": "excel_data_large.xlsx",
  "schema": {
    "fields": [
      {"name": "Column_0", "type": "string"},
      {"name": "Column_1", "type": "double"}
    ]
  },
  "total_records": 1000000,
  "grpc_endpoint": "grpc://localhost:8815",
  "ticket": "excel:excel_data_large.xlsx:{}"
}
```

**Step 2: Stream Data (via Python Client)**

Create `client.py`:
```python
import pyarrow.flight as flight
import requests

# 1. Prepare flight
response = requests.post(
    "http://localhost:8000/api/v1/flight/prepare",
    params={"file_path": "/path/to/large.xlsx"}
)
flight_info = response.json()

# 2. Connect to Flight server
client = flight.FlightClient("grpc://localhost:8815")

# 3. Stream data
ticket = flight.Ticket(flight_info["ticket"].encode())
reader = client.do_get(ticket)

# 4. Process batches
for batch in reader:
    df = batch.data.to_pandas()
    print(f"Received {len(df)} rows")
    # Process data here...

# 5. Or read entire stream at once
# table = reader.read_all()
# df = table.to_pandas()
```

Run the client:
```bash
pip install pyarrow requests pandas
python client.py
```

## Common Use Cases

### Use Case 1: Parse Excel and Get JSON

```bash
curl -X POST "http://localhost:8000/api/v1/process/excel" \
  -F "file=@sales_data.xlsx" \
  -F "output_format=json" \
  -F "sheet_name=Q1_2024"
```

### Use Case 2: Parse Specific Region

```bash
curl -X POST "http://localhost:8000/api/v1/process/excel" \
  -F "file=@sales_data.xlsx" \
  -F "region=A1:D100" \
  -F "output_format=json"
```

### Use Case 3: Get Arrow Binary Stream

```bash
curl -X POST "http://localhost:8000/api/v1/process/excel" \
  -F "file=@sales_data.xlsx" \
  -F "output_format=arrow" \
  --output output.arrow
```

Then read with PyArrow:
```python
import pyarrow as pa

with open('output.arrow', 'rb') as f:
    reader = pa.ipc.open_stream(f)
    table = reader.read_all()
    df = table.to_pandas()
    print(df.head())
```

### Use Case 4: Stream Large File (1M+ rows)

```python
import pyarrow.flight as flight
import requests

# Prepare flight
resp = requests.post(
    "http://localhost:8000/api/v1/flight/prepare",
    params={"file_path": "/data/huge_dataset.xlsx"}
)
ticket = resp.json()["ticket"]

# Stream in batches
client = flight.FlightClient("grpc://localhost:8815")
reader = client.do_get(flight.Ticket(ticket.encode()))

total_rows = 0
for batch in reader:
    df = batch.data.to_pandas()
    total_rows += len(df)
    # Process incrementally - no memory overflow
    print(f"Processed {total_rows} rows so far...")
```

## Performance Tips

### For Small Files (< 10 MB)
✅ Use REST API: `/api/v1/process/excel`
- Simple HTTP upload
- JSON response
- Easy to debug

### For Large Files (> 10 MB)
✅ Use Arrow Flight: `/api/v1/flight/prepare` + gRPC streaming
- 10-100x faster
- Zero-copy streaming
- Batch processing

### For Very Large Files (> 100 MB)
✅ Use Arrow Flight with batch processing
```python
# Don't accumulate - process incrementally
for batch in reader:
    df = batch.data.to_pandas()
    process(df)        # Process
    del df            # Free memory
```

## Troubleshooting

### Issue: "Connection refused" on localhost:8000

**Solution:**
```bash
# Check if services are running
docker ps

# Restart services
docker-compose down
docker-compose up --build
```

### Issue: "Connection refused" on localhost:8815

**Solution:**
```bash
# Check Flight server logs
docker logs excel-parser-python

# Verify Flight server started
curl http://localhost:8000/api/v1/flight/list
```

### Issue: "Java layer unhealthy"

**Solution:**
```bash
# Check Java layer logs
docker logs excel-parser-java

# Check Java layer directly
curl http://localhost:8080/api/v1/excel/health
```

### Issue: Out of memory when processing large file

**Solution:**
```python
# Use streaming instead of reading all at once
# BAD - loads entire dataset into memory
table = reader.read_all()
df = table.to_pandas()

# GOOD - processes in batches
for batch in reader:
    df = batch.data.to_pandas()
    process(df)
    del df  # Free memory after each batch
```

## Next Steps

Now that you have the service running:

1. **[API.md](API.md)** - Explore all API endpoints with detailed examples
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Understand the hybrid architecture
3. **[SETUP.md](SETUP.md)** - Set up development environment
4. **Main README.md** - Full project documentation

## Quick Reference

### Service Endpoints

| Service         | Port | URL                        |
| --------------- | ---- | -------------------------- |
| Control Plane   | 8000 | http://localhost:8000      |
| Data Plane      | 8815 | grpc://localhost:8815      |
| Java Layer      | 8080 | http://localhost:8080      |

### Key REST Endpoints

| Endpoint                    | Purpose                    |
| --------------------------- | -------------------------- |
| `GET /health`               | Health check               |
| `POST /api/v1/process/excel`| Process Excel (REST)       |
| `POST /api/v1/flight/prepare`| Prepare for streaming     |
| `GET /api/v1/flight/list`   | List available flights     |
| `GET /api/v1/flight/example`| Get client code example    |

### Performance Reference

| File Size | Method      | Time    |
| --------- | ----------- | ------- |
| < 10 MB   | REST        | < 2s    |
| 10-100 MB | Flight      | 1-2s    |
| > 100 MB  | Flight      | 2-15s   |

## Support

- **GitHub Issues:** https://github.com/Ai-Whisperers/excel-parsing-service/issues
- **Documentation:** See `.mcp/` folder
- **Main README:** See root `README.md`
