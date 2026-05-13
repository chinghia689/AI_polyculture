from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from api.db import get_db
from api.dependencies import get_optional_user
from api.models.history import DiagnoseHistory
from api.schemas.vision import PredictResponse, VisionDiagnoseResponse
from module_vision.predictor import predict as predict_shrimp
from module_vision.crab_predictor import predict as predict_crab

router = APIRouter(prefix="/vision", tags=["Vision"])


def _read_image(data: bytes) -> Image.Image:
    try:
        return Image.open(BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(400, "Không đọc được ảnh")


@router.post("/predict", response_model=PredictResponse)
async def predict_disease(
    file:    UploadFile = File(...),
    species: str        = Form("shrimp", description="shrimp | crab"),
):
    """Nhận ảnh tôm hoặc cua → trả về chẩn đoán bệnh."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File phải là ảnh (jpg, png, ...)")
    image = _read_image(await file.read())
    try:
        result = predict_shrimp(image) if species == "shrimp" else predict_crab(image)
        return result
    except Exception as e:
        raise HTTPException(500, f"Lỗi inference: {e}")


@router.post("/diagnose", response_model=VisionDiagnoseResponse)
async def vision_diagnose(
    file:            UploadFile  = File(...),
    species:         str          = Form("shrimp", description="shrimp | crab"),
    farm_id:         str | None   = Form(None),
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
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Upload ảnh tôm/cua → Vision detect bệnh → RAG ra phác đồ điều trị."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File phải là ảnh (jpg, png, ...)")

    image = _read_image(await file.read())

    try:
        vision_result = predict_shrimp(image) if species == "shrimp" else predict_crab(image)
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
            lr = calculate_lime(ph, area_ha, pond_stage=pond_stage, farming_model=farming_model)
            lime_result = {
                "dolomite_kg":          lr.dolomite_kg,
                "agricultural_lime_kg": lr.agricultural_lime_kg,
                "gypsum_kg":            lr.gypsum_kg,
                "status":               lr.status,
                "warning":              lr.warning,
            }
        if area_ha:
            is_sick = (not vision_result.get("is_healthy")) if vision_result.get("model_ready", True) else False
            pr = calculate_probiotic(
                area_ha, temperature or 28.0,
                has_disease_sign=is_sick,
                farming_model=farming_model, pond_stage=pond_stage,
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
             "status": a.status, "message": a.message, "action": a.action, "recheck": a.recheck}
            for a in wq.alerts
        ],
    } if wq.alerts else None

    disease_name = None
    if vision_result.get("model_ready", True) and not vision_result.get("is_healthy"):
        disease_name = vision_result.get("label_vi")

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
            sr = calculate_stocking(area_ha, FarmingModel(farming_model))
            stocking_result = {
                "shrimp_pl":                    sr.shrimp_pl,
                "crab_juveniles":               sr.crab_juveniles,
                "shrimp_density_per_m2":        sr.shrimp_density_per_m2,
                "crab_density_per_m2":          sr.crab_density_per_m2,
                "supplement_feed_kg_per_day":   sr.supplement_feed_kg_per_day,
                "supplement_feed_kg_per_month": sr.supplement_feed_kg_per_month,
                "feed_type":                    sr.feed_type,
            }
        except (ValueError, KeyError):
            pass

    calc_results = {"lime": lime_result, "probiotic": probiotic_result,
                    "stocking": stocking_result, "water_quality": wq_dict}
    try:
        rag_result = ask(query, calculator_results=calc_results)
    except Exception as e:
        raise HTTPException(500, f"Lỗi RAG: {e}")

    if current_user:
        db.add(DiagnoseHistory(
            user_id=current_user.id, farm_id=farm_id, disease=disease_name,
            species=species, ph=ph, salinity=salinity, temperature=temperature,
            area_ha=area_ha, farming_model=farming_model, pond_stage=pond_stage,
            treatment_plan=rag_result["answer"],
            lime_result=lime_result, probiotic_result=probiotic_result,
            stocking_result=stocking_result, wq_result=wq_dict,
        ))
        db.commit()

    return VisionDiagnoseResponse(
        disease=    vision_result["disease"],
        label_vi=   vision_result["label_vi"],
        confidence= vision_result["confidence"],
        is_healthy= vision_result.get("is_healthy"),
        query=          query,
        treatment_plan= rag_result["answer"],
        sources=        rag_result["sources"],
        lime=           lime_result,
        probiotic=      probiotic_result,
        stocking=       stocking_result,
        water_quality=  wq_dict,
    )
