# Testing Infrastructure

**Doc-Type:** Testing Guide · Version 1.0 · Updated 2025-11-08 · Author AI Whisperers

---

## Test Structure

```
tests/
├── integration-tests.sh       # Docker Compose integration tests
├── k8s-deploy-test.sh         # Kubernetes deployment tests
├── test_arrow_flight.py       # Arrow Flight streaming tests
└── python-layer/tests/        # Python unit tests
    ├── __init__.py
    └── test_health.py
```

---

## Running Tests

### Unit Tests (Python)
```bash
cd python-layer
pip install pytest pytest-cov
pytest tests/ -v --cov=app
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

### Arrow Flight Test
```bash
python tests/test_arrow_flight.py
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

### Java Layer
- Unit tests: Spring Boot components
- Integration tests: REST endpoints

### Python Layer
- Unit tests: FastAPI routes
- Integration tests: Java layer communication
- E2E tests: Arrow Flight streaming

### Kubernetes
- Deployment validation
- Service accessibility
- Health check verification

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
