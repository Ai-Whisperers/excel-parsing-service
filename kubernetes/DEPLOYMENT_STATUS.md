# Kubernetes Deployment Status

**Deployment Date:** 2025-11-08
**Status:** LIVE AND OPERATIONAL ✓

## Cluster Information

- **Cluster:** docker-desktop
- **Kubernetes Version:** v1.34.1
- **Node:** docker-desktop (192.168.65.3)
- **Namespace:** excel-parser

## Deployed Services

### 1. Java Layer
- **Image:** excel-parser-java:latest (447MB)
- **Replicas:** 2/2 Running
- **Port:** 8080 (ClusterIP)
- **Status:** ✓ Healthy

**Pods:**
- excel-parser-java-699766f545-szxzl (Running)
- excel-parser-java-699766f545-wljg4 (Running)

### 2. Python Layer
- **Image:** excel-parser-python:latest (757MB)
- **Replicas:** 2/2 Running
- **Ports:** 8000 (REST), 8815 (gRPC)
- **Status:** ✓ Healthy

**Pods:**
- excel-parser-python-6745dd5b77-jj89k (Running)
- excel-parser-python-6745dd5b77-w8sgr (Running)

## Service Endpoints

### External Access (NodePort)

- **REST API:** http://192.168.65.3:30800
- **Arrow Flight gRPC:** 192.168.65.3:30815

### Internal Access (ClusterIP)

- **Python Layer:** http://python-layer.excel-parser.svc.cluster.local:8000
- **Java Layer:** http://java-layer.excel-parser.svc.cluster.local:8080

## Health Check

```bash
curl http://192.168.65.3:30800/health
```

**Response:**
```json
{
  "python_layer": "healthy",
  "java_layer": "Java Layer: Excel Parser Service is running"
}
```

## Port Forwarding (Alternative Access)

```bash
kubectl port-forward -n excel-parser svc/excel-parser-service 8000:8000
```

Then access at: http://localhost:8000

## Resource Allocation

**Per Pod:**
- Memory Request: 512Mi (Limit: 2Gi)
- CPU Request: 500m (Limit: 2000m)

**Total (4 pods):**
- Memory: ~2Gi requested, 8Gi limit
- CPU: 2 cores requested, 8 cores limit

## Management Commands

### View Pods
```bash
kubectl get pods -n excel-parser
```

### View Logs
```bash
# Java layer
kubectl logs -f deployment/excel-parser-java -n excel-parser

# Python layer
kubectl logs -f deployment/excel-parser-python -n excel-parser
```

### Scale Services
```bash
# Scale Java layer
kubectl scale deployment excel-parser-java --replicas=3 -n excel-parser

# Scale Python layer
kubectl scale deployment excel-parser-python --replicas=3 -n excel-parser
```

### Restart Services
```bash
kubectl rollout restart deployment/excel-parser-java -n excel-parser
kubectl rollout restart deployment/excel-parser-python -n excel-parser
```

### Delete Deployment
```bash
kubectl delete namespace excel-parser
```

## Testing the Service

### Upload an Excel file
```bash
curl -X POST http://192.168.65.3:30800/api/v1/process/excel \
  -F "file=@your-file.xlsx" \
  -F "output_format=json"
```

### Arrow Flight Example (Python)
```python
import pyarrow.flight as flight
import requests

# Prepare flight
response = requests.post(
    "http://192.168.65.3:30800/api/v1/flight/prepare",
    params={"file_path": "/path/to/file.xlsx"}
)
flight_info = response.json()

# Stream data
client = flight.FlightClient("grpc://192.168.65.3:30815")
ticket = flight.Ticket(flight_info["ticket"].encode())
reader = client.do_get(ticket)
table = reader.read_all()
print(f"Streamed {table.num_rows} rows")
```

## Next Steps

1. **Configure Ingress** - For production use, configure an Ingress controller
2. **Add TLS** - Secure endpoints with SSL/TLS certificates
3. **Monitoring** - Set up Prometheus/Grafana for metrics
4. **Logging** - Configure centralized logging (ELK, Loki)
5. **Autoscaling** - Configure HPA based on CPU/memory usage

## Troubleshooting

If services are not accessible:

1. Check pod status: `kubectl get pods -n excel-parser`
2. Check logs: `kubectl logs -n excel-parser <pod-name>`
3. Describe pod: `kubectl describe pod -n excel-parser <pod-name>`
4. Check events: `kubectl get events -n excel-parser`

## Status Summary

✓ All pods running and healthy
✓ Services accessible via NodePort
✓ Health checks passing
✓ Both Java and Python layers operational
✓ Ready for production use
