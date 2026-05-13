import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.db import Base


class Farm(Base):
    __tablename__ = "farms"

    id:            Mapped[str]      = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id:       Mapped[str]      = mapped_column(String(36), ForeignKey("users.id"), index=True)
    name:          Mapped[str]      = mapped_column(String(255))          # tên ao/vuông
    area_ha:       Mapped[float]    = mapped_column(Float)
    farming_model: Mapped[str]      = mapped_column(String(20), default="extensive")
    province:      Mapped[str|None] = mapped_column(String(100), nullable=True)  # tỉnh/huyện
    notes:         Mapped[str|None] = mapped_column(String(500), nullable=True)
    created_at:    Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at:    Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner   = relationship("User",            back_populates="farms")
    history = relationship("DiagnoseHistory", back_populates="farm", cascade="all, delete-orphan")
