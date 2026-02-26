from sqlalchemy import String, Integer, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Zone(Base):
    __tablename__ = "zones"
    __table_args__ = (UniqueConstraint("floor_id", "name", name="unique_zone_per_floor"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    floor_id: Mapped[int] = mapped_column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    polygon_coordinates: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    floor = relationship("Floor", back_populates="zones")
    campaigns = relationship("Campaign", back_populates="zone")
    events = relationship("Event", back_populates="zone")
