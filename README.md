# Delivery Status Tracker

A full-stack web application for tracking shipment delivery statuses — built as a take-home assignment for TransVirtual.

> **Vertical slice of real, running software**: PostgreSQL + FastAPI + React, wired end-to-end with CSV data preloaded and ready to click through.


---

## ⏱ Timebox Summary

> **Effort: ~3.5 hours of focused work (2 sessions)** | **Constraint: 3–4 hour timebox, due within 2 days**
>
> *Per the assignment brief: "Stop at the timebox and write down what you would do next — unfinished-but-well-reasoned beats gold-plating."*

### 🕐 Session timeline

| Session | Time (local) | Duration | What happened |
|---|---|---|---|
| **Session 1** | 15:42 → 17:27 | 1h 45m | `Initial commit` → full vertical slice: DB schema, FastAPI backend, React frontend, README + AI usage note |
| **⏸ Pause** | 17:27 → 19:26 | 1h 59m | Stopped at the 3–4h boundary — documented the pause and what I'd do next (`docs: add timebox summary…`) |
| **Session 2** | 19:26 → 21:15 | 1h 49m | Resumed (`docs: continue to complete the project`) → review fixes, Docker Compose, SQL-injection hardening, tests expanded to 36, final polish |

**Total focused effort: ~3h 34m** · Wall-clock span: 15:42 → 21:15 (5h 33m, including pause)

### ✅ Completed within the timebox

| Area | Deliverable | Status |
|---|---|---|
| **Database** | PostgreSQL schema (`shipments` + `status_history`), idempotent CSV seed (20 records) | ✅ Done |
| **Backend** | FastAPI REST API — list, filter, detail, status update, history | ✅ Done |
| **State machine** | Server-side transition validation with 409 on invalid moves | ✅ Done |
| **Frontend** | React UI — filter tabs, inline status updates, detail modal with history timeline | ✅ Done |
| **Testing** | 36 tests (20 state machine + 16 API), all passing | ✅ Done |
| **DB viewer** | Built-in `/db` page for browsing tables and running queries | ✅ Done |
| **Documentation** | README, API reference, architecture notes, AI usage disclosure | ✅ Done |

### 📋 Stopped here — what I'd do next

