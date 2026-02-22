#!/bin/bash
# EvoSwarm Launcher (Git Bash / WSL)

set -e

echo "============================================"
echo "  EvoSwarm - Self-Evolving Agent Collective"
echo "============================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker not found. Install Docker Desktop first."
    exit 1
fi

# Start Neo4j
echo "[1/3] Starting Neo4j via Docker..."
docker compose up -d neo4j

# Wait for Neo4j health
echo "[*] Waiting for Neo4j to be ready..."
until docker inspect --format='{{.State.Health.Status}}' evoswarm-neo4j 2>/dev/null | grep -q "healthy"; do
    sleep 3
done
echo "[OK] Neo4j is healthy."

# Start Backend
echo ""
echo "[2/3] Starting Backend (uvicorn)..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

sleep 3

# Start Frontend
echo ""
echo "[3/3] Starting Frontend (Next.js)..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

echo ""
echo "============================================"
echo "  EvoSwarm is running!"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  Neo4j:    http://localhost:7474"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop all services..."

# Cleanup on exit
cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    docker compose down
    echo "Done."
}
trap cleanup EXIT INT TERM

# Wait for processes
wait
