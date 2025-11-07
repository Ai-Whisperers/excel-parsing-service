# Project Context & Important Information

Critical context and important information for Claude instances working on this project.

## Project Mission

**Goal:** Provide high-performance Excel parsing with real-time streaming capabilities for large datasets.

**Problem Solved:** Traditional REST APIs timeout or become extremely slow when processing large Excel files (100MB+, 1M+ rows). This service solves that with Arrow Flight streaming.

**Target Users:**
- Data engineers processing large Excel datasets
- Analytics platforms integrating Excel data
- Applications needing real-time Excel streaming
- Services with 100MB+ Excel files

## Critical Success Factors

1. **Performance:** Must handle 1GB Excel files in < 15 seconds
2. **Reliability:** No timeouts or memory issues
3. **Ease of Use:** Simple REST API for small files, Flight for large files
4. **Backward Compatibility:** Existing REST endpoints must continue working
5. **Zero Data Loss:** Parse all cells accurately

## Known Limitations

### Current Limitations

1. **No Authentication**
   - Development only, not production-ready
   - No rate limiting
   - No access control

2. **In-Memory Flight Registry**
   - Flights stored in Python process memory
   - Not persistent across restarts
   - Not shared across multiple instances

3. **Single-Threaded Flight Server**
   - Runs in single daemon thread
   - Limited concurrent streaming

4. **No Caching**
   - Re-parses same file every time
   - No deduplication

5. **File Size Limit**
   - Configurable (default 100MB for REST)
   - Limited by available memory

### Apache POI Limitations

1. **Not Thread-Safe**
   - Must create new Workbook per request
   - Cannot share workbook across threads

2. **Memory Intensive**
   - Large files consume significant RAM
   - XLS format more memory-intensive than XLSX

3. **Formula Evaluation**
   - Some complex formulas may not evaluate
   - External references not supported

## Design Decisions & Rationale

### Why Two-Plane Architecture?

**Decision:** Separate control (REST) and data (gRPC) planes

**Rationale:**
- REST is familiar and easy to use for small files
- gRPC is much faster for large data transfers
- Allows clients to choose based on use case
- Maintains backward compatibility

**Alternative Considered:** REST-only with streaming response
**Why Rejected:** HTTP chunked encoding is slow, limited to HTTP/1.1

### Why Arrow Flight?

**Decision:** Use Apache Arrow Flight for data streaming

**Rationale:**
- Zero-copy binary format (10-100x faster than JSON)
- Columnar format ideal for analytics
- Standard protocol with multi-language support
- Built-in batch streaming

**Alternative Considered:** gRPC with custom protobuf
**Why Rejected:** Reinventing the wheel, Arrow Flight is battle-tested

### Why Java for Parsing?

**Decision:** Use Java with Apache POI for Excel parsing

**Rationale:**
- Apache POI is the most mature Excel parsing library
- Better performance than Python libraries (openpyxl, xlrd)
- Handles complex Excel features (formulas, styles, merged cells)

**Alternative Considered:** Python-only with openpyxl
**Why Rejected:** openpyxl is slower and has limited features

### Why Python for Aggregation?

**Decision:** Use Python for data aggregation and API layer

**Rationale:**
- FastAPI is lightweight and fast
- PyArrow for Arrow data structures
- Easy integration with data science tools
- Rich ecosystem for data processing

**Alternative Considered:** Java-only
**Why Rejected:** Java is verbose for REST APIs, lacks Arrow Flight support

## Important Technical Constraints

### Memory Constraints

**Java Layer:**
- Default heap: 2GB (configurable with -Xmx)
- POI loads entire workbook into memory
- Large files (1GB+) need 3-4x RAM

**Python Layer:**
- No specific limits
- Arrow tables consume ~1x file size in RAM
- Flight registry stores tables in memory

**Recommendation:** 8GB+ RAM for production

### Network Constraints

**REST API:**
- Default timeout: 300 seconds
- Max upload size: 100MB (configurable)

**Arrow Flight:**
- No timeout (streaming)
- gRPC max message size: 4MB (batched)

### Concurrency Constraints

**Java Layer:**
- Thread-safe (Spring Boot)
- Each request gets new Workbook instance
- Can handle concurrent requests

**Python Layer:**
- FastAPI is async (thread-safe)
- Flight server runs in daemon thread
- Flight registry not thread-safe (use locks for writes)

## Security Considerations

### Current State (Development)

⚠️ **NOT PRODUCTION-READY** ⚠️

- No authentication
- No authorization
- No encryption (plain HTTP/gRPC)
- No input sanitization
- No rate limiting
- No audit logging

### Production Requirements

**Must Implement:**

1. **Authentication**
   - JWT tokens for REST API
   - Bearer tokens in Flight headers

2. **Authorization**
   - Role-based access control (RBAC)
   - Resource-level permissions

3. **Encryption**
   - HTTPS for REST API
   - TLS for Arrow Flight gRPC

