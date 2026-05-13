"""
Gom và split dataset cho Vision module (YOLOv8-cls).

Nguồn:
  - archive/ShrimpImages/ShrimpImages/{Healthy,BG,WSSV,WSSV_BG}/
  - module_vision/data/raw/healthy_shrimp/

Output:
  module_vision/data/dataset/
  ├── train/{healthy_shrimp,black_gill,white_spot,wssv_black_gill}/
  ├── val/  {...}
  └── test/ {...}

Usage:
  python scripts/prepare_vision_dataset.py
  python scripts/prepare_vision_dataset.py --reset
"""
import argparse
import random
import shutil
from pathlib import Path

RAW_DIR = Path("module_vision/data/raw")
OUT_DIR = Path("module_vision/data/dataset")

SOURCES = {
    "healthy_shrimp":  [RAW_DIR / "healthy_shrimp"],
    "black_gill":      [RAW_DIR / "black_gill"],
    "white_spot":      [RAW_DIR / "white_spot"],
    "wssv_black_gill": [RAW_DIR / "wssv_black_gill"],
}

SPLIT = {"train": 0.70, "val": 0.20, "test": 0.10}
SEED  = 42
IMG_EXTS = {".jpg", ".jpeg", ".png"}


def collect_images(src_dirs: list[Path]) -> list[Path]:
    imgs = []
    for d in src_dirs:
        if d.exists():
            imgs += [p for p in d.iterdir() if p.suffix.lower() in IMG_EXTS]
    return imgs


def split(imgs: list[Path]) -> dict[str, list[Path]]:
    random.shuffle(imgs)
    n = len(imgs)
    n_train = int(n * SPLIT["train"])
    n_val   = int(n * SPLIT["val"])
    return {
        "train": imgs[:n_train],
        "val":   imgs[n_train:n_train + n_val],
        "test":  imgs[n_train + n_val:],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Xóa dataset cũ, tạo lại")
    args = parser.parse_args()

    if args.reset and OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
        print("✓ Đã xóa dataset cũ\n")

    random.seed(SEED)

    print(f"{'Class':<20} {'Total':>6} {'Train':>6} {'Val':>5} {'Test':>5}")
    print("-" * 47)

    for cls_name, src_dirs in SOURCES.items():
        imgs = collect_images(src_dirs)
        splits = split(imgs)

        for split_name, split_imgs in splits.items():
            dst = OUT_DIR / split_name / cls_name
            dst.mkdir(parents=True, exist_ok=True)
            for img in split_imgs:
                shutil.copy2(img, dst / img.name)

        print(
            f"{cls_name:<20} {len(imgs):>6} "
            f"{len(splits['train']):>6} {len(splits['val']):>5} {len(splits['test']):>5}"
        )

    print("\n✓ Dataset sẵn sàng tại:", OUT_DIR)
    print(f"  Train: {sum(1 for _ in (OUT_DIR/'train').rglob('*') if _.is_file())} ảnh")
    print(f"  Val:   {sum(1 for _ in (OUT_DIR/'val').rglob('*') if _.is_file())} ảnh")
    print(f"  Test:  {sum(1 for _ in (OUT_DIR/'test').rglob('*') if _.is_file())} ảnh")


if __name__ == "__main__":
    main()
