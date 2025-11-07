# Coding Conventions & Standards

Coding standards and best practices for this project. Follow these when writing or modifying code.

## General Principles

1. **Clarity over cleverness** - Write code that's easy to understand
2. **Consistency over perfection** - Match existing code style
3. **Safety over speed** - Validate inputs, handle errors
4. **Documentation over memorization** - Comment complex logic
5. **Testing over hoping** - Test edge cases

## Python Layer Conventions

### Code Style

**Formatter:** Black (line length: 88)
**Linter:** Ruff
**Type Checker:** MyPy (optional but encouraged)
**Docstrings:** Google style

### File Organization

```python
"""
Module docstring explaining purpose.

Example:
    Basic usage example here.
"""

# Standard library imports
import os
import time
from typing import Optional, List, Dict

# Third-party imports
from fastapi import FastAPI, HTTPException
import pyarrow as pa

# Local imports
from app.services.java_client import JavaLayerClient
from app.models.schemas import ParseResponse
from app.config import settings

# Constants
MAX_RETRIES = 3
DEFAULT_BATCH_SIZE = 10000

# Module-level variables
logger = logging.getLogger(__name__)

# Functions/Classes
class MyClass:
    """Class docstring."""
    ...
```

### Naming Conventions

```python
# Variables and functions: snake_case
user_count = 10
def process_excel(file_path: str) -> dict:
    pass

# Classes: PascalCase
class ExcelFlightServer:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE_MB = 100
ARROW_COMPRESSION = "zstd"

# Private methods/variables: leading underscore
def _internal_helper():
    pass

_cache = {}

# Type hints: Always use for function signatures
def parse_file(
    file_path: str,
    sheet_name: Optional[str] = None
) -> Dict[str, Any]:
    """Parse Excel file.

    Args:
        file_path: Path to Excel file
        sheet_name: Optional sheet filter

    Returns:
        Dictionary with parsed data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format invalid
    """
    pass
```

### FastAPI Patterns

```python
# Endpoint naming: Use REST conventions
@app.get("/api/v1/resource")           # List/Get
@app.post("/api/v1/resource")          # Create
@app.put("/api/v1/resource/{id}")      # Update
@app.delete("/api/v1/resource/{id}")   # Delete

# Use dependency injection
from fastapi import Depends

def get_java_client():
    return JavaLayerClient(settings.java_layer_url)

@app.post("/api/v1/parse")
async def parse_excel(
    file: UploadFile = File(...),
    java_client: JavaLayerClient = Depends(get_java_client)
):
    return await java_client.parse_excel(file)

# Response models: Always define
from pydantic import BaseModel

class ParseResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    timestamp: int

@app.post("/api/v1/parse", response_model=ParseResponse)
async def parse_excel(...) -> ParseResponse:
    return ParseResponse(success=True, data=..., timestamp=...)

# Error handling: Use HTTPException
from fastapi import HTTPException

@app.get("/api/v1/resource/{id}")
async def get_resource(id: str):
    resource = await find_resource(id)
    if not resource:
        raise HTTPException(
            status_code=404,
            detail=f"Resource not found: {id}"
        )
    return resource
```

### Async/Await Patterns

```python
# Use async for I/O operations
async def fetch_from_java(file_path: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(...)
        return response.json()

# Don't use async for CPU-bound operations
def process_data(data: pd.DataFrame) -> pd.DataFrame:
    # CPU-bound, no async needed
    return data.transform(...)

# Combine async and sync properly
async def process_excel(file_path: str):
    # I/O: async
    raw_data = await fetch_from_java(file_path)

    # CPU: sync (in executor if needed)
    processed = process_data(raw_data)

    return processed
```

### Logging Patterns

```python
import logging

logger = logging.getLogger(__name__)

# Log levels:
logger.debug("Detailed debugging info")    # Development only
logger.info("Normal operations")           # Production: important events
logger.warning("Something unexpected")     # Production: warnings
logger.error("Error occurred", exc_info=True)  # Production: errors
logger.critical("System failure")          # Production: critical failures

# Good logging
logger.info(f"Processing Excel file: {file_path}")
logger.info(f"Flight registered: {flight_id} ({total_records} records)")
logger.error(f"Failed to parse Excel: {str(e)}", exc_info=True)

# Bad logging
logger.info("Starting")  # Too vague
logger.info(f"Data: {large_dict}")  # Too much data
logger.error(str(e))  # No stack trace
```

