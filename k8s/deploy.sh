#!/bin/bash

set -e

echo "=================================="
echo "Excel Parser Kubernetes Deployment"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Building Docker images...${NC}"

# Build Java layer
echo "Building Java layer Docker image..."
cd ../java-layer
docker build -t excel-parser-java:latest .

# Build Python layer
echo "Building Python layer Docker image..."
cd ../python-layer
docker build -t excel-parser-python:latest .

cd ../k8s

echo -e "${GREEN}Step 2: Tagging images for on-premise registry (if needed)...${NC}"
echo -e "${YELLOW}If you have a private registry, you should tag and push images now.${NC}"
echo -e "${YELLOW}Example: docker tag excel-parser-java:latest your-registry/excel-parser-java:latest${NC}"
echo ""
read -p "Press enter to continue with deployment..."

echo -e "${GREEN}Step 3: Creating namespace...${NC}"
kubectl apply -f namespace.yaml

echo -e "${GREEN}Step 4: Deploying ConfigMap...${NC}"
kubectl apply -f configmap.yaml

echo -e "${GREEN}Step 5: Deploying Java layer...${NC}"
kubectl apply -f java-layer-deployment.yaml

echo -e "${GREEN}Step 6: Waiting for Java layer to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=excel-parser-java -n excel-parser --timeout=300s

echo -e "${GREEN}Step 7: Deploying Python layer...${NC}"
kubectl apply -f python-layer-deployment.yaml

echo -e "${GREEN}Step 8: Waiting for Python layer to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=excel-parser-python -n excel-parser --timeout=300s

echo ""
echo -e "${GREEN}=================================="
echo "Deployment Complete!"
echo "==================================${NC}"
echo ""
echo "Services deployed:"
kubectl get deployments -n excel-parser
echo ""
kubectl get services -n excel-parser
echo ""
kubectl get pods -n excel-parser
echo ""
echo -e "${GREEN}Access the service:${NC}"
echo "  REST API: http://<node-ip>:30800"
echo "  Arrow Flight: <node-ip>:30815"
echo ""
echo -e "${YELLOW}To get node IP, run: kubectl get nodes -o wide${NC}"
