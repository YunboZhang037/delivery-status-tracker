"""Tests for the API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.models import Shipment, StatusHistory
from app.main import app

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite:///file::memory:?cache=shared&uri=true"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Wipe all data between tests."""
    db = TestSessionLocal()
    db.query(StatusHistory).delete()
    db.query(Shipment).delete()
    db.commit()
    db.close()
    yield
    db = TestSessionLocal()
    db.query(StatusHistory).delete()
    db.query(Shipment).delete()
    db.commit()
    db.close()


def _seed_shipment(reference="TV-TEST1", status="created", customer="Test Customer"):
    db = TestSessionLocal()
    shipment = Shipment(reference=reference, customer_name=customer, status=status)
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    db.close()
    return shipment


class TestListShipments:
    def test_list_empty(self):
        resp = client.get("/api/shipments")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_data(self):
        _seed_shipment(reference="TV-001", status="created")
        _seed_shipment(reference="TV-002", status="delivered")
        resp = client.get("/api/shipments")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["reference"] == "TV-001"

    def test_filter_by_status(self):
        _seed_shipment(reference="TV-001", status="created")
        _seed_shipment(reference="TV-002", status="delivered")
        _seed_shipment(reference="TV-003", status="delivered")
        resp = client.get("/api/shipments?status=delivered")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(s["status"] == "delivered" for s in data)


class TestGetShipment:
    def test_get_single_shipment(self):
        _seed_shipment(reference="TV-001", status="in_transit", customer="Acme Corp")
        resp = client.get("/api/shipments/TV-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["reference"] == "TV-001"
        assert data["customer_name"] == "Acme Corp"
        assert data["status"] == "in_transit"
        assert "history" in data

    def test_get_shipment_not_found(self):
        resp = client.get("/api/shipments/NOT-EXIST")
        assert resp.status_code == 404


class TestUpdateStatus:
    def test_valid_transition(self):
        _seed_shipment(reference="TV-001", status="created")
        resp = client.patch("/api/shipments/TV-001/status", json={"status": "picked_up"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "picked_up"

    def test_invalid_transition_409(self):
        _seed_shipment(reference="TV-001", status="created")
        resp = client.patch("/api/shipments/TV-001/status", json={"status": "delivered"})
        assert resp.status_code == 409
        assert "Cannot transition" in resp.json()["detail"]

    def test_terminal_state_409(self):
        _seed_shipment(reference="TV-001", status="delivered")
        resp = client.patch("/api/shipments/TV-001/status", json={"status": "failed"})
        assert resp.status_code == 409
        assert "terminal" in resp.json()["detail"].lower()

    def test_shipment_not_found(self):
        resp = client.patch("/api/shipments/NOT-EXIST/status", json={"status": "picked_up"})
        assert resp.status_code == 404

    def test_history_recorded_on_update(self):
        _seed_shipment(reference="TV-001", status="created")
        client.patch("/api/shipments/TV-001/status", json={"status": "picked_up"})
        resp = client.get("/api/shipments/TV-001/history")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["previous_status"] == "created"
        assert data[0]["new_status"] == "picked_up"

    def test_note_recorded_on_update(self):
        _seed_shipment(reference="TV-001", status="created")
        client.patch(
            "/api/shipments/TV-001/status",
            json={"status": "failed", "note": "Customer not available for pickup"},
        )
        resp = client.get("/api/shipments/TV-001/history")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["new_status"] == "failed"
        assert data[0]["note"] == "Customer not available for pickup"

    def test_note_optional(self):
        _seed_shipment(reference="TV-001", status="created")
        resp = client.patch("/api/shipments/TV-001/status", json={"status": "picked_up"})
        assert resp.status_code == 200
        history = client.get("/api/shipments/TV-001/history").json()
        assert history[0]["note"] is None

    # ── Unknown-status boundary (regression: used to raise 500) ──
    def test_unknown_status_rejected_422(self):
        """A status that is not part of the state machine must be a client error (422), not a 500."""
        _seed_shipment(reference="TV-001", status="created")
        resp = client.patch("/api/shipments/TV-001/status", json={"status": "bogus"})
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        # The validation error should point at the `status` field
        assert any("status" in err["loc"] for err in detail)

    def test_non_string_status_rejected_422(self):
        """Non-string values (e.g. numbers) must also be rejected as client errors."""
        _seed_shipment(reference="TV-001", status="created")
        resp = client.patch("/api/shipments/TV-001/status", json={"status": 123})
        assert resp.status_code == 422

    def test_valid_enum_but_illegal_transition_still_409(self):
        """Literal validation must not swallow state-machine semantics:
        a *legal* status that is an *illegal transition* still returns 409."""
        _seed_shipment(reference="TV-001", status="created")
        resp = client.patch("/api/shipments/TV-001/status", json={"status": "delivered"})
        assert resp.status_code == 409
        assert "Cannot transition" in resp.json()["detail"]

    def test_missing_status_field_422(self):
        """Payload without a status field is a validation error, not a 500."""
        _seed_shipment(reference="TV-001", status="created")
        resp = client.patch("/api/shipments/TV-001/status", json={"note": "no status"})
        assert resp.status_code == 422
