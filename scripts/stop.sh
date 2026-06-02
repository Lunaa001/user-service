#!/bin/bash

# Stop User Service
set -e

echo "Stopping User Service..."
docker-compose down

echo "User Service stopped successfully!"
