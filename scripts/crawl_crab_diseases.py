"""
Thu thập ảnh bệnh cua biển từ iNaturalist + Google Images.

Mục tiêu: 200+ ảnh/lớp × 5 lớp = 1,000+ ảnh raw
  - healthy_crab     Cua khỏe mạnh
  - black_gill_crab  Đen mang
  - barnacle         Đóng rong/hà bám
  - limb_loss        Rụng càng/gãy chân
  - fungal_crab      Nấm trên mai cua

Cách dùng:
  python scripts/crawl_crab_diseases.py --class healthy_crab --limit 300
  python scripts/crawl_crab_diseases.py --all --limit 200
"""
import argparse
import time
from pathlib import Path

import requests
from tqdm import tqdm

OUTPUT_DIR = Path("module_vision/data/raw/crab")

INATURALIST_QUERIES = {
    "healthy_crab":    ["Scylla serrata", "mud crab", "cua biển khỏe"],
    "black_gill_crab": ["crab black gill disease", "black gill mud crab"],
    "barnacle":        ["barnacle crab", "crab barnacle infestation", "hà bám cua"],
    "limb_loss":       ["crab missing leg", "crab limb autotomy", "cua gãy càng"],
    "fungal_crab":     ["crab shell disease", "fungal crab shell", "nấm vỏ cua"],
}

INATURALIST_TAXON_IDS = {
    "healthy_crab": 116726,  # Scylla serrata (mud crab)
}


def _inaturalist_search(query: str, limit: int = 50) -> list[str]:
    """Tìm ảnh trên iNaturalist theo từ khóa, trả về danh sách URL."""
    urls = []
    page = 1
    while len(urls) < limit:
        try:
            r = requests.get(
                "https://api.inaturalist.org/v1/observations",
                params={
                    "q": query,
                    "taxon_id": 116726,  # Portunidae / Scylla
                    "has[]": "photos",
                    "quality_grade": "research",
                    "per_page": 50,
                    "page": page,
                },
                timeout=15,
            )
            data = r.json()
            if not data.get("results"):
                break
            for obs in data["results"]:
                for photo in obs.get("photos", []):
                    url = photo.get("url", "").replace("square", "medium")
                    if url:
                        urls.append(url)
            page += 1
            time.sleep(1)
        except Exception as e:
            print(f"  iNaturalist error: {e}")
            break
    return urls[:limit]


def _download(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, timeout=15, stream=True)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return True
    except Exception:
        return False


def crawl_class(class_name: str, limit: int = 200):
    dest_dir = OUTPUT_DIR / class_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    queries = INATURALIST_QUERIES.get(class_name, [class_name])
    print(f"\n[{class_name}] Thu thập tối đa {limit} ảnh từ {len(queries)} truy vấn...")

    all_urls = []
    for q in queries:
        urls = _inaturalist_search(q, limit=limit // len(queries) + 20)
        all_urls.extend(urls)
        print(f"  '{q}' → {len(urls)} URL")

    # Loại trùng
    all_urls = list(dict.fromkeys(all_urls))[:limit]

    existing = len(list(dest_dir.glob("*.jpg")))
    downloaded = 0
    for i, url in enumerate(tqdm(all_urls, desc=class_name)):
        fname = dest_dir / f"{class_name}_{existing + i:04d}.jpg"
        if fname.exists():
            continue
        if _download(url, fname):
            downloaded += 1
        time.sleep(0.3)

    print(f"  ✓ Tải được {downloaded} ảnh mới → {dest_dir} (tổng: {existing + downloaded})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="cls", help="Tên lớp bệnh")
    parser.add_argument("--all",   action="store_true", help="Thu thập tất cả lớp")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    if args.all:
        for cls in INATURALIST_QUERIES:
            crawl_class(cls, args.limit)
    elif args.cls:
        crawl_class(args.cls, args.limit)
    else:
        parser.print_help()

    print("\n✅ Xong! Kiểm tra ảnh tại module_vision/data/raw/crab/")
    print("Tiếp theo: gán nhãn trên Roboflow rồi chạy scripts/train_vision.py --species crab")


if __name__ == "__main__":
    main()
