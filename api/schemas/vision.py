from pydantic import BaseModel


class PredictResponse(BaseModel):
    disease:    str
    label_vi:   str
    confidence: float
    top5:       list[dict]
    is_healthy: bool


class VisionDiagnoseResponse(BaseModel):
    # Vision
    disease:    str
    label_vi:   str
    confidence: float
    is_healthy: bool
    # RAG
    query:          str
    treatment_plan: str
    sources:        list[str]
    # Calculator
    lime:          dict | None
    probiotic:     dict | None
    stocking:      dict | None
    water_quality: dict | None
