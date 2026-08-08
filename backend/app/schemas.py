"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

from app.state_machine import VALID_STATUSES

# Status values accepted by the API — mirrors the state machine.
# A tuple preserves a stable order for the error message.
VALID_STATUS_TUPLE = tuple(sorted(VALID_STATUSES))


class ShipmentOut(BaseModel):
    """Shipment data returned by the API."""
    id: int
    reference: str
    customer_name: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StatusUpdateIn(BaseModel):
    """Request body for updating a shipment's status."""
    status: Literal[*VALID_STATUS_TUPLE] = Field(..., description="New status: created, picked_up, in_transit, delivered, or failed")
    note: str | None = Field(None, description="Optional note for the status change (e.g., failure reason)")


class StatusHistoryOut(BaseModel):
    """A single status-change record."""
    id: int
    previous_status: str | None
    new_status: str
    changed_at: datetime
    note: str | None

    model_config = {"from_attributes": True}


class ShipmentDetailOut(ShipmentOut):
    """Shipment with full status history (for the detail/history view)."""
    history: list[StatusHistoryOut] = []
