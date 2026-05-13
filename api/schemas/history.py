from pydantic import BaseModel
from datetime import datetime


class HistoryItem(BaseModel):
    id:              str
    farm_id:         str | None
    disease:         str | None
    species:         str | None
    ph:              float | None
    salinity:        float | None
    area_ha:         float | None
    farming_model:   str
    pond_stage:      str
    treatment_plan:  str | None
    lime_result:     dict | None
    probiotic_result:dict | None
    wq_result:       dict | None
    created_at:      datetime

    model_config = {"from_attributes": True}


class HistoryList(BaseModel):
    total: int
    items: list[HistoryItem]
