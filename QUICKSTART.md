# Quick Start Guide

## Getting Started in 5 Minutes

### Option 1: Using Docker (Recommended)

1. **Start the services**:
   ```bash
   pnpm docker:up
   ```

2. **Test the service**:
   ```bash
   # Health check
   curl http://localhost:8000/health

   # Upload and process an Excel file
   curl -X POST http://localhost:8000/api/v1/process/excel \
     -F "file=@your-file.xlsx" \
     -F "output_format=json"
   ```

### Option 2: Local Development

1. **Install dependencies**:
   ```bash
   pnpm install:all
   ```

2. **Start both layers**:
   ```bash
   pnpm dev
   ```

   This will start:
   - Java layer on `http://localhost:8080`
   - Python layer on `http://localhost:8000`

3. **Test the services**:
   ```bash
   # Python layer health
   curl http://localhost:8000/health

   # Java layer health
   curl http://localhost:8080/api/v1/excel/health
   ```

## Example Usage

### Upload Excel File (JSON Response)

```bash
curl -X POST http://localhost:8000/api/v1/process/excel \
  -F "file=@sample.xlsx" \
  -F "sheet_name=Sheet1" \
  -F "output_format=json"
```

### Upload Excel File (Arrow Response)

```bash
curl -X POST http://localhost:8000/api/v1/process/excel \
  -F "file=@sample.xlsx" \
  -F "output_format=arrow" \
  --output result.arrow
```

### Process from File Path

```bash
curl -X POST http://localhost:8000/api/v1/process/excel-from-path \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/file.xlsx",
    "sheet_name": "Sheet1",
    "output_format": "json",
    "aggregate": true
  }'
```

## Python Client Example

```python
import httpx

async def process_excel():
    async with httpx.AsyncClient() as client:
        with open("sample.xlsx", "rb") as f:
            files = {"file": ("sample.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            params = {"output_format": "json"}

            response = await client.post(
                "http://localhost:8000/api/v1/process/excel",
                files=files,
                params=params
            )

            return response.json()
```

## JavaScript Client Example

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('output_format', 'json');

const response = await fetch('http://localhost:8000/api/v1/process/excel', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result);
```

## Available pnpm Scripts

| Command | Description |
|---------|-------------|
| `pnpm install:all` | Install all dependencies (both layers) |
| `pnpm dev` | Start both layers in development mode |
| `pnpm dev:java` | Start Java layer only |
| `pnpm dev:python` | Start Python layer only |
| `pnpm build` | Build both layers |
| `pnpm test` | Run tests for both layers |
| `pnpm clean` | Clean build artifacts |
| `pnpm docker:build` | Build Docker images |
| `pnpm docker:up` | Start Docker containers |
| `pnpm docker:down` | Stop Docker containers |

## Troubleshooting

### Port Already in Use

If ports 8080 or 8000 are already in use:

1. Change ports in `docker-compose.yml`:
   ```yaml
   services:
     java-layer:
       ports:
         - "8081:8080"  # Change external port
     python-layer:
       ports:
         - "8001:8000"  # Change external port
   ```

2. Update Python layer configuration to point to new Java port.

### Java Layer Not Starting

Check Java version:
```bash
java -version  # Should be 17 or higher
```

### Python Dependencies Issues

Try upgrading pip:
```bash
cd python-layer
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Review [parser.md](parser.md) for architecture details
- Customize configurations in `application.yml` and `.env`
- Add custom extractors or formatters as needed
