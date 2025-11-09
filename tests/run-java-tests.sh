#!/bin/bash
set -e

cd "$(dirname "$0")/../java-layer"

echo "Running Java tests with coverage..."

# Create test directory in src/test if not exists
mkdir -p src/test/java/com/customeranalysis/excel

# Copy test files
cp -r ../tests/java/* src/test/java/com/customeranalysis/excel/ 2>/dev/null || true

# Run tests with Maven
mvn clean test

echo "Java tests completed!"
