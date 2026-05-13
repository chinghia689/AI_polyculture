"""Integration tests cho Vision API endpoints."""
import io
import pytest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

DATASET_TEST = Path("module_vision/data/dataset/test")


def _image_bytes(class_name: str) -> bytes:
    img_path = next((DATASET_TEST / class_name).iterdir())
    buf = io.BytesIO()
    Image.open(img_path).convert("RGB").save(buf, format="JPEG")
    return buf.getvalue()


def _upload(endpoint: str, class_name: str, extra_data: dict = None):
    data   = extra_data or {}
    files  = {"file": ("test.jpg", _image_bytes(class_name), "image/jpeg")}
    return client.post(f"/api/v1/vision/{endpoint}", data=data, files=files)


# ── /predict ──────────────────────────────────────────────────────────────────

class TestPredictEndpoint:
    def test_status_200(self):
        r = _upload("predict", "healthy_shrimp")
        assert r.status_code == 200

    def test_response_schema(self):
        r = _upload("predict", "black_gill")
        body = r.json()
        assert "disease" in body
        assert "label_vi" in body
        assert "confidence" in body
        assert "top5" in body
        assert "is_healthy" in body

    def test_confidence_range(self):
        r = _upload("predict", "white_spot")
        assert 0.0 <= r.json()["confidence"] <= 1.0

    def test_invalid_file_type(self):
        r = client.post(
            "/api/v1/vision/predict",
            files={"file": ("doc.pdf", b"fake content", "application/pdf")},
        )
        assert r.status_code == 400

    def test_all_classes_return_200(self):
        for cls in ["healthy_shrimp", "black_gill", "white_spot", "wssv_black_gill"]:
            r = _upload("predict", cls)
            assert r.status_code == 200, f"Failed for class: {cls}"


# ── /diagnose ─────────────────────────────────────────────────────────────────

class TestVisionDiagnoseEndpoint:
    def test_status_200_image_only(self):
        r = _upload("diagnose", "black_gill")
        assert r.status_code == 200

    def test_response_schema(self):
        r = _upload("diagnose", "black_gill")
        body = r.json()
        for key in ["disease", "label_vi", "confidence", "is_healthy",
                    "query", "treatment_plan", "sources", "lime", "probiotic"]:
            assert key in body, f"Missing key: {key}"

    def test_treatment_plan_not_empty(self):
        r = _upload("diagnose", "black_gill")
        assert len(r.json()["treatment_plan"]) > 50

    def test_with_water_params(self):
        r = _upload("diagnose", "black_gill", {
            "ph": "6.5", "salinity": "15", "temperature": "28", "area_ha": "1.5"
        })
        assert r.status_code == 200
        body = r.json()
        assert body["lime"] is not None
        assert body["probiotic"] is not None

    def test_healthy_shrimp_no_treatment_needed(self):
        r = _upload("diagnose", "healthy_shrimp")
        body = r.json()
        assert r.status_code == 200
        # is_healthy phải match prediction
        assert body["is_healthy"] == (body["disease"] == "healthy_shrimp")

    def test_lime_none_without_area(self):
        r = _upload("diagnose", "black_gill", {"ph": "6.5"})
        assert r.json()["lime"] is None   # ph có nhưng không có area_ha

    def test_invalid_file_type(self):
        r = client.post(
            "/api/v1/vision/diagnose",
            files={"file": ("doc.pdf", b"fake", "application/pdf")},
        )
        assert r.status_code == 400
