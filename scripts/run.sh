#!/bin/bash

# Load environment variables from .env file
export $(cat .env | xargs)
echo "Running server on HOST:PORT $HOST:$PORT"

cd src/

# Start the FastAPI server in the background
uvicorn app.main:app --host $HOST --port $PORT 
