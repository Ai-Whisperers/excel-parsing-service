# Kubernetes Deployment Guide

This guide explains how to deploy the Excel POI Parser service to your on-premise Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (v1.20+) running and accessible
- `kubectl` configured to access your cluster
- Docker installed for building images
- Access to push images to your cluster nodes or private registry

## Architecture

The service consists of two layers:

1. **Java Layer** (Port 8080): Excel parsing using Apache POI
2. **Python Layer** (Ports 8000, 8815): REST API and Arrow Flight gRPC server

## Quick Deployment

### Option 1: Using the deployment script (Linux/Mac)

```bash
cd k8s
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual deployment

#### Step 1: Build Docker Images

```bash
# Build Java layer
cd java-layer
docker build -t excel-parser-java:latest .

# Build Python layer
cd ../python-layer
docker build -t excel-parser-python:latest .
```

#### Step 2: Load images to Kubernetes nodes

For on-premise clusters, you need to make the images available to your nodes:

**Option A: Using a private registry**
```bash
# Tag images
docker tag excel-parser-java:latest your-registry.com/excel-parser-java:latest
docker tag excel-parser-python:latest your-registry.com/excel-parser-python:latest

# Push to registry
docker push your-registry.com/excel-parser-java:latest
docker push your-registry.com/excel-parser-python:latest

# Update image names in deployment files
# Edit k8s/java-layer-deployment.yaml and k8s/python-layer-deployment.yaml
# Replace "excel-parser-java:latest" with "your-registry.com/excel-parser-java:latest"
```

**Option B: Saving and loading images manually (for small clusters)**
```bash
# Save images
docker save excel-parser-java:latest | gzip > excel-parser-java.tar.gz
docker save excel-parser-python:latest | gzip > excel-parser-python.tar.gz

# Copy to each node and load
scp excel-parser-*.tar.gz node1:/tmp/
ssh node1 'docker load < /tmp/excel-parser-java.tar.gz'
ssh node1 'docker load < /tmp/excel-parser-python.tar.gz'
# Repeat for all nodes
```

**Option C: Using kind/minikube**
```bash
# For kind
kind load docker-image excel-parser-java:latest
kind load docker-image excel-parser-python:latest

# For minikube
minikube image load excel-parser-java:latest
minikube image load excel-parser-python:latest
```

#### Step 3: Deploy to Kubernetes

```bash
cd k8s

# Apply all manifests
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f java-layer-deployment.yaml
kubectl apply -f python-layer-deployment.yaml
```

**Or using kustomize:**
```bash
kubectl apply -k .
```

#### Step 4: Verify deployment

```bash
# Check pods
kubectl get pods -n excel-parser

# Check services
kubectl get services -n excel-parser

# Check logs
kubectl logs -f deployment/excel-parser-java -n excel-parser
kubectl logs -f deployment/excel-parser-python -n excel-parser
```

## Accessing the Service

The service is exposed using NodePort on:
- **REST API**: `http://<node-ip>:30800`
- **Arrow Flight gRPC**: `<node-ip>:30815`

To get your node IP:
```bash
kubectl get nodes -o wide
```

### Testing the deployment

```bash
# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Test health endpoint
curl http://$NODE_IP:30800/health

# Test Java layer health
kubectl port-forward -n excel-parser svc/java-layer 8080:8080
curl http://localhost:8080/api/v1/excel/health
```

## Configuration

Configuration is managed through ConfigMap at `k8s/configmap.yaml`. To update:

```bash
# Edit configmap
kubectl edit configmap excel-parser-config -n excel-parser

# Restart deployments to pick up changes
kubectl rollout restart deployment/excel-parser-java -n excel-parser
kubectl rollout restart deployment/excel-parser-python -n excel-parser
```

## Scaling

To scale the deployments:

```bash
# Scale Java layer
kubectl scale deployment excel-parser-java --replicas=3 -n excel-parser

# Scale Python layer
kubectl scale deployment excel-parser-python --replicas=3 -n excel-parser
```

## Resource Requirements

Each pod requests:
- Memory: 512Mi (limit: 2Gi)
- CPU: 500m (limit: 2000m)

For 2 replicas of each service, you need:
- Total memory: ~4Gi available
- Total CPU: ~4 cores available

## Monitoring

```bash
# Watch pods
kubectl get pods -n excel-parser -w

# View logs
kubectl logs -f deployment/excel-parser-python -n excel-parser
kubectl logs -f deployment/excel-parser-java -n excel-parser

# Describe pod for troubleshooting
kubectl describe pod <pod-name> -n excel-parser

# Check events
kubectl get events -n excel-parser --sort-by='.lastTimestamp'
```

## Troubleshooting

### Pods not starting (ImagePullBackOff)

This means Kubernetes can't pull the image. Solutions:
1. Ensure images are loaded on all nodes
2. Set `imagePullPolicy: Never` in deployments if using local images
3. Configure proper registry credentials if using private registry

Edit the deployment:
```bash
kubectl edit deployment excel-parser-java -n excel-parser
# Change imagePullPolicy to "Never" or "IfNotPresent"
```

### Python layer CrashLoopBackOff

Check if Java layer is ready:
```bash
kubectl get pods -n excel-parser
kubectl logs deployment/excel-parser-python -n excel-parser
```

### Service not accessible

1. Check NodePort is open on firewall
2. Verify services are running: `kubectl get svc -n excel-parser`
3. Check pod status: `kubectl get pods -n excel-parser`

## Cleanup

To remove the deployment:

```bash
kubectl delete namespace excel-parser
```

Or delete individual resources:
```bash
kubectl delete -f k8s/python-layer-deployment.yaml
kubectl delete -f k8s/java-layer-deployment.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/namespace.yaml
```

## Production Considerations

For production deployments, consider:

1. **Ingress Controller**: Replace NodePort with an Ingress for proper routing
2. **TLS/SSL**: Add certificates for secure communication
3. **Persistent Storage**: Add PVCs if you need to persist data
4. **Resource Limits**: Adjust based on actual usage patterns
5. **Monitoring**: Set up Prometheus/Grafana for metrics
6. **Logging**: Configure centralized logging (ELK, Loki, etc.)
7. **Secrets Management**: Move sensitive config to Kubernetes Secrets
8. **Network Policies**: Restrict pod-to-pod communication
9. **Pod Disruption Budgets**: Ensure availability during updates
10. **HPA**: Configure Horizontal Pod Autoscaling based on CPU/memory

## Support

For issues or questions, check the logs and events:
```bash
kubectl logs -n excel-parser deployment/excel-parser-python --tail=100
kubectl get events -n excel-parser
```