### Error Handling

```python
# Specific exceptions first
try:
    result = process_file(path)
except FileNotFoundError:
    logger.error(f"File not found: {path}")
    raise HTTPException(status_code=404, detail="File not found")
except ValueError as e:
    logger.error(f"Invalid file format: {str(e)}")
    raise HTTPException(status_code=422, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")

# Always log exceptions with exc_info=True
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {str(e)}", exc_info=True)
    raise

# Clean up resources
try:
    file = open(path, 'rb')
    process(file)
finally:
    file.close()

# Or use context managers
with open(path, 'rb') as file:
    process(file)
```

### Arrow/PyArrow Patterns

```python
import pyarrow as pa
import pyarrow.flight as flight

# Create Arrow table from dict
data = {
    'column1': [1, 2, 3],
    'column2': ['a', 'b', 'c']
}
table = pa.table(data)

# Create Arrow table from pandas
import pandas as pd
df = pd.DataFrame(data)
table = pa.Table.from_pandas(df)

# Stream Arrow batches (GOOD - memory efficient)
reader = client.do_get(ticket)
for batch in reader:
    df = batch.data.to_pandas()
    process(df)
    del df  # Free memory

# Load entire table (BAD - memory intensive)
table = reader.read_all()  # Don't do this for large data
df = table.to_pandas()

# Flight server: Always inherit FlightServerBase
class ExcelFlightServer(flight.FlightServerBase):
    def __init__(self, location):
        super().__init__(location)

    def do_get(self, context, ticket):
        # Return RecordBatchStream
        return flight.RecordBatchStream(table)
```

## Java Layer Conventions

### Code Style

**Formatter:** Spring Boot conventions
**Naming:** camelCase (methods/variables), PascalCase (classes)
**Annotations:** Lombok for boilerplate reduction

### File Organization

```java
package com.customeranalysis.excel.service;

// Imports: organized groups
import java.io.IOException;
import java.util.List;
import java.util.Map;

import org.apache.poi.ss.usermodel.Workbook;
import org.springframework.stereotype.Service;

import lombok.extern.slf4j.Slf4j;

/**
 * Service for parsing Excel files.
 *
 * @author Team Name
 */
@Slf4j
@Service
public class ExcelParserService {
    // Constants
    private static final int MAX_ROWS = 100000;

    // Dependencies (constructor injection)
    private final WorkbookLoaderService workbookLoader;

    public ExcelParserService(WorkbookLoaderService workbookLoader) {
        this.workbookLoader = workbookLoader;
    }

    // Public methods
    public ParseResponse parseExcel(MultipartFile file) {
        // Implementation
    }

    // Private methods
    private void validateFile(MultipartFile file) {
        // Implementation
    }
}
```

### Naming Conventions

```java
// Classes: PascalCase
public class ExcelParserService { }

// Methods: camelCase
public ParseResponse parseExcel() { }

// Variables: camelCase
String fileName = "data.xlsx";
int rowCount = 100;

// Constants: UPPER_SNAKE_CASE
private static final int MAX_ROWS = 100000;
private static final String DEFAULT_SHEET = "Sheet1";

// Interfaces: PascalCase (no I prefix)
public interface ExcelParser { }

// Implementations: PascalCase + Impl suffix
public class ExcelParserImpl implements ExcelParser { }
```

### Spring Boot Patterns

```java
// Service: Use @Service annotation
@Service
@Slf4j
public class ExcelParserService {
    private final DependencyService dependency;

    // Constructor injection (preferred)
    public ExcelParserService(DependencyService dependency) {
        this.dependency = dependency;
    }
}

// Controller: Use @RestController
@RestController
@RequestMapping("/api/v1/excel")
@Slf4j
public class ExcelParserController {
    private final ExcelParserService parserService;

    @PostMapping("/parse")
    public ResponseEntity<ParseResponse> parseExcel(
        @RequestParam("file") MultipartFile file
    ) {
        ParseResponse response = parserService.parseExcel(file);
        return ResponseEntity.ok(response);
    }
}

// Configuration: Use @Configuration
@Configuration
public class AppConfig {
    @Bean
    public SomeService someService() {
        return new SomeServiceImpl();
    }
}
```

### Lombok Usage

