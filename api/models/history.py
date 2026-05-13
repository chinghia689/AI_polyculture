import uuid
from datetime import datetime
from sqlalchemy import String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.db import Base


class DiagnoseHistory(Base):
    __tablename__ = "diagnose_history"

    id:              Mapped[str]       = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id:         Mapped[str]       = mapped_column(String(36), ForeignKey("users.id"), index=True)
    farm_id:         Mapped[str|None]  = mapped_column(String(36), ForeignKey("farms.id"), nullable=True, index=True)

    # Thông số đầu vào
    disease:         Mapped[str|None]  = mapped_column(String(100), nullable=True)
    species:         Mapped[str|None]  = mapped_column(String(20), nullable=True)   # shrimp / crab
    ph:              Mapped[float|None]= mapped_column(Float, nullable=True)
    salinity:        Mapped[float|None]= mapped_column(Float, nullable=True)
    temperature:     Mapped[float|None]= mapped_column(Float, nullable=True)
    area_ha:         Mapped[float|None]= mapped_column(Float, nullable=True)
    farming_model:   Mapped[str]       = mapped_column(String(20), default="extensive")
    pond_stage:      Mapped[str]       = mapped_column(String(20), default="stocked")
    image_path:      Mapped[str|None]  = mapped_column(String(500), nullable=True)

    # Kết quả
    treatment_plan:  Mapped[str|None]  = mapped_column(Text, nullable=True)
    lime_result:     Mapped[dict|None] = mapped_column(JSON, nullable=True)
    probiotic_result:Mapped[dict|None] = mapped_column(JSON, nullable=True)
    stocking_result: Mapped[dict|None] = mapped_column(JSON, nullable=True)
    wq_result:       Mapped[dict|None] = mapped_column(JSON, nullable=True)

    created_at:      Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="history")
    farm = relationship("Farm", back_populates="history")
