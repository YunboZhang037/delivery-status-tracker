"""Seed the database from shipments.csv."""
import csv
import os
import sys

from app.database import engine, SessionLocal, Base
from app.models import Shipment

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "shipments.csv")


def seed(csv_path: str | None = None):
    """Load shipments from CSV into the database.

    Idempotent: skips shipments that already exist (by reference).
    """
    path = csv_path or CSV_PATH
    if not os.path.isabs(path):
        path = os.path.abspath(path)

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ref = row["reference"].strip()
                existing = db.query(Shipment).filter_by(reference=ref).first()
                if existing:
                    skipped += 1
                    continue
                shipment = Shipment(
                    reference=ref,
                    customer_name=row["customer_name"].strip(),
                    status=row["status"].strip(),
                )
                db.add(shipment)
                inserted += 1
        db.commit()
        print(f"Seed complete: {inserted} inserted, {skipped} skipped (already exist)")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
