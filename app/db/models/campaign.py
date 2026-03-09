import uuid

from sqlalchemy import Boolean, Text, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False
    )
    # Optional display name / offer name (e.g. "Summer Sale")
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # Trigger type controls when this campaign is used (e.g. zone_entry, zone_exit_no_txn)
    trigger: Mapped[str] = mapped_column(String(50), nullable=False, default="zone_entry")
    active: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    zone = relationship("Zone", back_populates="campaigns")
    notifications = relationship("Notification", back_populates="campaign")
