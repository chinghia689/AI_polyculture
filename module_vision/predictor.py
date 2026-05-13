from functools import lru_cache
from pathlib import Path

from PIL import Image
from ultralytics import YOLO

MODEL_PATH = Path(__file__).parent / "models" / "shrimp_disease_cls.pt"

CLASSES = {
    "healthy_shrimp":  "Tôm khỏe mạnh",
    "black_gill":      "Bệnh đen mang (Black Gill)",
    "white_spot":      "Bệnh đốm trắng WSSV",
    "wssv_black_gill": "Đốm trắng + Đen mang",
}


@lru_cache(maxsize=1)
def _get_model() -> YOLO:
    return YOLO(str(MODEL_PATH))


def predict(image: Image.Image) -> dict:
    model = _get_model()
    results = model.predict(image, verbose=False)[0]

    probs      = results.probs
    top1_idx   = int(probs.top1)
    top1_conf  = float(probs.top1conf)
    class_name = results.names[top1_idx]

    top5 = [
        {
            "class":       results.names[int(i)],
            "label_vi":    CLASSES.get(results.names[int(i)], results.names[int(i)]),
            "confidence":  round(float(probs.data[int(i)]), 4),
        }
        for i in probs.top5
    ]

    return {
        "disease":    class_name,
        "label_vi":   CLASSES.get(class_name, class_name),
        "confidence": round(top1_conf, 4),
        "top5":       top5,
        "is_healthy": class_name == "healthy_shrimp",
    }
