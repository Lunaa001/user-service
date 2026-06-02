#!/bin/bash

# Run User Service in development mode with hot reload
set -e

echo "Starting User Service in development mode..."
echo "Hot reload enabled - changes will be reflected immediately"
echo "API docs at: http://localhost:8001/docs"

uvicorn main:app --host 0.0.0.0 --port 8001 --reload
