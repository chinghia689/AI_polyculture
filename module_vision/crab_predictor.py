"""
Crab disease predictor — placeholder until training data is collected.

Classes (5):
  healthy_crab     — Cua khỏe mạnh
  black_gill_crab  — Đen mang
  barnacle         — Đóng rong/hà
  limb_loss        — Rụng càng, gãy chân
  fungal_crab      — Nấm trên mai
"""
from functools import lru_cache
from pathlib import Path

from PIL import Image

MODEL_PATH = Path(__file__).parent / "models" / "crab_disease_cls.pt"

CLASSES = {
    "healthy_crab":    "Cua khỏe mạnh",
    "black_gill_crab": "Đen mang (cua)",
    "barnacle":        "Đóng rong / hà bám",
    "limb_loss":       "Rụng càng / gãy chân",
    "fungal_crab":     "Nấm trên mai cua",
}


def _model_ready() -> bool:
    return MODEL_PATH.exists()


@lru_cache(maxsize=1)
def _get_model():
    from ultralytics import YOLO
    return YOLO(str(MODEL_PATH))


def predict(image: Image.Image) -> dict:
    if not _model_ready():
        return {
            "disease":     "model_not_ready",
            "label_vi":    "Chưa có mô hình nhận diện bệnh cua",
            "confidence":  0.0,
            "is_healthy":  None,
            "top3":        [],
            "model_ready": False,
            "message":     (
                "Mô hình nhận diện bệnh cua đang được huấn luyện. "
                "Vui lòng mô tả triệu chứng bằng văn bản để nhận phác đồ từ chuyên gia AI."
            ),
        }

    model = _get_model()
    results = model.predict(image, verbose=False)[0]
    probs      = results.probs
    top1_idx   = int(probs.top1)
    top1_conf  = float(probs.top1conf)
    class_name = results.names[top1_idx]
    label_vi   = CLASSES.get(class_name, class_name)
    is_healthy = class_name == "healthy_crab"

    top3 = [
        {"disease": results.names[i], "label_vi": CLASSES.get(results.names[i], results.names[i]),
         "confidence": round(float(probs.data[i]), 3)}
        for i in probs.top5[:3]
    ]
    return {
        "disease":     class_name,
        "label_vi":    label_vi,
        "confidence":  round(top1_conf, 3),
        "is_healthy":  is_healthy,
        "top3":        top3,
        "model_ready": True,
        "message":     None,
    }