4. **Input Validation**
   - File type validation (.xls/.xlsx only)
   - File size limits
   - Path traversal prevention

5. **Rate Limiting**
   - Per-IP limits
   - Per-user limits
   - Burst protection

6. **Monitoring**
   - Request logging
   - Error tracking
   - Performance metrics

## Performance Characteristics

### Benchmarks

Based on testing with 50-column datasets:

| Rows      | File Size | REST Time | Flight Time | Memory (Java) | Memory (Python) |
| --------- | --------- | --------- | ----------- | ------------- | --------------- |
| 1,000     | 1 MB      | 100 ms    | 50 ms       | 100 MB        | 50 MB           |
| 10,000    | 10 MB     | 1.5 s     | 200 ms      | 500 MB        | 200 MB          |
| 100,000   | 100 MB    | 25 s      | 1.5 s       | 2 GB          | 1 GB            |
| 1,000,000 | 1 GB      | Timeout   | 12 s        | 4 GB          | 2 GB            |

**Key Insights:**
- Flight is ~10x faster for 10MB files
- Flight is ~16x faster for 100MB files
- REST times out for 1GB files (Flight works)
- Memory usage roughly 2-4x file size

### Bottlenecks

1. **Java POI Parsing** - CPU-bound, most time spent here
2. **Network Transfer** - Bandwidth-limited for large files
3. **Python Aggregation** - Minimal overhead
4. **Arrow Serialization** - Very fast (zero-copy)

### Optimization Opportunities

1. **Parallel Sheet Processing** - Parse sheets concurrently (Java)
2. **Streaming Parsing** - SAX/event-based parsing for very large files
3. **Caching** - Cache parsed results (Redis)
4. **Compression** - Use lz4 instead of zstd for speed
5. **Batch Size Tuning** - Larger batches = higher throughput

## Error Handling Strategy

### Error Types

1. **Client Errors (4xx)**
   - Invalid file format
   - Missing parameters
   - File not found
   - File too large

2. **Server Errors (5xx)**
   - POI parsing failed
   - Java layer unavailable
   - Out of memory
   - Internal errors

### Error Propagation

```
Java Exception
    ↓
Java Controller → HTTP 500
    ↓
Python receives error
    ↓
Python logs + wraps
    ↓
FastAPI HTTPException
    ↓
JSON error response to client
```

### Error Recovery

**Transient Errors:**
- Network failures → Retry with exponential backoff
- Java layer unavailable → Retry up to 3 times

**Permanent Errors:**
- Invalid file format → Return 422 immediately
- File too large → Return 413 immediately

## Monitoring & Observability

### Health Checks

```bash
# Python layer + Java layer
curl http://localhost:8000/health

# Java layer directly
curl http://localhost:8080/api/v1/excel/health

# Flight server
curl http://localhost:8000/api/v1/flight/list
```

### Key Metrics to Track

**Request Metrics:**
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate (%)

**Flight Metrics:**
- Active flights (count)
- Bytes streamed (GB/s)
- Batch processing time (ms)

**System Metrics:**
- CPU usage (%)
- Memory usage (MB)
- Disk I/O (MB/s)

**Business Metrics:**
- Files processed (count)
- Total data processed (GB)
- Large file ratio (%)

### Logging Strategy

**Log Levels:**
- **DEBUG:** Detailed debugging (development only)
- **INFO:** Important events (production)
- **WARNING:** Unexpected but handled
- **ERROR:** Errors with stack traces
- **CRITICAL:** System failures

**What to Log:**
- Request start/end with timing
- File processing stats (size, rows, columns)
- Flight registration/deletion
- Errors with context
- Performance metrics

**What NOT to Log:**
- Cell data (PII, large volume)
- Passwords or tokens
- Full stack traces in INFO level

## Scaling Considerations

### Horizontal Scaling

**Can Scale:**
- Python REST API (stateless)
- Java parsing layer (stateless)

**Challenges:**
- Flight registry (in-memory, not shared)
- Load balancing gRPC (needs special config)

**Solutions:**
- Use external flight registry (Redis)
- Sticky sessions for Flight connections
- Service mesh for gRPC load balancing

### Vertical Scaling

**CPU:**
- POI parsing is CPU-bound
- More cores = more concurrent requests
- Consider CPU-optimized instances

**Memory:**
- Large files need significant RAM
- Recommend 8GB+ for production
- Consider memory-optimized instances

**Disk:**
- Minimal disk I/O
- Temp files for large uploads
- SSD not required

## Deployment Patterns

### Development

```bash
# Local: pnpm + hot reload
pnpm dev

# Docker: Full stack
docker-compose up
```

### Staging

