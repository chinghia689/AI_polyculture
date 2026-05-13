from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=1000,
                          description="Câu hỏi về ao nuôi tôm/cua")


class DiagnoseRequest(BaseModel):
    disease:     str | None   = Field(None,  description="Tên bệnh phát hiện (từ Vision module)")
    ph:          float | None = Field(None,  ge=0,  le=14)
    salinity:    float | None = Field(None,  ge=0,  le=45,  description="Độ mặn (ppt)")
    temperature: float | None = Field(None,  ge=15, le=42,  description="Nhiệt độ nước (°C)")
    area_ha:     float | None = Field(None,  gt=0,  le=500)


class ChatResponse(BaseModel):
    answer:         str
    sources:        list[str]
    context_chunks: int


class DiagnoseResponse(BaseModel):
    query:          str
    treatment_plan: str
    sources:        list[str]
    lime:           dict | None
    probiotic:      dict | None
