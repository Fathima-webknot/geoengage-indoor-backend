from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Floor(Base):
    __tablename__ = "floors"

    floor_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    floor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    zones = relationship("Zone", back_populates="floor")
