from pydantic import BaseModel, Field
from datetime import datetime


class FarmCreate(BaseModel):
    name:          str   = Field(..., min_length=1, max_length=255)
    area_ha:       float = Field(..., gt=0, le=500)
    farming_model: str   = Field("extensive", pattern="^(extensive|semi_intensive)$")
    province:      str | None = None
    notes:         str | None = None


class FarmUpdate(BaseModel):
    name:          str   | None = None
    area_ha:       float | None = Field(None, gt=0, le=500)
    farming_model: str   | None = Field(None, pattern="^(extensive|semi_intensive)$")
    province:      str   | None = None
    notes:         str   | None = None


class FarmResponse(BaseModel):
    id:            str
    name:          str
    area_ha:       float
    farming_model: str
    province:      str | None
    notes:         str | None
    created_at:    datetime
    updated_at:    datetime

    model_config = {"from_attributes": True}
