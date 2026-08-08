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
    echo "[1/4] PostgreSQL not running. Attempting to start..."

    # Try common methods in order of likelihood
    if command -v brew >/dev/null 2>&1 && brew services list 2>/dev/null | grep -q postgresql; then
        brew services start postgresql
    elif [ -f "$HOME/postgresql/pg_ctl.sh" ]; then
        bash "$HOME/postgresql/pg_ctl.sh" start
    elif command -v pg_ctl >/dev/null 2>&1; then
        PGDATA="${PGDATA:-/usr/local/var/postgres}"
        pg_ctl -D "$PGDATA" start
    elif command -v docker >/dev/null 2>&1; then
        docker start postgres 2>/dev/null || \
            docker run --name postgres -p 5432:5432 -e POSTGRES_HOST_AUTH_METHOD=trust -d postgres:16
    else
        echo "      Could not auto-start PostgreSQL."
        echo "      Please start PostgreSQL manually, then re-run this script."
        echo "      Common methods:"
        echo "        brew services start postgresql"
        echo "        pg_ctl -D /usr/local/var/postgres start"
        echo "        docker run --name pg -p 5432:5432 -e POSTGRES_HOST_AUTH_METHOD=trust -d postgres:16"
        exit 1
    fi

    # Wait for PostgreSQL to be ready
    for i in $(seq 1 10); do
        if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
            echo "      PostgreSQL is now running."
            break
        fi
        sleep 1
    done

    if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
        echo "      PostgreSQL failed to start within 10 seconds."
        echo "      Please start it manually, then re-run this script."
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
