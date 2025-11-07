# Excel POI Parser Service

A two-layer microservice architecture for parsing Excel files using Apache POI (Java) and aggregating/formatting results with Python (Arrow/JSON).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Application                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP Request (Excel File)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               Python Aggregation Layer (Port 8000)          │
│  • Receives Excel files from clients                        │
│  • Forwards to Java layer for parsing                       │
│  • Aggregates and formats results                           │
│  • Outputs Arrow IPC or JSON                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Internal HTTP (JSON)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                Java Parsing Layer (Port 8080)               │
│  • Apache POI Excel parsing                                 │
│  • Cell extraction & metadata                               │
│  • Data normalization & type inference                      │
│  • Returns structured JSON                                  │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
excel-poi-parser/
├── pnpm-workspace.yaml          # pnpm workspace configuration
├── package.json                 # Root orchestration scripts
├── docker-compose.yml           # Multi-container setup
│
├── java-layer/                  # Java parsing layer
│   ├── package.json             # pnpm scripts for Maven
│   ├── pom.xml                  # Maven dependencies
│   ├── Dockerfile
│   └── src/main/java/com/customeranalysis/excel/
│       ├── ExcelParserApplication.java
│       ├── controller/
│       │   └── ExcelParserController.java
│       ├── service/
│       │   ├── ExcelParserService.java
│       │   └── extractor/
│       │       ├── WorkbookLoaderService.java
│       │       ├── SheetEnumeratorService.java
│       │       ├── CellExtractorService.java
│       │       ├── MetadataExtractorService.java
│       │       ├── DataNormalizerService.java
│       │       └── OutputFormatterService.java
│       ├── dto/
│       └── model/
│
└── python-layer/                # Python aggregation layer
    ├── package.json             # pnpm scripts for Python
    ├── requirements.txt         # Python dependencies
    ├── Dockerfile
    └── app/
        ├── main.py              # FastAPI application
        ├── config.py            # Configuration
        ├── models/
        │   └── schemas.py       # Pydantic models
        └── services/
            ├── java_client.py   # Java layer client
            ├── aggregator.py    # Data aggregation
            ├── arrow_formatter.py
            └── json_formatter.py
```

## Prerequisites

- **Node.js** >= 18.x
- **pnpm** >= 8.x
- **Java** 17 (for Java layer)
- **Maven** 3.x (for Java layer)
- **Python** 3.11+ (for Python layer)
- **Docker** & **Docker Compose** (optional, for containerized deployment)

## Installation

### Using pnpm (Monorepo Orchestration)

```bash
# Install pnpm globally if not installed
npm install -g pnpm

# Install all dependencies (both layers)
pnpm install:all
```

### Manual Installation

#### Java Layer
```bash
cd java-layer
mvn clean install
```

#### Python Layer
```bash
cd python-layer
pip install -r requirements.txt
```

## Development

### Start Both Layers Concurrently

```bash
pnpm dev
```

### Start Individual Layers

```bash
# Java layer (port 8080)
pnpm dev:java

# Python layer (port 8000)
pnpm dev:python
```

## Docker Deployment

### Build and Start All Services

```bash
pnpm docker:build
pnpm docker:up
```

Or using Docker Compose directly:

```bash
docker-compose up --build
```

### Stop Services

```bash
pnpm docker:down
```

## API Endpoints

### Python Layer (Port 8000)

#### Process Excel File (Multipart Upload)
```http
POST /api/v1/process/excel
Content-Type: multipart/form-data

Parameters:
  - file: Excel file (required)
  - sheet_name: Filter by sheet name (optional)
  - region: Cell region (e.g., "A1:D10") (optional)
  - output_format: "json" or "arrow" (default: "json")
  - aggregate: true/false (default: true)
```

#### Process Excel from Path
```http
POST /api/v1/process/excel-from-path
Content-Type: application/json

{
  "file_path": "/path/to/file.xlsx",
  "sheet_name": "Sheet1",
  "region": "A1:D10",
  "output_format": "json",
  "aggregate": true
}
```

#### Health Check
```http
GET /health
```

### Java Layer (Port 8080)

#### Parse Excel (Internal API)
```http
POST /api/v1/excel/parse
Content-Type: multipart/form-data
```

#### Health Check
```http
GET /api/v1/excel/health
```

## Output Formats

### JSON Format
```json
{
  "success": true,
  "metadata": {
    "numberOfSheets": 2,
    "numberOfNames": 0,
    "sheets": {
      "Sheet1": 0,
      "Sheet2": 1
    }
  },
  "sheets": {
    "Sheet1": {
      "columns": ["Column_0", "Column_1", ...],
      "data": [[...], [...], ...],
      "rowCount": 100,
      "columnCount": 10
    }
  },
  "statistics": {...},
  "timestamp": 1234567890
}
```

### Arrow Format
Returns Apache Arrow IPC stream format (binary)
- Content-Type: `application/vnd.apache.arrow.stream`
- Can be read by Arrow libraries in any language

## Testing

```bash
# Test all
pnpm test

# Test Java layer
pnpm test:java

# Test Python layer
pnpm test:python
```

## Build

```bash
# Build all
pnpm build

# Build Java layer
pnpm build:java

# Build Python layer
pnpm build:python
```

## Clean

```bash
pnpm clean
```

## Component Descriptions

### Java Layer Components

1. **WorkbookLoaderService**: Loads Excel files (.xls/.xlsx) with POI
2. **SheetEnumeratorService**: Iterates over sheets and collects metadata
3. **CellExtractorService**: Extracts cell data, formulas, merged cells
4. **MetadataExtractorService**: Gathers styles, named ranges, comments
5. **DataNormalizerService**: Normalizes values and infers types
6. **OutputFormatterService**: Formats data as JSON

### Python Layer Components

1. **JavaLayerClient**: HTTP client for Java layer communication
2. **DataAggregator**: Aggregates cell data into tabular format
3. **ArrowFormatter**: Converts to Apache Arrow IPC format
4. **JSONFormatter**: Formats structured JSON output

## Configuration

### Java Layer
Edit `java-layer/src/main/resources/application.yml`:
```yaml
parser:
  max-rows: 100000
  max-columns: 1000
  enable-formula-evaluation: true
```

### Python Layer
Copy `.env.example` to `.env` and configure:
```bash
JAVA_LAYER_URL=http://localhost:8080
MAX_FILE_SIZE_MB=100
ARROW_COMPRESSION=zstd
```

## License

MIT
