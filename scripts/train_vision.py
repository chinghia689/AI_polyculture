"""
Train YOLOv8 classification model cho bệnh tôm sú.

Usage:
  python scripts/train_vision.py
  python scripts/train_vision.py --epochs 50 --model yolov8s-cls.pt
"""
import argparse
from pathlib import Path

from ultralytics import YOLO

DATASET_DIR = Path("module_vision/data/dataset")
MODEL_DIR   = Path("module_vision/models")
RUNS_DIR    = Path("module_vision/runs")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model",  default="yolov8n-cls.pt", help="Model base")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--imgsz",  type=int, default=224)
    parser.add_argument("--batch",  type=int, default=16)
    args = parser.parse_args()

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Model : {args.model}")
    print(f"Data  : {DATASET_DIR}")
    print(f"Epochs: {args.epochs} | Imgsz: {args.imgsz} | Batch: {args.batch}\n")

    model = YOLO(args.model)
    results = model.train(
        data=str(DATASET_DIR),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=str(RUNS_DIR),
        name="shrimp_cls",
        exist_ok=True,
        patience=10,        # early stopping
        cache=False,
    )

    # Copy best model sang models/
    best = Path(results.save_dir) / "weights" / "best.pt"
    if best.exists():
        dst = MODEL_DIR / "shrimp_disease_cls.pt"
        import shutil
        shutil.copy2(best, dst)
        print(f"\n✓ Best model saved: {dst}")

    # Eval trên test set
    print("\n[Test set evaluation]")
    metrics = model.val(data=str(DATASET_DIR), split="test")
    print(f"  Top-1 accuracy: {metrics.top1:.3f}")
    print(f"  Top-5 accuracy: {metrics.top5:.3f}")


if __name__ == "__main__":
    main()
