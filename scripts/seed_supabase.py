"""
One-off script: create tables and insert static seed data in Supabase.
Uses DATABASE_URL and app models. Run from project root:
  python -m scripts.seed_supabase
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.base import Base
from app.db.models import User, Floor, Zone, Campaign, Event, Notification


def main():
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    # 1) Drop all tables then create from current models (fresh schema)
    Base.metadata.drop_all(bind=engine)
    print("Dropped existing tables.")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    try:
        # 2) Skip if already seeded
        if db.query(Floor).first():
            print("Floors already exist. Skip seed.")
            return

        # 3) Static floors (floor_id = floor number, floor_name only)
        ground = Floor(floor_id=0, floor_name="Ground Floor")
        first = Floor(floor_id=1, floor_name="First Floor")
        db.add_all([ground, first])
        db.commit()

        # 4) Static zones (id=UUID, floor_id=floor number, name; no polygon_coordinates)
        zones = [
            Zone(id=uuid.uuid4(), floor_id=0, name="Pantry"),
            Zone(id=uuid.uuid4(), floor_id=0, name="Meeting Room A"),
            Zone(id=uuid.uuid4(), floor_id=0, name="Conference Hall"),
            Zone(id=uuid.uuid4(), floor_id=1, name="Webknot 2nd floor"),
        ]
        db.add_all(zones)
        db.commit()
        print("Seeded floors and zones.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
