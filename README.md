# Delivery Status Tracker

A full-stack web application for tracking shipment delivery statuses — built as a take-home assignment for TransVirtual.

> **Vertical slice of real, running software**: PostgreSQL + FastAPI + React, wired end-to-end with CSV data preloaded and ready to click through.

---

## Table of Contents

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

### Prerequisites

| Tool | Version | Notes |
|---|---|---|
| **Python** | 3.12+ | Backend runtime |
| **Node.js** | 18+ | Frontend runtime |
| **PostgreSQL** | 14+ | Database |

### 1. Start PostgreSQL

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

### 2. Start the Backend API

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

### 3. Start the Frontend UI

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
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py          # SQLAlchemy engine, session, Base
│   │   ├── models.py            # Shipment + StatusHistory ORM models
│   │   ├── state_machine.py     # Transition rules + validation
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── main.py              # FastAPI routes (list, filter, update, history)
│   │   └── seed.py              # CSV → PostgreSQL loader (idempotent)
│   ├── tests/
│   │   ├── test_state_machine.py   # 16 transition validation tests
│   │   └── test_api.py             # 8 API endpoint tests
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
| `PATCH` | `/api/shipments/{reference}/status` | Update a shipment's status |
| `GET` | `/api/shipments/{reference}/history` | Get the full status-change history |

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
cd backend
source .venv/bin/activate
python -m pytest tests/ -v
```

**28 tests, all passing:**

| Test File | Tests | Coverage |
|---|---|---|
| `test_state_machine.py` | 16 | All valid transitions, all invalid transitions (skip steps, backwards, terminal states), error message quality, unknown status handling |
| `test_api.py` | 8 | Empty list, list with data, filter by status, valid update, invalid update (409), terminal state (409), not found (404), history recorded on update |

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

**Tools used**: Claude (via WorkBuddy) for code generation, refactoring, and test writing.

### What AI generated vs. hand-written

| Area | AI-Generated | Human |
|---|---|---|
| Project scaffolding & file structure | ✅ | Reviewed and adjusted |
| SQLAlchemy models, schemas, state machine | ✅ | Reviewed logic against requirements |
| FastAPI routes and seed script | ✅ | Verified against API spec |
| React components and API client | ✅ | Reviewed UX flow |
| Test suite (28 tests) | ✅ | Reviewed coverage, added edge cases |
| README | ✅ | Edited for accuracy |
| Architecture & tooling decisions | Partial | Human chose the stack; AI executed |
| PyCharm venv configuration | Partial | AI modified config files; human verified |

### One thing AI got wrong — and how I caught it

**Virtual environment path breakage**: After moving the project directory from one location to another, the Python virtual environment's `bin/` scripts had hardcoded shebangs pointing to the old path. The AI attempted to start the backend with the broken venv, producing confusing `bad interpreter` errors. I caught this by checking the actual shebang lines in `.venv/bin/uvicorn` and resolved it by recreating the venv from scratch with `python3 -m venv .venv` and reinstalling dependencies.

**Lesson**: Virtual environments are not portable across directory moves. Always recreate after relocating a project.

---

## What I'd Do Next

Given more time beyond the 3–4 hour timebox, here's what I'd prioritize:

1. **Docker Compose for single-command startup** — `docker compose up` spins up PostgreSQL, API, and UI with CSV auto-seeded. This is the highest-impact addition for demo reliability.
2. **Frontend testing** — Add Vitest + React Testing Library tests for component rendering, filter behavior, and mutation flows.
3. **Pagination** — The list endpoint currently returns all records. For a real product, server-side pagination with cursor-based navigation would be essential.
4. **Optimistic updates** — Show the new status immediately in the UI before the server confirms, with rollback on error.
5. **Status transition notes** — The `status_history.note` column exists but isn't exposed in the UI. Adding an optional "reason" field on failed transitions would be valuable for operations teams.
6. **WebSocket notifications** — Push status changes to all connected clients in real time, so multiple operators see updates without refreshing.
7. **Input validation hardening** — Add server-side validation for customer name length, reference format patterns, and rate limiting on the update endpoint.
