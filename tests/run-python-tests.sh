#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "Running Python tests with coverage..."
cd python-layer

pip install -q pytest pytest-cov pytest-asyncio

pytest ../tests/python/ -v \
  --cov=app \
  --cov-report=term-missing \
  --cov-report=html:../tests/coverage/python \
  --cov-report=xml:../tests/coverage/python-coverage.xml

echo "Python tests completed!"
echo "Coverage report: tests/coverage/python/index.html"
