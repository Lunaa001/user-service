#!/bin/bash

# Run User Service with docker-compose
set -e

echo "Starting User Service..."
docker-compose up -d

echo "User Service is running!"
echo "Check health at: http://localhost:8001/health"
echo "API docs at: http://localhost:8001/docs"
