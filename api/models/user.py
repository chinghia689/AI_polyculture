import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.db import Base


class User(Base):
    __tablename__ = "users"

    id:              Mapped[str]      = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email:           Mapped[str]      = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str]      = mapped_column(String(255))
    full_name:       Mapped[str]      = mapped_column(String(255))
    phone:           Mapped[str|None] = mapped_column(String(20), nullable=True)
    created_at:      Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    farms   = relationship("Farm",           back_populates="owner",   cascade="all, delete-orphan")
    history = relationship("DiagnoseHistory", back_populates="user",   cascade="all, delete-orphan")
