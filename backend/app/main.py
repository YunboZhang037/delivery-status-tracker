"""FastAPI application — shipment tracking endpoints."""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db, engine, Base
from app.models import Shipment, StatusHistory
from app.schemas import ShipmentOut, StatusUpdateIn, ShipmentDetailOut, StatusHistoryOut
from app.state_machine import validate_transition, InvalidTransitionError

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Delivery Status Tracker", version="1.0.0")

# CORS — allow the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/shipments", response_model=list[ShipmentOut])
def list_shipments(
    status: str | None = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    """List all shipments, optionally filtered by status."""
    stmt = select(Shipment).order_by(Shipment.id)
    if status:
        stmt = stmt.where(Shipment.status == status)
    return db.execute(stmt).scalars().all()


@app.get("/api/shipments/{reference}", response_model=ShipmentDetailOut)
def get_shipment(reference: str, db: Session = Depends(get_db)):
    """Get a single shipment with its status history."""
    shipment = db.execute(
        select(Shipment).where(Shipment.reference == reference)
    ).scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail=f"Shipment '{reference}' not found")
    return shipment


@app.patch("/api/shipments/{reference}/status", response_model=ShipmentOut)
def update_status(
    reference: str,
    payload: StatusUpdateIn,
    db: Session = Depends(get_db),
):
    """Update a shipment's status.

    Validates the transition against the state machine:
    created -> picked_up -> in_transit -> delivered
    `failed` is allowed from any non-delivered status.
    """
    shipment = db.execute(
        select(Shipment).where(Shipment.reference == reference)
    ).scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail=f"Shipment '{reference}' not found")

    try:
        validate_transition(shipment.status, payload.status)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Record history
    history_entry = StatusHistory(
        shipment_id=shipment.id,
        previous_status=shipment.status,
        new_status=payload.status,
    )
    shipment.status = payload.status
    db.add(history_entry)
    db.commit()
    db.refresh(shipment)
    return shipment


@app.get("/api/shipments/{reference}/history", response_model=list[StatusHistoryOut])
def get_status_history(reference: str, db: Session = Depends(get_db)):
    """Get the full status-change history for a shipment."""
    shipment = db.execute(
        select(Shipment).where(Shipment.reference == reference)
    ).scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail=f"Shipment '{reference}' not found")
    return shipment.history
