#!/bin/bash

# CarbonBridge Knowledge Graph Pipeline Startup Script
# ====================================================

set -e  # Exit on any error

echo "Starting CarbonBridge Knowledge Graph Pipeline..."
echo "================================================"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[OK] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

print_info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Function to check if port is in use
is_port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Step 1: Activate Virtual Environment
print_info "Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    print_status "Virtual environment activated"
else
    print_error "Virtual environment not found at venv/bin/activate"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Step 2: Check and Install Dependencies
print_info "Checking Python dependencies..."
if python -c "import fastapi, uvicorn, spacy" 2>/dev/null; then
    print_status "Python dependencies available"
else
    print_warning "Installing missing dependencies..."
    pip install -r requirements.txt
fi

# Step 3: Start Dgraph Database
print_info "Starting Dgraph database..."
cd knowledge_graph

if is_port_in_use 8080; then
    print_status "Dgraph appears to be running on port 8080"
else
    print_info "Starting Dgraph with Docker Compose..."
    docker compose up -d
    
    # Wait for Dgraph to be ready
    print_info "Waiting for Dgraph to be ready..."
    timeout=60
    count=0
    while [ $count -lt $timeout ]; do
        if curl -s http://localhost:8080/health >/dev/null 2>&1; then
            print_status "Dgraph is ready"
            break
        fi
        sleep 2
        count=$((count + 2))
        echo -n "."
    done
    
    if [ $count -ge $timeout ]; then
        print_error "Dgraph failed to start within $timeout seconds"
        exit 1
    fi
fi

# Step 4: Update Dgraph Schema
print_info "Updating Dgraph schema..."
python -c "
from dgraph_manager import DgraphManager
dm = DgraphManager()
result = dm.load_schema('schema.graphql')
print('Schema updated:', result)
"

if [ $? -eq 0 ]; then
    print_status "Schema updated successfully"
else
    print_warning "Schema update had issues, but continuing..."
fi

# Step 5: Start API Server with Auto Port Detection
print_info "Starting API server with automatic port detection..."

# Check port availability and start API
if is_port_in_use 8000; then
    print_warning "Port 8000 in use (Dgraph Ratel), using port 8001 for API"
    API_PORT=8001
else
    API_PORT=8000
fi

# Find next available port if needed
while is_port_in_use $API_PORT; do
    print_warning "Port $API_PORT in use, trying $((API_PORT + 1))"
    API_PORT=$((API_PORT + 1))
done

print_info "Starting FastAPI server on port $API_PORT..."

# Start API in background
python -c "
import uvicorn
from api import app
import sys

port = $API_PORT
print(f'Starting Knowledge Graph API on http://localhost:{port}')
print(f'API Documentation: http://localhost:{port}/docs')
print(f'Interactive Query: http://localhost:{port}/redoc')

try:
    uvicorn.run('api:app', host='0.0.0.0', port=port, reload=True)
except KeyboardInterrupt:
    print('\\nAPI server stopped')
except Exception as e:
    print(f'Error starting API: {e}')
    sys.exit(1)
" &

API_PID=$!

# Wait for API to start properly
sleep 8

# Step 6: Verify Everything is Running
print_info "Verifying services..."

# Check Dgraph
if curl -s http://localhost:8080/health >/dev/null; then
    print_status "Dgraph database: http://localhost:8080 (healthy)"
else
    print_error "Dgraph database: not responding"
fi

# Check Dgraph UI (Ratel)
if is_port_in_use 8000; then
    print_status "Dgraph UI (Ratel): http://localhost:8000"
fi

# Check API with retries
print_info "Checking API health (with retries)..."
api_ready=false
for i in {1..5}; do
    if curl -s http://localhost:$API_PORT/api/health >/dev/null 2>&1; then
        print_status "Knowledge Graph API: http://localhost:$API_PORT (healthy)"
        api_ready=true
        break
    else
        print_info "API not ready yet, attempt $i/5..."
        sleep 2
    fi
done

if [ "$api_ready" = true ]; then
    # Test the source span endpoint
    print_info "Testing API endpoints..."
    if curl -s "http://localhost:$API_PORT/api/relations/search?limit=1" > /tmp/test_relations.json 2>/dev/null; then
        if [ -s /tmp/test_relations.json ]; then
            print_status "API endpoints responding correctly"
        else
            print_warning "API responding but no data found (database may be empty)"
        fi
    else
        print_warning "API health OK but endpoints may need data"
    fi
else
    print_error "Knowledge Graph API: not responding after retries"
fi

echo ""
echo "CarbonBridge Knowledge Graph Pipeline Status:"
echo "============================================="
echo "Dgraph Database: http://localhost:8080"
echo "Dgraph UI: http://localhost:8000"
echo "Knowledge Graph API: http://localhost:$API_PORT"
echo "API Documentation: http://localhost:$API_PORT/docs"
echo "Source Span Endpoint: http://localhost:$API_PORT/api/relations/{id}/source-span"
echo ""
echo "Quick test commands:"
echo "curl http://localhost:$API_PORT/api/health"
echo "curl http://localhost:$API_PORT/api/relations/search?limit=3"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep script running and handle cleanup
cleanup() {
    echo ""
    print_info "Shutting down services..."
    kill $API_PID 2>/dev/null || true
    cd "$SCRIPT_DIR/knowledge_graph"
    docker compose down
    print_status "All services stopped"
}

trap cleanup EXIT INT TERM

# Wait for API process
wait $API_PID