```java
// DTOs: Use @Data
@Data
@AllArgsConstructor
@NoArgsConstructor
public class ParseResponse {
    private boolean success;
    private Map<String, Object> metadata;
    private Map<String, SheetData> sheets;
}

// Entities: Use @Data or individual annotations
@Data
@Builder
public class SheetData {
    private List<List<Object>> data;
    private int rowCount;
    private int columnCount;
}

// Services: Use @Slf4j for logging
@Slf4j
@Service
public class ExcelParserService {
    public void parse() {
        log.info("Parsing Excel file");  // Auto-injected logger
    }
}

// Avoid @Data on services (use it for POJOs only)
```

### Error Handling

```java
// Custom exceptions
public class ExcelParsingException extends RuntimeException {
    public ExcelParsingException(String message) {
        super(message);
    }

    public ExcelParsingException(String message, Throwable cause) {
        super(message, cause);
    }
}

// Service layer: Throw domain exceptions
public ParseResponse parseExcel(MultipartFile file) {
    try {
        Workbook workbook = loadWorkbook(file);
        return extractData(workbook);
    } catch (IOException e) {
        log.error("Failed to read Excel file", e);
        throw new ExcelParsingException("Failed to read file", e);
    }
}

// Controller layer: Handle exceptions
@ExceptionHandler(ExcelParsingException.class)
public ResponseEntity<ErrorResponse> handleParsingException(
    ExcelParsingException e
) {
    log.error("Excel parsing failed", e);
    return ResponseEntity
        .status(HttpStatus.INTERNAL_SERVER_ERROR)
        .body(new ErrorResponse(e.getMessage()));
}

// Global exception handler
@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(Exception e) {
        log.error("Unexpected error", e);
        return ResponseEntity
            .status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(new ErrorResponse("Internal server error"));
    }
}
```

### Apache POI Patterns

```java
// Always close workbooks
try (Workbook workbook = WorkbookFactory.create(file.getInputStream())) {
    // Process workbook
} catch (IOException e) {
    throw new ExcelParsingException("Failed to load workbook", e);
}

// Iterate sheets safely
for (int i = 0; i < workbook.getNumberOfSheets(); i++) {
    Sheet sheet = workbook.getSheetAt(i);
    processSheet(sheet);
}

// Iterate rows safely
for (Row row : sheet) {
    processRow(row);
}

// Get cell value safely
private Object getCellValue(Cell cell) {
    if (cell == null) {
        return null;
    }

    switch (cell.getCellType()) {
        case STRING:
            return cell.getStringCellValue();
        case NUMERIC:
            if (DateUtil.isCellDateFormatted(cell)) {
                return cell.getDateCellValue();
            }
            return cell.getNumericCellValue();
        case BOOLEAN:
            return cell.getBooleanCellValue();
        case FORMULA:
            return evaluateFormula(cell);
        case BLANK:
            return null;
        default:
            return cell.toString();
    }
}

// Thread safety: Create new workbook per request
// POI is NOT thread-safe!
public ParseResponse parseExcel(MultipartFile file) {
    // Each request gets its own workbook instance
    try (Workbook workbook = WorkbookFactory.create(file.getInputStream())) {
        // Safe: workbook not shared across threads
        return process(workbook);
    }
}
```

## Docker & Configuration

### Dockerfile Patterns

```dockerfile
# Use official base images
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# Expose ports with comments
# 8000: REST API (control plane)
# 8815: Arrow Flight gRPC (data plane)
EXPOSE 8000 8815

# Use exec form for CMD
CMD ["python", "-m", "app.main"]
```

### Environment Variables

```bash
# Use UPPER_SNAKE_CASE
API_PORT=8000
FLIGHT_PORT=8815
JAVA_LAYER_URL=http://localhost:8080

# Provide defaults in code
class Settings(BaseSettings):
    api_port: int = 8000  # Default

# Document in .env.example
# API Configuration
API_PORT=8000  # REST API port

# Flight Configuration
FLIGHT_PORT=8815  # Arrow Flight gRPC port
```

## Git Conventions

### Commit Messages

```bash
# Format: <type>: <subject>

# Types:
feat: Add new feature
fix: Fix bug
docs: Update documentation
refactor: Refactor code
test: Add/update tests
chore: Maintain project

# Examples:
feat: Add Arrow Flight streaming support
fix: Handle empty Excel sheets correctly
docs: Update API documentation
refactor: Extract cell parsing logic
test: Add integration tests for Flight server
chore: Update dependencies

# Always include:
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Branch Naming

```bash
# Format: <type>/<description>

