#!/bin/bash
set -e

BASE_URL="http://localhost:8000"
JAVA_URL="http://localhost:8080"

echo "Testing Java layer health..."
curl -f ${JAVA_URL}/api/v1/excel/health || exit 1

echo "Testing Python layer health..."
HEALTH=$(curl -f ${BASE_URL}/health)
echo $HEALTH | grep -q "healthy" || exit 1

echo "Testing Flight list..."
curl -f ${BASE_URL}/api/v1/flight/list || exit 1

echo "All integration tests passed!"
