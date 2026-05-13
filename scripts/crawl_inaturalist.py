"""
Crawl ảnh tôm sú & cua biển từ iNaturalist API (public, không cần key).

Usage:
    python scripts/crawl_inaturalist.py
    python scripts/crawl_inaturalist.py --disease black_gill --limit 300
    python scripts/crawl_inaturalist.py --list-targets
"""
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from tqdm import tqdm

# ── Cấu hình taxon iNaturalist ────────────────────────────────────────────────
# Tôm sú: Penaeus monodon (taxon_id=209120)
# Cua biển: Scylla serrata (taxon_id=340825), Scylla spp (taxon_id=324720)
TARGETS = {
    # Tôm sú khoẻ mạnh
    "healthy_shrimp": {
        "taxon_id": 209120,           # Penaeus monodon
        "query": "Penaeus monodon",
        "save_dir": "healthy_shrimp",
        "quality": "research",        # chỉ lấy ảnh đã xác nhận
    },
    # Cua biển khoẻ mạnh
    "healthy_crab": {
        "taxon_id": 340825,           # Scylla serrata
        "query": "Scylla serrata",
        "save_dir": "healthy_crab",
        "quality": "research",
    },
    # ── Bệnh tôm — cần tìm theo từ khoá (quality thấp hơn OK) ──────────────
    "white_spot": {
        "taxon_id": 209120,
        "query": "white spot disease shrimp WSSV",
        "save_dir": "white_spot",
        "quality": "any",
    },
    "black_gill": {
        "taxon_id": 209120,
        "query": "black gill shrimp diseased",
        "save_dir": "black_gill",
        "quality": "any",
    },
    "barnacle": {
        "taxon_id": 340825,
        "query": "barnacle fouling mud crab",
        "save_dir": "barnacle",
        "quality": "any",
    },
    "limb_loss": {
        "taxon_id": 340825,
        "query": "mud crab limb loss damaged",
        "save_dir": "limb_loss",
        "quality": "any",
    },
}

BASE_URL = "https://api.inaturalist.org/v1"
OUTPUT_DIR = Path("module_vision/data/raw")


def fetch_observations(taxon_id: int, query: str, quality: str, limit: int) -> list:
    """Lấy danh sách observation từ iNaturalist API."""
    results = []
    page = 1
    per_page = min(200, limit)

    while len(results) < limit:
        params = {
            "taxon_id": taxon_id,
            "q": query,
            "quality_grade": quality,
            "photos": True,
            "per_page": per_page,
            "page": page,
            "order": "desc",
            "order_by": "votes",  # lấy ảnh chất lượng cao trước
        }
        resp = requests.get(f"{BASE_URL}/observations", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if not data["results"]:
            break

        results.extend(data["results"])
        page += 1
        time.sleep(0.5)  # tránh rate limit

    return results[:limit]


def download_image(url: str, save_path: Path) -> bool:
    """Tải 1 ảnh về disk."""
    if save_path.exists():
        return True
    try:
        resp = requests.get(url, timeout=30, stream=True)
        resp.raise_for_status()
        save_path.write_bytes(resp.content)
        return True
    except Exception:
        return False


def crawl_target(name: str, config: dict, limit: int, workers: int):
    save_dir = OUTPUT_DIR / config["save_dir"]
    save_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[{name}] Fetching observations...")
    observations = fetch_observations(
        config["taxon_id"], config["query"], config["quality"], limit
    )
    print(f"  Found {len(observations)} observations")

    download_jobs = []
    for obs in observations:
        if not obs.get("photos"):
            continue
        photo = obs["photos"][0]
        url = photo["url"].replace("square", "large")
        obs_id = obs["id"]
        ext = url.split(".")[-1].split("?")[0]
        save_path = save_dir / f"{name}_{obs_id}.{ext}"
        download_jobs.append((url, save_path))

    downloaded = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(download_image, url, save_path)
            for url, save_path in download_jobs
        ]
        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc=f"  Downloading {name}",
        ):
            if future.result():
                downloaded += 1
            else:
                failed += 1

    print(f"  ✓ Downloaded: {downloaded}  ✗ Failed: {failed}")
    return downloaded


def main():
    parser = argparse.ArgumentParser(description="Crawl ảnh tôm/cua từ iNaturalist")
    parser.add_argument("--disease", type=str, default=None,
                        help="Chỉ crawl target cụ thể (vd: black_gill)")
    parser.add_argument("--limit", type=int, default=200,
                        help="Số ảnh tối đa mỗi target (default: 200)")
    parser.add_argument("--workers", type=int, default=6,
                        help="Số luồng tải ảnh song song (default: 6)")
    parser.add_argument("--list-targets", action="store_true",
                        help="Liệt kê các target có sẵn")
    args = parser.parse_args()

    if args.list_targets:
        print("Các target có sẵn:")
        for name in TARGETS:
            print(f"  - {name}")
        return

    targets = {args.disease: TARGETS[args.disease]} if args.disease else TARGETS

    if args.disease and args.disease not in TARGETS:
        print(f"✗ Target '{args.disease}' không tồn tại. Dùng --list-targets để xem.")
        return

    total = 0
    for name, config in targets.items():
        total += crawl_target(name, config, args.limit, args.workers)

    print(f"\n{'='*50}")
    print(f"Hoàn tất! Tổng {total} ảnh tải về {OUTPUT_DIR}/")
    print(f"\nBước tiếp theo:")
    print(f"  1. Kiểm tra ảnh tại module_vision/data/raw/")
    print(f"  2. Upload lên Roboflow để gán nhãn")
    print(f"  3. Xoá ảnh không phù hợp (mờ, không nhìn rõ tôm/cua)")


if __name__ == "__main__":
    main()
