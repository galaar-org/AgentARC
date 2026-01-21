#!/bin/bash

# Start the custom FastAPI server with event streaming
cd "$(dirname "$0")"

echo "Starting CDP Agent API server with PolicyLayer event streaming..."
echo "API will be available at http://localhost:2024"
echo "API docs: http://localhost:2024/docs"
echo ""

# Use asyncio loop instead of uvloop (required for nest_asyncio compatibility)
poetry run uvicorn server:app --reload --host 0.0.0.0 --port 2024 --loop asyncio
