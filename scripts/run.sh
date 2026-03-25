#!/bin/bash

# Load environment variables from .env file if it exists (local dev only)
if [ -f .env ]; then
  export $(cat .env | xargs)
fi
echo "Running server on HOST:PORT $HOST:$PORT"

cd src/

# Start the FastAPI server in the background
uvicorn app.main:app --host $HOST --port $PORT 