See [What I'd Do Next](#what-id-do-next) for the prioritized backlog of improvements that were intentionally deferred at the timebox boundary.

---

## Table of Contents

- [⏱ Timebox Summary](#-timebox-summary)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Status Lifecycle](#status-lifecycle)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Frontend](#frontend)
- [Testing](#testing)
- [Key Decisions](#key-decisions)
- [AI Usage Note](#ai-usage-note)
- [What I'd Do Next](#what-id-do-next)

---

## Quick Start

### Option A — Docker Compose (recommended, zero prerequisites)

```bash
git clone https://github.com/YunboZhang037/delivery-status-tracker.git delivery-status-tracker
cd delivery-status-tracker

# One command — spins up PostgreSQL, backend API, and frontend UI
docker compose up
```

That's it. No PostgreSQL, Python, or Node.js installation required — Docker handles everything:
- PostgreSQL 16 on `:5432` (with auto-created `delivery_tracker` database)
- FastAPI backend on `:8000` (auto-seeds 20 CSV records on startup)
- React frontend on `:5173` (built and served via nginx)

Press `Ctrl+C` to stop. Add `--build` to rebuild after code changes.

> **Port note**: Docker maps PostgreSQL to host `:5432`. If you already have PostgreSQL running locally, either stop it first (`brew services stop postgresql` or `pg_ctl stop`) or change the host port in `docker-compose.yml` (e.g. `5433:5432`).

### Option B — Local dev (requires PostgreSQL pre-installed)

```bash
git clone https://github.com/YunboZhang037/delivery-status-tracker.git delivery-status-tracker
cd delivery-status-tracker

# Install dependencies and seed the database (first time only)
make setup

# Start everything — PostgreSQL, backend API, and frontend UI
make dev
```

This runs `scripts/dev.sh`, which starts PostgreSQL, seeds the database, and launches both the backend (`:8000`) and frontend (`:5173`) in parallel. Press `Ctrl+C` to stop all services.

### Option C — Manual startup

#### Prerequisites

| Tool | Version | Notes |
|---|---|---|
| **Python** | 3.12+ | Backend runtime |
| **Node.js** | 18+ | Frontend runtime |
| **PostgreSQL** | 14+ | Database |

#### 1. Start PostgreSQL

```bash
# If PostgreSQL is already running, skip this step
# Otherwise, start it with your preferred method, e.g.:
pg_ctl -D /usr/local/var/postgres start
# or: brew services start postgresql
# or: docker run --name pg -p 5432:5432 -e POSTGRES_HOST_AUTH_METHOD=trust -d postgres:16
```

Create the database:

```bash
createdb delivery_tracker
```

#### 2. Start the Backend API

```bash
cd backend

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Load CSV data into PostgreSQL (idempotent — safe to re-run)
python -m app.seed

# Start the API server
uvicorn app.main:app --reload --port 8000
```

The API is now live at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

#### 3. Start the Frontend UI

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The UI is now live at `http://localhost:5173`. You should see 20 shipments loaded from the CSV, ready to filter, update, and inspect.

> **That's it.** Backend on `:8000`, frontend on `:5173`, 20 shipments ready to click through.

---

## Architecture

```
delivery-status-tracker/
├── docker-compose.yml             # docker compose up — zero-prerequisite single command
├── Makefile                        # make dev / make setup / make test / make seed
├── scripts/
│   └── dev.sh                      # Local dev startup (PostgreSQL + API + UI)
├── backend/
│   ├── Dockerfile                  # Backend container image
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py          # SQLAlchemy engine, session, Base
│   │   ├── models.py            # Shipment + StatusHistory ORM models
│   │   ├── state_machine.py     # Transition rules + validation
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── main.py              # FastAPI routes + /db viewer
│   │   └── seed.py              # CSV → PostgreSQL loader (idempotent)
│   ├── tests/
│   │   ├── test_state_machine.py   # 20 transition validation tests
│   │   └── test_api.py             # 12 API endpoint tests
│   ├── requirements.txt
│   └── shipments.csv            # 20 sample shipments
├── frontend/
│   ├── src/
│   │   ├── main.jsx             # React + QueryClientProvider entry
│   │   ├── App.jsx              # Layout + header
│   │   ├── api/shipments.js     # Axios client + state machine constants
│   │   ├── components/
│   │   │   ├── ShipmentList.jsx        # Table + filter tabs + row click
│   │   │   ├── StatusBadge.jsx         # Colored status pill
│   │   │   ├── StatusUpdateMenu.jsx    # Dropdown (only valid transitions)
│   │   │   └── ShipmentDetailModal.jsx # Detail view + history timeline
│   │   ├── App.css
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── .gitignore
└── README.md
```

**Three layers, clearly separated:**

| Layer | Tech | Responsibility |
|---|---|---|
| **Frontend** | React 19 + Vite + TanStack Query | UI rendering, status updates without page reload |
| **Backend** | FastAPI + SQLAlchemy + Pydantic | Business logic, state machine validation, REST API |
| **Database** | PostgreSQL 16 | Persistent storage for shipments + status history |

---

## Status Lifecycle

```
created ──► picked_up ──► in_transit ──► delivered
   │            │              │
   └────────────┴──────────────┴──► failed
```

| Current Status | Allowed Next States |
|---|---|
| `created` | `picked_up`, `failed` |
| `picked_up` | `in_transit`, `failed` |
| `in_transit` | `delivered`, `failed` |
| `delivered` | *(terminal — no transitions)* |
| `failed` | *(terminal — no transitions)* |

- **`delivered`** and **`failed`** are terminal states — no further transitions are allowed.
- Invalid transitions are rejected with **HTTP 409 Conflict** and a clear error message listing the allowed next states.
- The state machine is enforced **server-side** in `state_machine.py` and mirrored **client-side** in `api/shipments.js` so the UI only offers valid actions.

---

## API Reference

Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/shipments` | List all shipments (20 records) |
| `GET` | `/api/shipments?status=delivered` | Filter shipments by status |
| `GET` | `/api/shipments/{reference}` | Get a single shipment with full status history |
| `PATCH` | `/api/shipments/{reference}/status` | Update a shipment's status (optional `note` field) |
| `GET` | `/api/shipments/{reference}/history` | Get the full status-change history |
| `GET` | `/db` | Visual database browser (HTML page) |
| `GET` | `/api/db/tables` | List all tables with row counts |
| `GET` | `/api/db/tables/{table}/structure` | Get column definitions for a table |
| `GET` | `/api/db/tables/{table}/data` | Get all rows from a table |
| `POST` | `/api/db/query?query=SELECT...` | Run a read-only SQL query |

### Example: Update Status

```bash
# Valid transition: created → picked_up
curl -X PATCH http://localhost:8000/api/shipments/TV-1002/status \
  -H "Content-Type: application/json" \
  -d '{"status": "picked_up"}'

# Response: 200 OK
{"id": 2, "reference": "TV-1002", "customer_name": "...", "status": "picked_up", ...}
```

```bash
# With an optional note (e.g., for failed deliveries)
curl -X PATCH http://localhost:8000/api/shipments/TV-1002/status \
  -H "Content-Type: application/json" \
  -d '{"status": "failed", "note": "Customer not available for pickup"}'
```

```bash
# Invalid transition: picked_up → delivered (skips in_transit)
curl -X PATCH http://localhost:8000/api/shipments/TV-1002/status \
  -H "Content-Type: application/json" \
  -d '{"status": "delivered"}'

# Response: 409 Conflict
{"detail": "Cannot transition from 'picked_up' to 'delivered'. Allowed transitions from 'picked_up': ['in_transit', 'failed']."}
```

Interactive Swagger docs available at `http://localhost:8000/docs`.

---

## Database Schema

### `shipments` — Main table

| Column | Type | Constraints |
|---|---|---|
| `id` | `INTEGER` | Primary key, auto-increment |
| `reference` | `VARCHAR(50)` | Unique, not null, indexed |
| `customer_name` | `VARCHAR(200)` | Not null |
| `status` | `VARCHAR(20)` | Not null, default `'created'`, indexed |
| `created_at` | `TIMESTAMP` | Not null, default `now()` |
| `updated_at` | `TIMESTAMP` | Not null, auto-updated on change |

### `status_history` — Change audit log

| Column | Type | Constraints |
|---|---|---|
| `id` | `INTEGER` | Primary key, auto-increment |
| `shipment_id` | `INTEGER` | Foreign key → `shipments.id`, cascade delete |
| `previous_status` | `VARCHAR(20)` | Nullable (null for initial state) |
| `new_status` | `VARCHAR(20)` | Not null |
| `changed_at` | `TIMESTAMP` | Not null, default `now()` |
| `note` | `TEXT` | Nullable |

Every status update atomically writes a `status_history` record and updates the `shipments` row in a single transaction.

---

## Frontend

### Features

| Feature | How it works |
|---|---|
| **Status filter tabs** | Tabs for All / Created / Picked Up / In Transit / Delivered / Failed, each with a live count badge |
| **Shipment table** | Reference, customer name, status badge, timestamps, and an action dropdown per row |
| **Inline status update** | Dropdown shows only valid next states (driven by the same state machine as the backend) |
| **No page reload** | TanStack Query automatically invalidates and refetches after a mutation — the list updates instantly |
| **Detail modal** | Click any row to see full shipment info + a visual status history timeline |
| **Error toasts** | Invalid transitions and network errors surface as dismissible toast notifications |
| **Responsive** | Table adapts for mobile — secondary columns hidden on narrow screens |

### Tech Choices

| Library | Why |
|---|---|
| **Vite** | Fast HMR, zero-config React setup |
| **TanStack Query** | Server-state management — caching, invalidation, and optimistic updates handled declaratively |
| **Axios** | Simple, well-understood HTTP client |

---

## Testing

```bash
# From the project root
make test

# Or manually:
cd backend
source .venv/bin/activate
python -m pytest tests/ -v
```

**36 tests, all passing:**

| Test File | Tests | Coverage |
|---|---|---|
| `test_state_machine.py` | 20 | All valid transitions, all invalid transitions (skip steps, backwards, terminal states), error message quality, unknown status handling |
| `test_api.py` | 16 | Empty list, list with data, filter by status, get single shipment (200 + 404), valid update, invalid update (409), terminal state (409), not found (404), history recorded, note recorded, note optional, unknown status → 422 (regression), non-string status → 422, missing status field → 422 |

API tests use an in-memory SQLite database with FastAPI's `TestClient` — no external dependencies, fast execution.

---

## Key Decisions

### 1. State machine in a dedicated module — not inline in routes

**Decision**: Extracted transition rules into `state_machine.py` with a single `validate_transition()` function.

**Why**: The state machine is the core business logic. Keeping it isolated means it's testable in isolation, reusable across endpoints, and impossible to accidentally bypass. The API layer just calls `validate_transition()` and translates exceptions to HTTP status codes.

### 2. Status history table from day one

**Decision**: Designed `status_history` alongside `shipments` even though history is a stretch goal.

**Why**: Adding audit logging retroactively means data loss for changes that already happened. A nullable `previous_status` column costs nothing and makes the history view trivial to implement. Every `PATCH` writes the history record in the same transaction as the status update.

### 3. TanStack Query over manual state management

**Decision**: Used TanStack Query instead of `useEffect` + `useState` for data fetching.

**Why**: The requirement says "changes visible without a full page reload." TanStack Query handles this declaratively — after a successful mutation, we invalidate the shipments query and the list refetches automatically. No manual cache management, no stale state bugs.

### 4. In-memory SQLite for tests, PostgreSQL for the app

**Decision**: Tests run against in-memory SQLite; the app runs against PostgreSQL.

**Why**: Tests should be fast and dependency-free. SQLAlchemy's ORM abstraction makes the switch transparent — the same models work with both engines. The test suite runs in under a second with zero external services.

### 5. CSV seed script is idempotent

**Decision**: `seed.py` checks for existing records by `reference` before inserting.

**Why**: The demo should be re-runnable without producing duplicate data. Running `python -m app.seed` twice inserts 20 records the first time and skips all 20 the second time, with a clear log message.

---

## AI Usage Note

**Tools used**: GLM-5.2 (via WorkBuddy, an AI coding agent built on Zhipu AI's GLM model) for code generation, refactoring, and test writing. The developer directed all architectural decisions, reviewed every line of AI output, and caught multiple issues through iterative review.

### What AI generated vs. what the developer did

| Area | AI-Generated | Developer |
|---|---|---|
| Project scaffolding & file structure | ✅ | Designed architecture; caught and removed leftover Vite template assets |
| SQLAlchemy models, schemas, state machine | ✅ | Verified state transitions against PDF spec; caught `datetime.utcnow()` deprecation |
| FastAPI routes and seed script | ✅ | Identified SQL injection risk in `/api/db/query`; directed 4-layer defense |
| React components and API client | ✅ | Flagged `window.prompt()` as poor UX; caught filter badge disappearing bug |
| Test suite (36 tests) | ✅ | Found missing GET single-shipment tests; caught test count mismatch in README |
| Docker Compose setup | ✅ | Pointed out `make dev` wasn't truly single-command; directed Docker approach |
| README & documentation | ✅ | Cross-checked against assignment PDF 3 times; caught multiple inaccuracies |
| DB viewer UI polish | ✅ | Flagged raw `nextval()` display as confusing; directed auto-increment badge |
| Architecture & tooling decisions | Partial | Chose the full stack (PostgreSQL + FastAPI + React/Vite); AI executed |
| PyCharm venv configuration | Partial | Verified config; debugged venv path breakage after directory move |

### One thing AI got wrong — and how I caught it

**SQL injection protection was too shallow**: The AI built a `/api/db/query` endpoint that let users run raw SQL on the database. Its only defense was checking that the query started with `SELECT`. I pointed out this wasn't enough — a crafted query like `SELECT 1; DROP TABLE shipments` could still slip through. I directed the AI to add three more layers: reject queries containing semicolons, block dangerous keywords (DROP, INSERT, UPDATE, DELETE, etc.), and wrap every query in a `BEGIN READ ONLY` transaction so even if all else fails, no writes can happen.

**Lesson**: A single validation check is never sufficient for user-facing SQL. Layer your defenses so each layer catches what the previous one misses.

---

## What I'd Do Next

> **Stopped at the 3–4 hour timebox.** The items below are intentionally deferred — not missing. Each is prioritized by impact and scoped so a reviewer can see the reasoning.

### Priority 1 — Deployment & CI

1. **CI pipeline** — GitHub Actions workflow that runs the 32-test suite on every push, ensuring the repo is always in a green state.

### Priority 2 — Production readiness

2. **Pagination** — The list endpoint currently returns all 20 records. For a real product, server-side pagination with cursor-based navigation would be essential.
3. **Input validation hardening** — Server-side validation for customer name length, reference format patterns, and rate limiting on the update endpoint.
4. **Authentication & authorization** — Role-based access (e.g., operators can update status, viewers can only read). Currently all endpoints are open.
5. **Structured logging & error tracking** — Replace print-style debugging with proper logging (structlog/loguru) and integrate Sentry for error monitoring.

### Priority 3 — UX polish

6. **Optimistic updates** — Show the new status immediately in the UI before the server confirms, with rollback on error.
7. **Frontend testing** — Vitest + React Testing Library tests for component rendering, filter behavior, and mutation flows.
8. **WebSocket notifications** — Push status changes to all connected clients in real time, so multiple operators see updates without refreshing.

### What I intentionally did NOT do (and why)

| Skipped | Reason |
|---|---|
| User auth | Out of scope for the assignment brief; would add complexity without demonstrating the core state machine |
| Pagination | 20 records don't warrant it; would add premature complexity |
| i18n / a11y audit | Important for production, but the assignment focuses on the status tracking vertical slice |
