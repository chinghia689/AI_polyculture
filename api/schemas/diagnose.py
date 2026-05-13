from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=1000,
                          description="Câu hỏi về ao nuôi tôm/cua")


class DiagnoseRequest(BaseModel):
    disease:         str | None   = Field(None, description="Tên bệnh phát hiện (từ Vision module)")
    # Thông số cơ bản
    ph:              float | None = Field(None, ge=0,    le=14)
    salinity:        float | None = Field(None, ge=0,    le=45,   description="Độ mặn (ppt)")
    temperature:     float | None = Field(None, ge=15,   le=42,   description="Nhiệt độ nước (°C)")
    area_ha:         float | None = Field(None, gt=0,    le=500)
    # Thông số nâng cao (đo bằng bộ test kit phổ thông)
    do_mgl:          float | None = Field(None, ge=0,    le=20,   description="Oxy hòa tan (mg/L)")
    alkalinity:      float | None = Field(None, ge=0,    le=500,  description="Độ kiềm (mg/L CaCO₃)")
    nh3_mgl:         float | None = Field(None, ge=0,    le=10,   description="NH₃ (mg/L)")
    no2_mgl:         float | None = Field(None, ge=0,    le=10,   description="NO₂⁻ (mg/L)")
    transparency_cm: float | None = Field(None, ge=5,    le=200,  description="Độ trong đĩa Secchi (cm)")
    days_cultured:   int   | None = Field(None, ge=0,    le=365,  description="Số ngày đã nuôi")
    # Mô hình & giai đoạn
    farming_model:   str          = Field("extensive",   description="extensive | semi_intensive")
    pond_stage:      str          = Field("stocked",     description="preparation | stocked")


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
    water_quality:  dict | None
