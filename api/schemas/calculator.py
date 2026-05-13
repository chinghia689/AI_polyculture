from pydantic import BaseModel, Field
from datetime import date
from enum import Enum


class FarmingModelEnum(str, Enum):
    extensive      = "extensive"
    semi_intensive = "semi_intensive"


class FarmPhaseEnum(str, Enum):
    preparation = "preparation"
    early       = "early"
    mid         = "mid"
    late        = "late"


# ── Request models ────────────────────────────────────────────────────────────
class StockingRequest(BaseModel):
    area_ha: float = Field(..., gt=0, le=500, description="Diện tích ao (ha)")
    model:   FarmingModelEnum = FarmingModelEnum.extensive


class LimeRequest(BaseModel):
    current_ph:    float          = Field(..., ge=0, le=14, description="pH hiện tại của ao")
    area_ha:       float          = Field(..., gt=0, le=500)
    farming_model: FarmingModelEnum = FarmingModelEnum.extensive
    pond_stage:    str            = Field("stocked", pattern="^(preparation|stocked)$")


class ProbioticRequest(BaseModel):
    area_ha:              float          = Field(..., gt=0, le=500)
    temperature_c:        float          = Field(28.0, ge=15, le=40, description="Nhiệt độ nước (°C)")
    days_since_last_dose: int            = Field(7,    ge=0,  le=365)
    has_disease_sign:     bool           = Field(False)
    farming_model:        FarmingModelEnum = FarmingModelEnum.extensive
    pond_stage:           str            = Field("stocked", pattern="^(preparation|stocked)$")


class ScheduleRequest(BaseModel):
    start_date:    date             = Field(default_factory=date.today)
    phase:         FarmPhaseEnum    = FarmPhaseEnum.early
    duration_days: int              = Field(60, ge=7, le=365)
    area_ha:       float            = Field(1.0, gt=0)
    farming_model: FarmingModelEnum = FarmingModelEnum.extensive


class RecommendRequest(BaseModel):
    """Tính toán toàn bộ trong 1 request."""
    area_ha:              float          = Field(..., gt=0, le=500)
    current_ph:           float          = Field(..., ge=0, le=14)
    temperature_c:        float          = Field(28.0)
    salinity_ppt:         float          = Field(15.0, ge=0, le=40)
    days_since_probiotic: int            = Field(7, ge=0)
    has_disease_sign:     bool           = Field(False)
    farming_model:        FarmingModelEnum = FarmingModelEnum.extensive
    pond_stage:           str            = Field("stocked", pattern="^(preparation|stocked)$")
    phase:                FarmPhaseEnum  = FarmPhaseEnum.early


# ── Response models ───────────────────────────────────────────────────────────
class StockingResponse(BaseModel):
    model:                        str
    area_ha:                      float
    shrimp_pl:                    int
    crab_juveniles:               int
    shrimp_density_m2:            float
    crab_density_m2:              float
    supplement_feed_kg_per_day:   float
    supplement_feed_kg_per_month: float
    feed_type:                    str | None
    notes:                        list[str]


class LimeResponse(BaseModel):
    current_ph:           float
    area_ha:              float
    status:               str
    dolomite_kg:          float
    agricultural_lime_kg: float
    gypsum_kg:            float
    target_ph:            str
    timing:               str
    notes:                list[str]
    warning:              str | None


class ProbioticResponse(BaseModel):
    area_ha:       float
    bacillus_kg:   float
    em_liters:     float
    apply_time:    str
    frequency:     str
    next_dose_day: int
    notes:         list[str]


class ScheduleTaskResponse(BaseModel):
    date:     date
    task:     str
    category: str
    priority: str
    note:     str


class ScheduleResponse(BaseModel):
    farm_phase: str
    start_date: date
    tasks:      list[ScheduleTaskResponse]
    upcoming_7d: list[ScheduleTaskResponse]


class RecommendResponse(BaseModel):
    stocking:  StockingResponse
    lime:      LimeResponse
    probiotic: ProbioticResponse
