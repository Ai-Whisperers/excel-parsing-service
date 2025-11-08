#!/bin/bash

# Script to load Docker images to Kubernetes nodes
# Usage: ./load-images-to-nodes.sh [method]
# Methods: kind, minikube, manual

set -e

METHOD=${1:-"manual"}

echo "Loading images to Kubernetes nodes using method: $METHOD"

case $METHOD in
  kind)
    echo "Loading images to kind cluster..."
    kind load docker-image excel-parser-java:latest
    kind load docker-image excel-parser-python:latest
    echo "Images loaded successfully!"
    ;;

  minikube)
    echo "Loading images to minikube..."
    minikube image load excel-parser-java:latest
    minikube image load excel-parser-python:latest
    echo "Images loaded successfully!"
    ;;

  manual)
    echo "Saving images to tar files..."
    docker save excel-parser-java:latest | gzip > excel-parser-java.tar.gz
    docker save excel-parser-python:latest | gzip > excel-parser-python.tar.gz

    echo ""
    echo "Images saved!"
    echo "Now copy these files to each Kubernetes node and load them:"
    echo ""
    echo "  scp excel-parser-*.tar.gz user@node:/tmp/"
    echo "  ssh user@node 'docker load < /tmp/excel-parser-java.tar.gz'"
    echo "  ssh user@node 'docker load < /tmp/excel-parser-python.tar.gz'"
    echo ""
    ;;

  *)
    echo "Unknown method: $METHOD"
    echo "Usage: $0 [kind|minikube|manual]"
    exit 1
    ;;
esac
