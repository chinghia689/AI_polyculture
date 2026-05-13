from fastapi import APIRouter, HTTPException
from module_calculator.src.lime_calculator import calculate_lime
from module_calculator.src.probiotic_calculator import calculate_probiotic
from module_rag.src.generation.chain import ask, build_diagnosis_query
from api.schemas.diagnose import (
    ChatRequest, ChatResponse,
    DiagnoseRequest, DiagnoseResponse,
)

router = APIRouter(prefix="/diagnose", tags=["Diagnose"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Hỏi đáp tự do với chuyên gia RAG."""
    try:
        result = ask(req.question)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(500, f"RAG error: {e}")


@router.post("/", response_model=DiagnoseResponse)
def diagnose(req: DiagnoseRequest):
    """Tích hợp chẩn đoán + tính toán → phác đồ điều trị hoàn chỉnh."""
    lime_result      = None
    probiotic_result = None

    try:
        if req.ph is not None and req.area_ha:
            lr = calculate_lime(req.ph, req.area_ha)
            lime_result = {
                "dolomite_kg":          lr.dolomite_kg,
                "agricultural_lime_kg": lr.agricultural_lime_kg,
                "gypsum_kg":            lr.gypsum_kg,
                "status":               lr.status,
                "warning":              lr.warning,
            }
        if req.area_ha:
            pr = calculate_probiotic(
                req.area_ha,
                req.temperature or 28.0,
                has_disease_sign=bool(req.disease),
            )
            probiotic_result = {
                "bacillus_kg":  pr.bacillus_kg,
                "em_liters":    pr.em_liters,
                "apply_time":   pr.apply_time,
                "next_dose_day": pr.next_dose_day,
            }
    except ValueError:
        pass

    query = build_diagnosis_query(
        disease=req.disease,
        ph=req.ph,
        salinity=req.salinity,
        temperature=req.temperature,
        area_ha=req.area_ha,
        calc_recommendation={"lime": lime_result, "probiotic": probiotic_result},
    )

    try:
        rag_result = ask(query)
    except Exception as e:
        raise HTTPException(500, f"RAG error: {e}")

    return DiagnoseResponse(
        query=query,
        treatment_plan=rag_result["answer"],
        sources=rag_result["sources"],
        lime=lime_result,
        probiotic=probiotic_result,
    )
