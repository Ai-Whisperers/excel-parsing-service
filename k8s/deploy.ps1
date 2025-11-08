# PowerShell deployment script for Windows
# Excel Parser Kubernetes Deployment

$ErrorActionPreference = "Stop"

Write-Host "==================================" -ForegroundColor Green
Write-Host "Excel Parser Kubernetes Deployment" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""

# Check if kubectl is installed
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "Error: kubectl is not installed" -ForegroundColor Red
    exit 1
}

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker is not installed" -ForegroundColor Red
    exit 1
}

Write-Host "Step 1: Building Docker images..." -ForegroundColor Green

# Build Java layer
Write-Host "Building Java layer Docker image..." -ForegroundColor Yellow
Set-Location ..\java-layer
docker build -t excel-parser-java:latest .

# Build Python layer
Write-Host "Building Python layer Docker image..." -ForegroundColor Yellow
Set-Location ..\python-layer
docker build -t excel-parser-python:latest .

Set-Location ..\k8s

Write-Host ""
Write-Host "Step 2: Images built successfully!" -ForegroundColor Green
Write-Host "If you have a private registry, tag and push images now:" -ForegroundColor Yellow
Write-Host "  docker tag excel-parser-java:latest your-registry/excel-parser-java:latest" -ForegroundColor Yellow
Write-Host "  docker push your-registry/excel-parser-java:latest" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to continue with deployment"

Write-Host "Step 3: Creating namespace..." -ForegroundColor Green
kubectl apply -f namespace.yaml

Write-Host "Step 4: Deploying ConfigMap..." -ForegroundColor Green
kubectl apply -f configmap.yaml

Write-Host "Step 5: Deploying Java layer..." -ForegroundColor Green
kubectl apply -f java-layer-deployment.yaml

Write-Host "Step 6: Waiting for Java layer to be ready..." -ForegroundColor Green
kubectl wait --for=condition=ready pod -l app=excel-parser-java -n excel-parser --timeout=300s

Write-Host "Step 7: Deploying Python layer..." -ForegroundColor Green
kubectl apply -f python-layer-deployment.yaml

Write-Host "Step 8: Waiting for Python layer to be ready..." -ForegroundColor Green
kubectl wait --for=condition=ready pod -l app=excel-parser-python -n excel-parser --timeout=300s

Write-Host ""
Write-Host "==================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""

Write-Host "Services deployed:" -ForegroundColor Yellow
kubectl get deployments -n excel-parser
Write-Host ""
kubectl get services -n excel-parser
Write-Host ""
kubectl get pods -n excel-parser

Write-Host ""
Write-Host "Access the service:" -ForegroundColor Green
Write-Host "  REST API: http://<node-ip>:30800" -ForegroundColor Cyan
Write-Host "  Arrow Flight: <node-ip>:30815" -ForegroundColor Cyan
Write-Host ""
Write-Host "To get node IP, run: kubectl get nodes -o wide" -ForegroundColor Yellow
