# Testing Infrastructure

**Doc-Type:** Testing Guide · Version 1.0 · Updated 2025-11-08 · Author AI Whisperers

---

## Test Structure

```
tests/
├── java/                      # Java layer unit tests
│   ├── ExcelParserServiceTest.java
│   └── ExcelParserControllerTest.java
├── python/                    # Python layer unit tests
│   ├── conftest.py
│   ├── test_aggregator.py
│   ├── test_arrow_formatter.py
│   ├── test_flight_server.py
│   └── test_java_client.py
├── integration-tests.sh       # Docker Compose integration tests
├── k8s-deploy-test.sh         # Kubernetes deployment tests
├── run-python-tests.sh        # Run Python tests with coverage
├── run-java-tests.sh          # Run Java tests with coverage
└── run-all-tests.sh           # Run all tests
```

---

## Running Tests

### All Tests
```bash
./tests/run-all-tests.sh
```

### Unit Tests Only

**Python:**
```bash
./tests/run-python-tests.sh
```

**Java:**
```bash
./tests/run-java-tests.sh
```

### Integration Tests (Docker)
```bash
docker-compose up -d
./tests/integration-tests.sh
docker-compose down
```

### K8s Deployment Test
```bash
./tests/k8s-deploy-test.sh
```

---

## CI/CD Pipelines

### GitHub Actions Workflows

**Java Layer CI** (`.github/workflows/ci-java.yml`)
- Build with Maven
- Run unit tests
- Build Docker image
- Triggered on java-layer changes

**Python Layer CI** (`.github/workflows/ci-python.yml`)
- Lint with ruff
- Run pytest with coverage
- Build Docker image
- Triggered on python-layer changes

**Integration Tests** (`.github/workflows/ci-integration.yml`)
- Build both images
- Start services with docker-compose
- Run integration tests
- Triggered on main branch

**CD Deploy** (`.github/workflows/cd-deploy.yml`)
- Build and push to GitHub Container Registry
- Tag with version/SHA
- Manual trigger or on tags

---

## Test Coverage

### Java Layer (100% Critical Nodes)
- ExcelParserService: Pipeline orchestration
- ExcelParserController: REST endpoints
- Service mocks: All extractors and formatters

### Python Layer (100% Critical Nodes)
- DataAggregator: Cell to table conversion, metadata extraction, statistics
- ArrowFormatter: Arrow serialization, schema inference
- FlightServer: gRPC streaming, flight management
- JavaClient: HTTP communication, error handling

### Integration
- Docker Compose: Service communication
- Kubernetes: Deployment and accessibility
- Arrow Flight: E2E streaming

---

## Quality Gates

All PRs must pass:
- Unit tests (100% of existing tests)
- Linting (ruff for Python)
- Docker build (both images)
- Integration tests (service communication)

---

## Adding New Tests

1. Add test file in appropriate location
2. Follow naming: `test_*.py` or `*-test.sh`
3. Update this README if new category
4. Ensure tests are idempotent
