#!/bin/bash

# Build User Service Docker image
set -e

echo "Building User Service Docker image..."
docker build -t notebookum-user-service:latest -f Dockerfile .
echo "Build completed successfully!"
