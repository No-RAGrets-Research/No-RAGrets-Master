#!/bin/bash
# Start the Knowledge Graph API server

cd "$(dirname "$0")"
PYTHONPATH="$(pwd):$PYTHONPATH" ./venv/bin/python -m uvicorn knowledge_graph.api:app --reload --port 8001
