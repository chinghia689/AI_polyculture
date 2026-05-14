from pydantic import BaseModel
from datetime import datetime


class ScheduleHistoryItem(BaseModel):
    id:            str
    start_date:    str
    phase:         str
    duration_days: int
    area_ha:       float
    farming_model: str
    task_count:    int
    tasks:         list | None
    created_at:    datetime

    model_config = {"from_attributes": True}


class ScheduleHistoryList(BaseModel):
    total: int
    items: list[ScheduleHistoryItem]
