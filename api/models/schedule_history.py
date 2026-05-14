import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.db import Base


class ScheduleHistory(Base):
    __tablename__ = "schedule_history"

    id:            Mapped[str]       = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id:       Mapped[str]       = mapped_column(String(36), ForeignKey("users.id"), index=True)

    start_date:    Mapped[str]       = mapped_column(String(10))
    phase:         Mapped[str]       = mapped_column(String(20))
    duration_days: Mapped[int]       = mapped_column(Integer)
    area_ha:       Mapped[float]     = mapped_column(Float)
    farming_model: Mapped[str]       = mapped_column(String(20))
    task_count:    Mapped[int]       = mapped_column(Integer)
    tasks:         Mapped[list|None] = mapped_column(JSON, nullable=True)

    created_at:    Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="schedule_history")