```bash
# Docker Compose with prod config
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

### Production

**Option 1: Docker Compose**
- Simple, good for single-server deployments
- Limited scaling

**Option 2: Kubernetes**
- Complex but powerful
- Horizontal scaling
- Service discovery
- Health checks
- Rolling updates

**Option 3: Serverless (Future)**
- Lambda/Cloud Functions
- Limited by execution time (15 min max)
- Cold start issues

## Testing Strategy

### Unit Tests

**Python:**
- Test each service independently
- Mock external dependencies (Java client)
- Use pytest fixtures

**Java:**
- Test each extractor service
- Mock POI classes if needed
- Use JUnit + AssertJ

### Integration Tests

- Test Python → Java communication
- Test Flight streaming end-to-end
- Use real Excel files (small samples)

### Performance Tests

- Test with large files (100MB+)
- Measure response times
- Monitor memory usage
- Use Apache Bench or Locust

### Manual Tests

- Test with real Excel files
- Test edge cases (empty sheets, formulas, merged cells)
- Test error conditions (invalid files, large files)

## Future Enhancements

### Planned

1. **Authentication & Authorization**
   - JWT tokens
   - RBAC

2. **Persistent Flight Registry**
   - Store flights in Redis
   - Share across instances

3. **Caching**
   - Cache parsed results
   - Deduplication

4. **Advanced Features**
   - Delta streaming (only changed cells)
   - Parallel sheet processing
   - Incremental parsing

### Under Consideration

1. **Write Support**
   - Create Excel files from Arrow
   - DoPut for data ingestion

2. **Format Conversion**
   - Excel → Parquet
   - Excel → CSV
   - Excel → JSON Lines

3. **Cloud Storage Integration**
   - S3 support
   - GCS support
   - Azure Blob support

4. **Webhook Support**
   - Async processing
   - Completion notifications

## Common Pitfalls

### Pitfall 1: Loading Entire Dataset into Memory

```python
# BAD - OOM for large files
table = reader.read_all()
df = table.to_pandas()

# GOOD - Stream batches
for batch in reader:
    df = batch.data.to_pandas()
    process(df)
    del df
```

### Pitfall 2: Not Closing POI Workbooks

```java
// BAD - Resource leak
Workbook workbook = WorkbookFactory.create(file);
// ... forget to close

// GOOD - Auto-close
try (Workbook workbook = WorkbookFactory.create(file)) {
    // Process
}
```

### Pitfall 3: Thread-Unsafe Flight Registry

```python
# BAD - Race condition
self.flights[flight_id] = data

# GOOD - Use lock
with self._lock:
    self.flights[flight_id] = data
```

### Pitfall 4: Not Handling Empty Sheets

```java
// BAD - NullPointerException
Row row = sheet.getRow(0);
Cell cell = row.getCell(0);  // Crashes if row is null

// GOOD - Null checks
Row row = sheet.getRow(0);
if (row != null) {
    Cell cell = row.getCell(0);
    if (cell != null) {
        // Process cell
    }
}
```

### Pitfall 5: Ignoring Timeouts

```python
# BAD - Default timeout (10s)
async with httpx.AsyncClient() as client:
    response = await client.post(url, files=files)

# GOOD - Longer timeout for large files
async with httpx.AsyncClient(timeout=300.0) as client:
    response = await client.post(url, files=files)
```

## Important File Locations

**Configuration:**
- `python-layer/.env` - Python environment variables
- `python-layer/app/config.py` - Python settings
- `java-layer/src/main/resources/application.yml` - Java settings

**Entry Points:**
- `python-layer/app/main.py` - Python FastAPI app
- `java-layer/src/main/java/.../ExcelParserApplication.java` - Java Spring Boot app

**Core Logic:**
- `python-layer/app/services/flight_server.py` - Flight server
- `java-layer/src/main/java/.../service/ExcelParserService.java` - Parsing orchestrator

**Tests:**
- `python-layer/tests/` - Python tests
- `java-layer/src/test/java/` - Java tests

**Documentation:**
- `.claude/` - Claude context (this folder)
- `.mcp/` - User documentation
- `README.md` - Project overview

## Quick Decision Guide

**When to use REST:**
- File < 10 MB
- Simple use case
- Quick testing
- Backward compatibility

**When to use Flight:**
- File > 10 MB
- Performance critical
- Large datasets
- Real-time streaming

**When to modify Java:**
- Change parsing logic
- Add POI features
- Handle new Excel features

**When to modify Python:**
- Add REST endpoint
- Add Flight operation
- Change data format
- Add aggregation logic

**When to add dependency:**
- Python: requirements.txt
- Java: pom.xml
- Rebuild Docker images

## Contact & Resources

**Repository:** https://github.com/Ai-Whisperers/excel-parsing-service
**Issues:** Report bugs and feature requests on GitHub
**Documentation:** See `.mcp/` folder
**License:** MIT

## Final Notes for Claude

1. **Always read this context first** - Saves time and prevents mistakes
2. **Follow conventions** - Consistency is critical
3. **Test thoroughly** - Large file edge cases are common
4. **Document decisions** - Future Claude instances will thank you
5. **Ask questions** - Better to clarify than assume
6. **Performance matters** - This project is about speed
7. **Safety first** - Validate inputs, handle errors
8. **Log everything** - Production debugging relies on logs

Welcome to the team! 🎉