feature/add-flight-streaming
bugfix/handle-empty-sheets
docs/update-readme
refactor/extract-services
test/add-integration-tests
```

## Testing Conventions

### Python Tests

```python
# File naming: test_*.py
# tests/test_flight_server.py

import pytest
from app.services.flight_server import ExcelFlightServer

# Test naming: test_<what>_<condition>_<expected>
def test_register_flight_success():
    """Test that flight registration succeeds with valid data."""
    server = ExcelFlightServer()
    table = create_test_table()

    server.register_flight("test_flight", table)

    assert "test_flight" in server.flights
    assert server.flights["test_flight"]["total_records"] == 100

# Use fixtures
@pytest.fixture
def flight_server():
    return ExcelFlightServer()

def test_do_get_returns_batches(flight_server):
    # Use fixture
    ...

# Parametrize for multiple cases
@pytest.mark.parametrize("file_size,expected_time", [
    (1_000, 0.1),
    (10_000, 0.5),
    (100_000, 2.0),
])
def test_processing_time(file_size, expected_time):
    # Test with different inputs
    ...
```

### Java Tests

```java
// Test naming: should<ExpectedBehavior>When<StateUnderTest>
@Test
void shouldParseExcelWhenValidFileProvided() {
    // Given
    MultipartFile file = createMockExcelFile();

    // When
    ParseResponse response = parserService.parseExcel(file);

    // Then
    assertTrue(response.isSuccess());
    assertNotNull(response.getMetadata());
}

// Use @BeforeEach for setup
@BeforeEach
void setUp() {
    parserService = new ExcelParserService(dependencies);
}

// Use AssertJ for fluent assertions
assertThat(response.getSheets())
    .isNotEmpty()
    .containsKey("Sheet1");
```

## Documentation Conventions

### Code Comments

```python
# Good: Explain WHY, not WHAT
# Use Arrow Flight for large files to avoid timeouts
if file_size > 10_MB:
    return stream_via_flight(file)

# Bad: Explain obvious
# Check if file size is greater than 10MB
if file_size > 10_MB:
    ...

# Complex logic: Add explanation
# Parse ticket format: "excel:flight_id:{options_json}"
# Example: "excel:data_2024.xlsx:{batch_size:5000}"
parts = ticket.split(':', 2)
```

### Docstrings

```python
def process_excel(
    file_path: str,
    sheet_name: Optional[str] = None
) -> Dict[str, Any]:
    """Process Excel file and return structured data.

    This function parses an Excel file using the Java layer and
    aggregates the results into a dictionary format suitable for
    Arrow or JSON serialization.

    Args:
        file_path: Path to Excel file (.xls or .xlsx)
        sheet_name: Optional filter for specific sheet

    Returns:
        Dictionary with keys:
            - metadata: File metadata
            - sheets: Sheet data
            - statistics: Processing stats

    Raises:
        FileNotFoundError: If file_path doesn't exist
        ValueError: If file format is invalid
        HTTPException: If Java layer is unavailable

    Example:
        >>> result = process_excel("/data/sales.xlsx")
        >>> print(result['metadata']['numberOfSheets'])
        2
    """
    pass
```

## Performance Considerations

### Python

```python
# GOOD: Stream batches
for batch in reader:
    df = batch.data.to_pandas()
    process(df)
    del df

# BAD: Load all data
table = reader.read_all()
df = table.to_pandas()  # OOM for large files

# GOOD: Use generators
def process_batches():
    for batch in reader:
        yield batch.data

# BAD: Build large lists
batches = [batch.data for batch in reader]  # Memory issue
```

### Java

```java
// GOOD: Close resources
try (Workbook workbook = WorkbookFactory.create(file)) {
    // Process
}  // Auto-closed

// BAD: Resource leak
Workbook workbook = WorkbookFactory.create(file);
// ... forget to close
```

## Key Reminders

1. **Python:** Always use type hints
2. **Java:** Always close POI resources
3. **Both:** Log errors with stack traces
4. **Both:** Validate inputs
5. **Both:** Handle exceptions gracefully
6. **FastAPI:** Use Pydantic models for validation
7. **Spring:** Use constructor injection
8. **Arrow:** Stream batches, don't load all
9. **POI:** Not thread-safe, create per request
10. **Git:** Follow commit message format

## When in Doubt

1. Check existing code for patterns
2. Follow language idioms (Pythonic vs Java conventions)
3. Prefer readability over brevity
4. Add tests for new functionality
5. Document complex logic
6. Ask questions in comments if unsure
