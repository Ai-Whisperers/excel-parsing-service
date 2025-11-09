#!/bin/bash
set -e

echo "========================================="
echo "Running All Tests"
echo "========================================="

cd "$(dirname "$0")"

echo ""
echo "1. Running Java Layer Tests..."
echo "-----------------------------------------"
./run-java-tests.sh

echo ""
echo "2. Running Python Layer Tests..."
echo "-----------------------------------------"
./run-python-tests.sh

echo ""
echo "3. Running Integration Tests..."
echo "-----------------------------------------"
./integration-tests.sh

echo ""
echo "========================================="
echo "All Tests Passed!"
echo "========================================="
echo ""
echo "Coverage Reports:"
echo "  Python: tests/coverage/python/index.html"
echo "  Java: java-layer/target/site/jacoco/index.html"
