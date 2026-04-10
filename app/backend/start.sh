#!/bin/bash

# Ensure we are in the correct directory if started from root
# Hugging Face Spaces / Docker SDK starts from the root of the deployment
if [ -d "app/backend" ]; then
    cd app/backend
fi

# Start the application with uvicorn directly
# Direct uvicorn is more stable for OpenTelemetry in single-worker environments
PORT_NUMBER=${PORT:-8000}

echo "Starting FinBot Backend on port $PORT_NUMBER..."

exec uvicorn main:app \
    --host 0.0.0.0 \
    --port $PORT_NUMBER \
    --log-level info \
    --timeout-keep-alive 600
