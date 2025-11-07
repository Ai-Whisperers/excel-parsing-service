# API Reference

Complete API documentation for the Excel POI Parser Service.

## Table of Contents

1. [Overview](#overview)
2. [Control Plane API (REST)](#control-plane-api-rest)
3. [Data Plane API (Arrow Flight)](#data-plane-api-arrow-flight)
4. [Java Layer API](#java-layer-api)
5. [Response Formats](#response-formats)
6. [Error Handling](#error-handling)
7. [Client Examples](#client-examples)

## Overview

The service exposes two API planes:

| Plane | Protocol | Port | Base URL |
| ----- | -------- | ---- | -------- |
| **Control Plane** | REST (HTTP) | 8000 | `http://localhost:8000` |
| **Data Plane** | gRPC (Arrow Flight) | 8815 | `grpc://localhost:8815` |
| **Java Layer** | REST (HTTP) | 8080 | `http://localhost:8080` |

## Control Plane API (REST)

### Base Information

**Base URL:** `http://localhost:8000`

**Content-Type:**
- Request: `multipart/form-data` (file uploads) or `application/json`
- Response: `application/json` or `application/vnd.apache.arrow.stream`

### Endpoints

---

#### `GET /`

Get service information and available endpoints.

**Request:**
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "service": "Excel Parser - Python Layer",
  "version": "2.0.0",
  "architecture": "Hybrid (REST + Arrow Flight)",
  "status": "running",
  "endpoints": {
    "control_plane": {
      "rest_api": "http://localhost:8000",
      "health": "/health",
      "legacy_upload": "/api/v1/process/excel",
      "flight_prepare": "/api/v1/flight/prepare",
      "flight_list": "/api/v1/flight/list"
    },
    "data_plane": {
      "grpc_streaming": "grpc://localhost:8815",
      "protocol": "Arrow Flight",
      "example": "/api/v1/flight/example"
    }
  }
}
```

---

#### `GET /health`

Health check endpoint for monitoring.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "python_layer": "healthy",
  "java_layer": "Java Layer: Excel Parser Service is running"
}
```

**Status Codes:**
- `200 OK` - All layers healthy
- `503 Service Unavailable` - One or more layers unhealthy

---

#### `POST /api/v1/process/excel`

Process Excel file via REST (legacy endpoint for small files < 10 MB).

**Parameters:**

| Parameter | Type | Required | Description |
| --------- | ---- | -------- | ----------- |
| `file` | File | Yes | Excel file (.xls or .xlsx) |
| `sheet_name` | String | No | Filter by specific sheet name |
| `region` | String | No | Cell region (e.g., "A1:D10") |
| `output_format` | String | No | "json" or "arrow" (default: "json") |
| `aggregate` | Boolean | No | Aggregate data (default: true) |

**Request (curl):**
```bash
curl -X POST "http://localhost:8000/api/v1/process/excel" \
  -F "file=@sales_data.xlsx" \
  -F "sheet_name=Q1_2024" \
  -F "region=A1:Z100" \
  -F "output_format=json" \
  -F "aggregate=true"
```

**Request (Python):**
```python
import requests

with open('sales_data.xlsx', 'rb') as f:
    files = {'file': f}
    params = {
        'sheet_name': 'Q1_2024',
        'output_format': 'json',
        'aggregate': True
    }
    response = requests.post(
        'http://localhost:8000/api/v1/process/excel',
        files=files,
        data=params
    )
    data = response.json()
```

**Response (JSON format):**
```json
{
  "success": true,
  "metadata": {
    "numberOfSheets": 2,
    "numberOfNames": 0,
    "sheets": {
      "Q1_2024": 0,
      "Q2_2024": 1
    }
  },
  "sheets": {
    "Q1_2024": {
      "columns": ["Date", "Product", "Revenue", "Quantity"],
      "data": [
        ["2024-01-01", "Widget A", 1000.50, 10],
        ["2024-01-02", "Widget B", 2500.75, 25],
        ["2024-01-03", "Widget C", 1800.00, 18]
      ],
      "rowCount": 3,
      "columnCount": 4
    }
  },
  "statistics": {
    "totalRows": 3,
    "totalColumns": 4,
    "processingTimeMs": 150
  },
  "timestamp": 1704067200
}
```

**Response (Arrow format):**
- Content-Type: `application/vnd.apache.arrow.stream`
- Binary Arrow IPC stream

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid file or parameters
- `413 Payload Too Large` - File exceeds size limit
- `500 Internal Server Error` - Processing error

---

#### `POST /api/v1/process/excel-from-path`

Process Excel file from server file path (no upload required).

**Request Body:**
```json
{
  "file_path": "/data/sales_2024.xlsx",
  "sheet_name": "Q1_2024",
  "region": "A1:Z100",
  "output_format": "json",
  "aggregate": true
}
```

**Request (curl):**
```bash
curl -X POST "http://localhost:8000/api/v1/process/excel-from-path" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/data/sales_2024.xlsx",
    "output_format": "json"
  }'
```

**Request (Python):**
```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/process/excel-from-path',
    json={
        'file_path': '/data/sales_2024.xlsx',
        'output_format': 'json'
    }
)
data = response.json()
```

**Response:** Same as `/api/v1/process/excel`

---

#### `POST /api/v1/flight/prepare`

Prepare Excel file for high-performance streaming via Arrow Flight.

**Parameters:**

| Parameter | Type | Required | Description |
| --------- | ---- | -------- | ----------- |
| `file_path` | String | Yes | Server path to Excel file |
| `sheet_name` | String | No | Filter by specific sheet |
| `region` | String | No | Cell region filter |

**Request (curl):**
```bash
curl -X POST "http://localhost:8000/api/v1/flight/prepare" \
  -d "file_path=/data/large_dataset.xlsx" \
  -d "sheet_name=Sales"
```

**Request (Python):**
```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/flight/prepare',
    params={
        'file_path': '/data/large_dataset.xlsx',
        'sheet_name': 'Sales'
    }
)
flight_info = response.json()
```

**Response:**
```json
{
  "flight_id": "excel_data_large_dataset.xlsx",
  "schema": {
    "fields": [
      {
        "name": "Date",
        "type": "timestamp[ms]",
        "nullable": true
      },
      {
        "name": "Product",
        "type": "utf8",
        "nullable": true
      },
      {
        "name": "Revenue",
        "type": "double",
        "nullable": true
      },
      {
        "name": "Quantity",
        "type": "int64",
        "nullable": true
      }
    ]
  },
  "total_records": 1000000,
  "grpc_endpoint": "grpc://localhost:8815",
  "ticket": "excel:excel_data_large_dataset.xlsx:{}",
  "instructions": {
    "step_1": "Connect to gRPC endpoint",
    "step_2": "Use ticket to stream data",
    "example": "See /api/v1/flight/example"
  }
}
```

**Status Codes:**
- `200 OK` - Flight prepared successfully
- `400 Bad Request` - Invalid file path or parameters
- `404 Not Found` - File not found
- `500 Internal Server Error` - Processing error

---

#### `POST /api/v1/flight/upload`

Upload Excel file and prepare for streaming (upload + prepare in one call).

**Parameters:**

| Parameter | Type | Required | Description |
| --------- | ---- | -------- | ----------- |
| `file` | File | Yes | Excel file (.xls or .xlsx) |
| `sheet_name` | String | No | Filter by specific sheet |
| `region` | String | No | Cell region filter |

**Request (curl):**
```bash
curl -X POST "http://localhost:8000/api/v1/flight/upload" \
  -F "file=@large_dataset.xlsx" \
  -F "sheet_name=Sales"
```

**Request (Python):**
```python
import requests

with open('large_dataset.xlsx', 'rb') as f:
    files = {'file': f}
    params = {'sheet_name': 'Sales'}
    response = requests.post(
        'http://localhost:8000/api/v1/flight/upload',
        files=files,
        data=params
    )
    flight_info = response.json()
```

**Response:** Same as `/api/v1/flight/prepare`

---

#### `GET /api/v1/flight/list`

List all available flights (prepared datasets).

**Request:**
```bash
curl http://localhost:8000/api/v1/flight/list
```

**Response:**
```json
{
  "flights": [
    {
      "flight_id": "excel_data_sales_2024.xlsx",
      "total_records": 500000,
      "schema_fields": 10,
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "flight_id": "excel_data_inventory.xlsx",
      "total_records": 1000000,
      "schema_fields": 15,
      "created_at": "2024-01-15T11:00:00Z"
    }
  ],
  "count": 2,
  "grpc_endpoint": "grpc://localhost:8815"
}
```

---

#### `GET /api/v1/flight/info/{flight_id}`

Get detailed information about a specific flight.

**Parameters:**

| Parameter | Type | Required | Description |
| --------- | ---- | -------- | ----------- |
| `flight_id` | String | Yes | Flight identifier (URL path) |

**Request:**
```bash
curl http://localhost:8000/api/v1/flight/info/excel_data_sales_2024.xlsx
```

**Response:**
```json
{
  "flight_id": "excel_data_sales_2024.xlsx",
  "schema": {
    "fields": [...]
  },
  "total_records": 500000,
  "total_bytes": 52428800,
  "ticket": "excel:excel_data_sales_2024.xlsx:{}",
  "grpc_endpoint": "grpc://localhost:8815",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

#### `GET /api/v1/flight/example`

Get Python client code example for Arrow Flight streaming.

**Request:**
```bash
curl http://localhost:8000/api/v1/flight/example
```

**Response:**
```json
{
  "language": "python",
  "code": "import pyarrow.flight as flight\nimport requests\n\n# 1. Prepare flight\nresponse = requests.post(\n    \"http://localhost:8000/api/v1/flight/prepare\",\n    params={\"file_path\": \"/path/to/file.xlsx\"}\n)\nflight_info = response.json()\n\n# 2. Connect to Flight server\nclient = flight.FlightClient(\"grpc://localhost:8815\")\n\n# 3. Stream data\nticket = flight.Ticket(flight_info[\"ticket\"].encode())\nreader = client.do_get(ticket)\n\n# 4. Process batches\nfor batch in reader:\n    df = batch.data.to_pandas()\n    print(f\"Received {len(df)} rows\")\n",
  "dependencies": [
    "pyarrow",
    "requests",
    "pandas"
  ],
  "install": "pip install pyarrow requests pandas"
}
```

---

## Data Plane API (Arrow Flight)

### Base Information

**Endpoint:** `grpc://localhost:8815`

**Protocol:** Apache Arrow Flight (gRPC)

**Language Support:** Python, Java, JavaScript, C++, R, etc.

### Flight Methods

---

#### `DoGet` - Stream Data (Server → Client)

Stream Arrow record batches from server to client.

**Python Example:**
```python
import pyarrow.flight as flight

# Connect to Flight server
client = flight.FlightClient("grpc://localhost:8815")

# Create ticket (from /api/v1/flight/prepare response)
ticket = flight.Ticket(b"excel:excel_data_sales.xlsx:{}")

# Stream data
reader = client.do_get(ticket)

# Process batches
for batch in reader:
    # batch.data is a RecordBatch
    df = batch.data.to_pandas()
    print(f"Batch: {len(df)} rows")
    # Process data...

# Or read entire stream
table = reader.read_all()
df = table.to_pandas()
```

**JavaScript Example:**
```javascript
const flight = require('@apache-arrow/flight');

// Connect
const client = await flight.connect('grpc://localhost:8815');

// Stream data
const stream = await client.doGet({
  ticket: Buffer.from('excel:excel_data_sales.xlsx:{}')
});

// Process batches
for await (const batch of stream) {
  console.log(`Received ${batch.numRows} rows`);
  // Process batch...
}
```

**Java Example:**
```java
import org.apache.arrow.flight.*;
import org.apache.arrow.memory.RootAllocator;

// Connect
RootAllocator allocator = new RootAllocator();
FlightClient client = FlightClient.builder()
    .allocator(allocator)
    .location(Location.forGrpcInsecure("localhost", 8815))
    .build();

// Stream data
Ticket ticket = new Ticket("excel:excel_data_sales.xlsx:{}".getBytes());
FlightStream stream = client.getStream(ticket);

// Process batches
while (stream.next()) {
    VectorSchemaRoot root = stream.getRoot();
    System.out.println("Batch: " + root.getRowCount() + " rows");
    // Process batch...
}
```

---

#### `DoPut` - Upload Data (Client → Server)

Upload Arrow data stream from client to server.

**Python Example:**
```python
import pyarrow as pa
import pyarrow.flight as flight

# Create data
data = {
    'column1': [1, 2, 3],
    'column2': ['a', 'b', 'c']
}
table = pa.table(data)

# Connect
client = flight.FlightClient("grpc://localhost:8815")

# Upload descriptor
descriptor = flight.FlightDescriptor.for_path("uploaded_data")

# Upload data
writer, metadata_reader = client.do_put(descriptor, table.schema)
writer.write_table(table)
writer.close()
```

---

#### `ListFlights` - List Available Datasets

List all available flights/datasets.

**Python Example:**
```python
import pyarrow.flight as flight

client = flight.FlightClient("grpc://localhost:8815")

# List all flights
for flight_info in client.list_flights():
    print(f"Flight: {flight_info.descriptor}")
    print(f"Records: {flight_info.total_records}")
    print(f"Schema: {flight_info.schema}")
```

---

#### `GetFlightInfo` - Get Flight Metadata

Get schema and metadata for a specific flight.

**Python Example:**
```python
import pyarrow.flight as flight

client = flight.FlightClient("grpc://localhost:8815")

# Get flight info
descriptor = flight.FlightDescriptor.for_path("excel_data_sales.xlsx")
flight_info = client.get_flight_info(descriptor)

print(f"Schema: {flight_info.schema}")
print(f"Total records: {flight_info.total_records}")
print(f"Total bytes: {flight_info.total_bytes}")
```

---

## Java Layer API

### Base Information

**Base URL:** `http://localhost:8080/api/v1/excel`

**Internal API** - Called by Python layer, not directly by clients.

---

#### `POST /api/v1/excel/parse`

Parse Excel file and return structured data (internal endpoint).

**Request (multipart/form-data):**
```bash
curl -X POST "http://localhost:8080/api/v1/excel/parse" \
  -F "file=@data.xlsx" \
  -F "sheetName=Sheet1" \
  -F "region=A1:Z100"
```

**Response:**
```json
{
  "success": true,
  "metadata": {
    "numberOfSheets": 1,
    "numberOfNames": 0,
    "sheets": {
      "Sheet1": 0
    }
  },
  "sheets": {
    "Sheet1": {
      "data": [[...], [...], ...],
      "mergedRegions": [],
      "columnWidths": {},
      "rowHeights": {}
    }
  },
  "namedRanges": {},
  "comments": {}
}
```

---

#### `GET /api/v1/excel/health`

Health check for Java layer.

**Request:**
```bash
curl http://localhost:8080/api/v1/excel/health
```

**Response:**
```
Java Layer: Excel Parser Service is running
```

---

## Response Formats

### JSON Format

Standard JSON response structure:

```json
{
  "success": true,
  "metadata": {
    "numberOfSheets": 2,
    "sheets": {
      "Sheet1": 0,
      "Sheet2": 1
    }
  },
  "sheets": {
    "Sheet1": {
      "columns": ["Col1", "Col2", "Col3"],
      "data": [
        ["val1", "val2", "val3"],
        ["val4", "val5", "val6"]
      ],
      "rowCount": 2,
      "columnCount": 3
    }
  },
  "statistics": {
    "totalRows": 2,
    "totalColumns": 3,
    "processingTimeMs": 150
  },
  "timestamp": 1704067200
}
```

### Arrow IPC Format

Binary Apache Arrow IPC stream format.

**Reading in Python:**
```python
import pyarrow as pa

# From HTTP response
response = requests.post('...', data={'output_format': 'arrow'})
arrow_bytes = response.content

with pa.ipc.open_stream(arrow_bytes) as reader:
    table = reader.read_all()
    df = table.to_pandas()
```

**Reading from file:**
```python
import pyarrow as pa

with open('output.arrow', 'rb') as f:
    reader = pa.ipc.open_stream(f)
    table = reader.read_all()
    df = table.to_pandas()
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 400,
  "error_type": "ValidationError"
}
```

### Common Error Codes

| Code | Meaning | Common Causes |
| ---- | ------- | ------------- |
| `400` | Bad Request | Invalid file, missing parameters |
| `404` | Not Found | File path not found, flight not found |
| `413` | Payload Too Large | File exceeds size limit |
| `422` | Unprocessable Entity | Invalid file format |
| `500` | Internal Server Error | Processing error, POI exception |
| `503` | Service Unavailable | Java layer down |

### Example Error Responses

**Invalid file format:**
```json
{
  "detail": "Unsupported file format. Only .xls and .xlsx are supported",
  "status_code": 422
}
```

**File not found:**
```json
{
  "detail": "File not found: /data/missing.xlsx",
  "status_code": 404
}
```

**Java layer unavailable:**
```json
{
  "detail": "Java layer unavailable. Please check if the service is running.",
  "status_code": 503
}
```

---

## Client Examples

### Python Complete Example

```python
import requests
import pyarrow.flight as flight
import pandas as pd

class ExcelParserClient:
    def __init__(self, rest_url="http://localhost:8000", grpc_url="grpc://localhost:8815"):
        self.rest_url = rest_url
        self.grpc_url = grpc_url
        self.flight_client = flight.FlightClient(grpc_url)

    def process_small_file(self, file_path, output_format='json'):
        """Process small file via REST"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            params = {'output_format': output_format}
            response = requests.post(
                f"{self.rest_url}/api/v1/process/excel",
                files=files,
                data=params
            )
            return response.json()

    def stream_large_file(self, server_path, sheet_name=None):
        """Stream large file via Arrow Flight"""
        # 1. Prepare flight
        params = {'file_path': server_path}
        if sheet_name:
            params['sheet_name'] = sheet_name

        response = requests.post(
            f"{self.rest_url}/api/v1/flight/prepare",
            params=params
        )
        flight_info = response.json()

        # 2. Stream data
        ticket = flight.Ticket(flight_info['ticket'].encode())
        reader = self.flight_client.do_get(ticket)

        # 3. Process batches
        dfs = []
        for batch in reader:
            df = batch.data.to_pandas()
            dfs.append(df)

        # Combine all batches
        return pd.concat(dfs, ignore_index=True)

# Usage
client = ExcelParserClient()

# Small file
data = client.process_small_file('small.xlsx')
print(data)

# Large file (streaming)
df = client.stream_large_file('/data/large.xlsx', sheet_name='Sales')
print(f"Streamed {len(df)} rows")
```

### JavaScript Complete Example

```javascript
const axios = require('axios');
const flight = require('@apache-arrow/flight');

class ExcelParserClient {
  constructor(restUrl = 'http://localhost:8000', grpcUrl = 'grpc://localhost:8815') {
    this.restUrl = restUrl;
    this.grpcUrl = grpcUrl;
  }

  async processSmallFile(filePath, outputFormat = 'json') {
    const FormData = require('form-data');
    const fs = require('fs');

    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    form.append('output_format', outputFormat);

    const response = await axios.post(
      `${this.restUrl}/api/v1/process/excel`,
      form,
      { headers: form.getHeaders() }
    );

    return response.data;
  }

  async streamLargeFile(serverPath, sheetName = null) {
    // 1. Prepare flight
    const params = { file_path: serverPath };
    if (sheetName) params.sheet_name = sheetName;

    const prepareResponse = await axios.post(
      `${this.restUrl}/api/v1/flight/prepare`,
      null,
      { params }
    );

    const flightInfo = prepareResponse.data;

    // 2. Connect to Flight server
    const client = await flight.connect(this.grpcUrl);

    // 3. Stream data
    const stream = await client.doGet({
      ticket: Buffer.from(flightInfo.ticket)
    });

    // 4. Process batches
    const batches = [];
    for await (const batch of stream) {
      console.log(`Received ${batch.numRows} rows`);
      batches.push(batch);
    }

    return batches;
  }
}

// Usage
const client = new ExcelParserClient();

// Small file
client.processSmallFile('small.xlsx')
  .then(data => console.log(data));

// Large file (streaming)
client.streamLargeFile('/data/large.xlsx', 'Sales')
  .then(batches => console.log(`Streamed ${batches.length} batches`));
```

---

## Rate Limiting

Current implementation has no rate limiting. For production:

**Recommended limits:**
- `/api/v1/process/excel`: 10 requests/minute per IP
- `/api/v1/flight/prepare`: 5 requests/minute per IP
- Flight streaming: No limit (handled by gRPC flow control)

---

## Authentication (Future)

Current implementation has no authentication. For production:

**Planned authentication methods:**
- JWT tokens in Authorization header
- API keys for service-to-service
- OAuth 2.0 for user applications

**Example (future):**
```python
# REST API
headers = {'Authorization': 'Bearer <jwt-token>'}
response = requests.post(url, headers=headers)

# Flight API
token = ('bearer', '<jwt-token>')
reader = client.do_get(ticket, options=flight.FlightCallOptions(headers=[token]))
```

---

## Additional Resources

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Deep dive into architecture
- **[SETUP.md](SETUP.md)** - Development environment setup
- **Apache Arrow Flight:** https://arrow.apache.org/docs/format/Flight.html
- **FastAPI Docs:** https://fastapi.tiangolo.com/
