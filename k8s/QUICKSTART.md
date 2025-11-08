# Quick Start Guide - Deploy to Kubernetes Today

This guide will help you get the Excel Parser service running on your on-premise Kubernetes cluster as quickly as possible.

## Prerequisites Check

```bash
# Check kubectl
kubectl version --client

# Check Docker
docker --version

# Check cluster connection
kubectl get nodes
```

## Fast Track Deployment (5 minutes)

### For Windows Users

```powershell
# Run from the k8s directory
.\deploy.ps1
```

### For Linux/Mac Users

```bash
# Run from the k8s directory
chmod +x deploy.sh
./deploy.sh
```

## Manual Deployment (if scripts fail)

### 1. Build Images (2 minutes)

```bash
# From project root
cd java-layer
docker build -t excel-parser-java:latest .

cd ../python-layer
docker build -t excel-parser-python:latest .
```

### 2. Load Images to Cluster

**For kind cluster:**
```bash
kind load docker-image excel-parser-java:latest
kind load docker-image excel-parser-python:latest
```

**For minikube:**
```bash
minikube image load excel-parser-java:latest
minikube image load excel-parser-python:latest
```

**For other on-premise clusters:**
```bash
cd k8s
chmod +x load-images-to-nodes.sh
./load-images-to-nodes.sh manual
# Follow the instructions printed
```

### 3. Deploy to Kubernetes (1 minute)

```bash
cd k8s

# Deploy everything
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f java-layer-deployment.yaml
kubectl apply -f python-layer-deployment.yaml

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=excel-parser-java -n excel-parser --timeout=300s
kubectl wait --for=condition=ready pod -l app=excel-parser-python -n excel-parser --timeout=300s
```

### 4. Verify Deployment

```bash
# Check everything is running
kubectl get all -n excel-parser

# Should see:
# - 2 pods for java layer (Running)
# - 2 pods for python layer (Running)
# - Services exposed
```

### 5. Access the Service

```bash
# Get your node IP
kubectl get nodes -o wide

# Access endpoints:
# REST API: http://<NODE_IP>:30800
# Flight gRPC: <NODE_IP>:30815

# Test health
curl http://<NODE_IP>:30800/health
```

## Common Issues & Quick Fixes

### Issue: ImagePullBackOff

**Problem:** Kubernetes can't find the Docker images

**Fix:**
```bash
# Edit deployments to use local images
kubectl edit deployment excel-parser-java -n excel-parser
# Change: imagePullPolicy: IfNotPresent to imagePullPolicy: Never

kubectl edit deployment excel-parser-python -n excel-parser
# Change: imagePullPolicy: IfNotPresent to imagePullPolicy: Never
```

### Issue: Python layer CrashLoopBackOff

**Problem:** Python layer can't reach Java layer

**Fix:**
```bash
# Check Java layer is ready first
kubectl get pods -n excel-parser

# Check logs
kubectl logs -l app=excel-parser-python -n excel-parser
```

### Issue: Can't access via NodePort

**Problem:** Firewall or network issue

**Fix:**
```bash
# Use port-forward as temporary solution
kubectl port-forward -n excel-parser svc/excel-parser-service 8000:8000

# Now access at: http://localhost:8000
```

## What Gets Deployed?

- **Namespace:** excel-parser
- **Java Layer:** 2 replicas on port 8080 (internal)
- **Python Layer:** 2 replicas on ports 8000 (REST) and 8815 (gRPC)
- **NodePort Service:** Exposes ports 30800 (REST) and 30815 (gRPC)

## Next Steps

Once deployed:

1. Test the API:
   ```bash
   curl http://<NODE_IP>:30800/health
   ```

2. Upload an Excel file:
   ```bash
   curl -X POST http://<NODE_IP>:30800/parse \
     -F "file=@your-file.xlsx"
   ```

3. Monitor logs:
   ```bash
   kubectl logs -f -l app=excel-parser-python -n excel-parser
   ```

## Need Help?

- Check logs: `kubectl logs -n excel-parser <pod-name>`
- Check events: `kubectl get events -n excel-parser`
- Describe pod: `kubectl describe pod -n excel-parser <pod-name>`
- Full documentation: See DEPLOYMENT.md

## Cleanup

When you're done testing:
```bash
kubectl delete namespace excel-parser
```
