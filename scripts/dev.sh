#!/bin/bash
# scripts/dev.sh — Start backend + frontend with a single command.
# Usage: make dev  (or: bash scripts/dev.sh)
set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo ""
echo "=============================================="
echo "  Delivery Status Tracker — Starting"
echo "=============================================="
echo ""

# ── 1. Ensure PostgreSQL is running ──────────────────────
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    PG_CTL="$HOME/postgresql/pg_ctl.sh"
    if [ -f "$PG_CTL" ]; then
        echo "[1/4] Starting PostgreSQL..."
        bash "$PG_CTL" start
    else
        echo "[1/4] PostgreSQL not running and pg_ctl.sh not found."
        echo "      Start PostgreSQL manually, then re-run this script."
        exit 1
    fi
else
    echo "[1/4] PostgreSQL is already running."
fi

# ── 2. Ensure database exists ────────────────────────────
if ! psql -h localhost -p 5432 -U postgres -lqt 2>/dev/null | grep -qw delivery_tracker; then
    echo "[2/4] Creating database 'delivery_tracker'..."
    createdb -h localhost -p 5432 -U postgres delivery_tracker
else
    echo "[2/4] Database 'delivery_tracker' exists."
fi

# ── 3. Start backend ─────────────────────────────────────
echo "[3/4] Starting backend (port 8000)..."
cd "$ROOT_DIR/backend"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi
python -m app.seed
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd "$ROOT_DIR"

# ── 4. Start frontend ────────────────────────────────────
echo "[4/4] Starting frontend (port 5173)..."
cd "$ROOT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run dev &
FRONTEND_PID=$!
cd "$ROOT_DIR"

# ── Cleanup on exit ──────────────────────────────────────
cleanup() {
    echo ""
    echo "Shutting down..."
    kill "$BACKEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
    wait 2>/dev/null
    echo "Done."
}
trap cleanup EXIT INT TERM

echo ""
echo "=============================================="
echo "  Ready!"
echo "  Backend API:  http://localhost:8000"
echo "  API docs:     http://localhost:8000/docs"
echo "  DB viewer:    http://localhost:8000/db"
echo "  Frontend UI:  http://localhost:5173"
echo "=============================================="
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

wait
