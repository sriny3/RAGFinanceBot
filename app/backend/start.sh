#!/bin/bash

# Ensure we are in the correct directory if started from root
# Hugging Face Spaces / Docker SDK starts from the root of the deployment
if [ -d "app/backend" ]; then
    cd app/backend
fi

# Start the application with gunicorn + uvicorn worker
# Default to port 8000 if $PORT is not set (standard for local/HF)
PORT_NUMBER=${PORT:-8000}

echo "Starting FinBot Backend on port $PORT_NUMBER..."

exec gunicorn main:app \
    --bind 0.0.0.0:$PORT_NUMBER \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 600
