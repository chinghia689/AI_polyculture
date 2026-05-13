from fastapi import APIRouter, HTTPException
from module_calculator.src.lime_calculator import calculate_lime
from module_calculator.src.probiotic_calculator import calculate_probiotic
from module_calculator.src.stocking_calculator import FarmingModel, calculate_stocking
from module_calculator.src.water_quality import assess_water_quality
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
            lr = calculate_lime(req.ph, req.area_ha, pond_stage=req.pond_stage, farming_model=req.farming_model)
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
                farming_model=req.farming_model,
                pond_stage=req.pond_stage,
            )
            probiotic_result = {
                "bacillus_kg":   pr.bacillus_kg,
                "em_liters":     pr.em_liters,
                "apply_time":    pr.apply_time,
                "next_dose_day": pr.next_dose_day,
            }
    except ValueError:
        pass

    wq = assess_water_quality(
        do_mgl=req.do_mgl,
        alkalinity=req.alkalinity,
        nh3_mgl=req.nh3_mgl,
        no2_mgl=req.no2_mgl,
        transparency_cm=req.transparency_cm,
        days_cultured=req.days_cultured,
    )
    wq_dict = {
        "overall_status":   wq.overall_status,
        "danger_count":     wq.danger_count,
        "warning_count":    wq.warning_count,
        "priority_actions": wq.priority_actions,
        "growth_note":      wq.growth_note,
        "alerts": [
            {"param": a.param, "label": a.label, "value": a.value, "unit": a.unit,
             "status": a.status, "message": a.message, "action": a.action}
            for a in wq.alerts
        ],
    }

    query = build_diagnosis_query(
        disease=req.disease,
        ph=req.ph,
        salinity=req.salinity,
        temperature=req.temperature,
        area_ha=req.area_ha,
        calc_recommendation={"lime": lime_result, "probiotic": probiotic_result},
        farming_model=req.farming_model,
        pond_stage=req.pond_stage,
        do_mgl=req.do_mgl,
        alkalinity=req.alkalinity,
        nh3_mgl=req.nh3_mgl,
        no2_mgl=req.no2_mgl,
        transparency_cm=req.transparency_cm,
        days_cultured=req.days_cultured,
        water_quality=wq_dict,
    )

    stocking_result = None
    if req.area_ha:
        try:
            fm = FarmingModel(req.farming_model)
            sr = calculate_stocking(req.area_ha, fm)
            stocking_result = {
                "shrimp_pl":                   sr.shrimp_pl,
                "crab_juveniles":              sr.crab_juveniles,
                "shrimp_density_per_m2":       sr.shrimp_density_per_m2,
                "crab_density_per_m2":         sr.crab_density_per_m2,
                "supplement_feed_kg_per_day":  sr.supplement_feed_kg_per_day,
                "supplement_feed_kg_per_month": sr.supplement_feed_kg_per_month,
                "feed_type":                   sr.feed_type,
            }
        except (ValueError, KeyError):
            pass

    calc_results = {
        "lime":          lime_result,
        "probiotic":     probiotic_result,
        "stocking":      stocking_result,
        "water_quality": wq_dict,
    }
    try:
        rag_result = ask(query, calculator_results=calc_results)
    except Exception as e:
        raise HTTPException(500, f"RAG error: {e}")

    return DiagnoseResponse(
        query=query,
        treatment_plan=rag_result["answer"],
        sources=rag_result["sources"],
        lime=lime_result,
        probiotic=probiotic_result,
        stocking=stocking_result,
        water_quality=wq_dict if wq.alerts else None,
    )
