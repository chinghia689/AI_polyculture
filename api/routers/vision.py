from io import BytesIO

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image

from api.schemas.vision import PredictResponse, VisionDiagnoseResponse
from module_vision.predictor import predict

router = APIRouter(prefix="/vision", tags=["Vision"])


def _read_image(data: bytes) -> Image.Image:
    try:
        return Image.open(BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(400, "Không đọc được ảnh")


@router.post("/predict", response_model=PredictResponse)
async def predict_disease(file: UploadFile = File(...)):
    """Nhận ảnh tôm → trả về chẩn đoán bệnh."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File phải là ảnh (jpg, png, ...)")
    image = _read_image(await file.read())
    try:
        return predict(image)
    except Exception as e:
        raise HTTPException(500, f"Lỗi inference: {e}")


@router.post("/diagnose", response_model=VisionDiagnoseResponse)
async def vision_diagnose(
    file:            UploadFile  = File(...),
    ph:              float | None = Form(None),
    salinity:        float | None = Form(None),
    temperature:     float | None = Form(None),
    area_ha:         float | None = Form(None),
    farming_model:   str          = Form("extensive"),
    pond_stage:      str          = Form("stocked"),
    do_mgl:          float | None = Form(None),
    alkalinity:      float | None = Form(None),
    nh3_mgl:         float | None = Form(None),
    no2_mgl:         float | None = Form(None),
    transparency_cm: float | None = Form(None),
    days_cultured:   int   | None = Form(None),
):
    """Upload ảnh tôm → Vision detect bệnh → RAG ra phác đồ điều trị."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File phải là ảnh (jpg, png, ...)")

    image = _read_image(await file.read())

    try:
        vision_result = predict(image)
    except Exception as e:
        raise HTTPException(500, f"Lỗi vision: {e}")

    from module_calculator.src.lime_calculator import calculate_lime
    from module_calculator.src.probiotic_calculator import calculate_probiotic
    from module_calculator.src.stocking_calculator import FarmingModel, calculate_stocking
    from module_calculator.src.water_quality import assess_water_quality
    from module_rag.src.generation.chain import ask, build_diagnosis_query

    lime_result = probiotic_result = None
    try:
        if ph is not None and area_ha:
            lr = calculate_lime(ph, area_ha, pond_stage=pond_stage)
            lime_result = {
                "dolomite_kg":          lr.dolomite_kg,
                "agricultural_lime_kg": lr.agricultural_lime_kg,
                "gypsum_kg":            lr.gypsum_kg,
                "status":               lr.status,
                "warning":              lr.warning,
            }
        if area_ha:
            pr = calculate_probiotic(
                area_ha,
                temperature or 28.0,
                has_disease_sign=not vision_result["is_healthy"],
                farming_model=farming_model,
                pond_stage=pond_stage,
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
        do_mgl=do_mgl, alkalinity=alkalinity, nh3_mgl=nh3_mgl,
        no2_mgl=no2_mgl, transparency_cm=transparency_cm, days_cultured=days_cultured,
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
    } if wq.alerts else None

    disease_name = None if vision_result["is_healthy"] else vision_result["label_vi"]
    query = build_diagnosis_query(
        disease=disease_name,
        ph=ph, salinity=salinity, temperature=temperature, area_ha=area_ha,
        calc_recommendation={"lime": lime_result, "probiotic": probiotic_result},
        farming_model=farming_model, pond_stage=pond_stage,
        do_mgl=do_mgl, alkalinity=alkalinity, nh3_mgl=nh3_mgl,
        no2_mgl=no2_mgl, transparency_cm=transparency_cm, days_cultured=days_cultured,
        water_quality=wq_dict,
    )

    stocking_result = None
    if area_ha:
        try:
            fm = FarmingModel(farming_model)
            sr = calculate_stocking(area_ha, fm)
            stocking_result = {
                "shrimp_pl":             sr.shrimp_pl,
                "crab_juveniles":        sr.crab_juveniles,
                "shrimp_density_per_m2": sr.shrimp_density_per_m2,
                "crab_density_per_m2":   sr.crab_density_per_m2,
                "feed_kg_per_month":     sr.feed_kg_per_month,
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
        raise HTTPException(500, f"Lỗi RAG: {e}")

    return VisionDiagnoseResponse(
        disease=    vision_result["disease"],
        label_vi=   vision_result["label_vi"],
        confidence= vision_result["confidence"],
        is_healthy= vision_result["is_healthy"],
        query=          query,
        treatment_plan= rag_result["answer"],
        sources=        rag_result["sources"],
        lime=          lime_result,
        probiotic=     probiotic_result,
        stocking=      stocking_result,
        water_quality= wq_dict,
    )
