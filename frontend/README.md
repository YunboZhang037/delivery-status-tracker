# Frontend — Delivery Status Tracker

React UI for tracking shipment delivery statuses, built with Vite + TanStack Query.

## Quick Start

```bash
# From project root
make dev    # starts backend + frontend together

# Or standalone
cd frontend
npm install
npm run dev
```

The UI runs on `http://localhost:5173` and proxies `/api` requests to the backend on port 8000.

## Features

- **Filter tabs** — All / Created / Picked Up / In Transit / Delivered / Failed, each with live count badges
- **Inline status updates** — Dropdown shows only valid next states (same state machine as backend)
- **No page reload** — TanStack Query auto-refetches after mutations
- **Detail modal** — Click any row to see full shipment info + status history timeline
- **Error toasts** — Invalid transitions and network errors shown as dismissible notifications

## Tech Stack

| Library | Purpose |
|---|---|
| Vite | Build tool + dev server with HMR |
| React 19 | UI framework |
| TanStack Query | Server-state management (caching, invalidation) |
| Axios | HTTP client |

## Project Structure

```
frontend/src/
├── main.jsx                          # Entry point + QueryClientProvider
├── App.jsx                           # Layout + header
├── api/shipments.js                  # Axios client + state machine constants
├── components/
│   ├── ShipmentList.jsx              # Table + filter tabs + row click
│   ├── StatusBadge.jsx               # Colored status pill
│   ├── StatusUpdateMenu.jsx          # Dropdown (only valid transitions)
│   └── ShipmentDetailModal.jsx       # Detail view + history timeline
├── App.css
└── index.css
```
