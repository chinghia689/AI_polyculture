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
    file:        UploadFile  = File(...),
    ph:          float | None = Form(None),
    salinity:    float | None = Form(None),
    temperature: float | None = Form(None),
    area_ha:     float | None = Form(None),
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
    from module_rag.src.generation.chain import ask, build_diagnosis_query

    lime_result = probiotic_result = None
    try:
        if ph is not None and area_ha:
            lr = calculate_lime(ph, area_ha)
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
            )
            probiotic_result = {
                "bacillus_kg":   pr.bacillus_kg,
                "em_liters":     pr.em_liters,
                "apply_time":    pr.apply_time,
                "next_dose_day": pr.next_dose_day,
            }
    except ValueError:
        pass

    disease_name = None if vision_result["is_healthy"] else vision_result["label_vi"]
    query = build_diagnosis_query(
        disease=disease_name,
        ph=ph,
        salinity=salinity,
        temperature=temperature,
        area_ha=area_ha,
        calc_recommendation={"lime": lime_result, "probiotic": probiotic_result},
    )

    try:
        rag_result = ask(query)
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
        lime=      lime_result,
        probiotic= probiotic_result,
    )
