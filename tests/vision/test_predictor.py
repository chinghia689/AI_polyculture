"""Unit tests cho module_vision/predictor.py"""
import pytest
from pathlib import Path
from PIL import Image

from module_vision.predictor import predict, CLASSES

DATASET_TEST = Path("module_vision/data/dataset/test")

CLASSES_ALL = list(CLASSES.keys())


def _first_image(class_name: str) -> Image.Image:
    folder = DATASET_TEST / class_name
    img_path = next(folder.iterdir())
    return Image.open(img_path).convert("RGB")


# ── Output schema ─────────────────────────────────────────────────────────────

class TestPredictSchema:
    def test_keys_present(self):
        img = _first_image("healthy_shrimp")
        result = predict(img)
        assert set(result.keys()) == {"disease", "label_vi", "confidence", "top5", "is_healthy"}

    def test_confidence_range(self):
        img = _first_image("healthy_shrimp")
        result = predict(img)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_disease_is_valid_class(self):
        img = _first_image("black_gill")
        result = predict(img)
        assert result["disease"] in CLASSES_ALL

    def test_label_vi_not_empty(self):
        img = _first_image("white_spot")
        result = predict(img)
        assert len(result["label_vi"]) > 0

    def test_top5_length(self):
        img = _first_image("healthy_shrimp")
        result = predict(img)
        assert len(result["top5"]) == 4   # 4 classes → top5 capped at 4

    def test_top5_confidence_sum(self):
        img = _first_image("healthy_shrimp")
        result = predict(img)
        total = sum(r["confidence"] for r in result["top5"])
        assert abs(total - 1.0) < 0.01   # softmax → tổng ≈ 1


# ── is_healthy flag ───────────────────────────────────────────────────────────

class TestIsHealthy:
    def test_healthy_flag_true(self):
        img = _first_image("healthy_shrimp")
        result = predict(img)
        # Không assert cứng prediction đúng vì accuracy 78% — chỉ test flag logic
        assert result["is_healthy"] == (result["disease"] == "healthy_shrimp")

    def test_sick_flag_false_when_predicted_sick(self):
        img = _first_image("black_gill")
        result = predict(img)
        assert result["is_healthy"] == (result["disease"] == "healthy_shrimp")


# ── Accuracy spot-check ───────────────────────────────────────────────────────

class TestAccuracy:
    @pytest.mark.parametrize("class_name", CLASSES_ALL)
    def test_top1_on_sample(self, class_name):
        """Mỗi class predict đúng ít nhất 1 ảnh trong 3 ảnh đầu test set."""
        folder = DATASET_TEST / class_name
        images = list(folder.iterdir())[:3]
        predictions = [predict(Image.open(p).convert("RGB"))["disease"] for p in images]
        assert class_name in predictions, (
            f"Không có ảnh nào trong 3 ảnh đầu của {class_name} được predict đúng. "
            f"Predictions: {predictions}"
        )


# ── Input edge cases ──────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_small_image(self):
        img = Image.new("RGB", (32, 32), color=(128, 128, 128))
        result = predict(img)
        assert result["disease"] in CLASSES_ALL

    def test_large_image(self):
        img = Image.new("RGB", (2048, 2048), color=(50, 100, 150))
        result = predict(img)
        assert result["disease"] in CLASSES_ALL

    def test_grayscale_converted(self):
        gray = Image.new("L", (224, 224), color=128).convert("RGB")
        result = predict(gray)
        assert result["disease"] in CLASSES_ALL
