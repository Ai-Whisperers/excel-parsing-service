#!/bin/bash
set -e

NAMESPACE="excel-parser-test"

echo "Creating test namespace..."
kubectl create namespace ${NAMESPACE} || true

echo "Deploying services..."
kubectl apply -f k8s/configmap.yaml -n ${NAMESPACE}
kubectl apply -f k8s/java-layer-deployment.yaml -n ${NAMESPACE}
kubectl apply -f k8s/python-layer-deployment.yaml -n ${NAMESPACE}

echo "Waiting for deployments..."
kubectl wait --for=condition=available --timeout=180s \
  deployment/excel-parser-java -n ${NAMESPACE}
kubectl wait --for=condition=available --timeout=180s \
  deployment/excel-parser-python -n ${NAMESPACE}

echo "Verifying services..."
kubectl get all -n ${NAMESPACE}

echo "Cleanup..."
kubectl delete namespace ${NAMESPACE}

echo "K8s deployment test passed!"
