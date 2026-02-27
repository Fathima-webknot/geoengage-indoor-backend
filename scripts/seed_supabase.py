"""
One-off script: create tables and insert static seed data in Supabase.
Uses DATABASE_URL and app models. Run from project root:
  python -m scripts.seed_supabase
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.base import Base
from app.db.models import Floor, Zone

def main():
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    
    # 1) Create all tables (idempotent; safe if they exist)
    Base.metadata.create_all(bind=engine)
    print("Tables created or already exist.")

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    try:
        # 2) Skip if already seeded
        if db.query(Floor).first():
            print("Floors already exist. Skip seed.")
            return

        # 3) Static floors
        ground = Floor(name="Ground Floor", floor_number=0)
        first = Floor(name="First Floor", floor_number=1)
        db.add_all([ground, first])
        db.commit()
        db.refresh(ground)
        db.refresh(first)

        # 4) Static zones (polygon format: [[lng, lat], ...] – example coords)
        zones = [
            Zone(
                floor_id=ground.id,
                name="Pantry",
                polygon_coordinates=[
                    [77.5946, 12.9716],
                    [77.5948, 12.9716],
                    [77.5948, 12.9714],
                    [77.5946, 12.9714],
                    [77.5946, 12.9716],
                ],
            ),
            Zone(
                floor_id=ground.id,
                name="Meeting Room A",
                polygon_coordinates=[
                    [77.5950, 12.9716],
                    [77.5952, 12.9716],
                    [77.5952, 12.9714],
                    [77.5950, 12.9714],
                    [77.5950, 12.9716],
                ],
            ),
            Zone(
                floor_id=ground.id,
                name="Conference Hall",
                polygon_coordinates=[
                    [77.5954, 12.9716],
                    [77.5958, 12.9716],
                    [77.5958, 12.9712],
                    [77.5954, 12.9712],
                    [77.5954, 12.9716],
                ],
            ),
        ]
        db.add_all(zones)
        db.commit()
        print("Seeded floors and zones.")
    finally:
        db.close()


if __name__ == "__main__":
    main()