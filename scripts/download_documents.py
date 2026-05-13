"""
Tải tự động tài liệu kỹ thuật thủy sản về module_rag/data/documents/

Usage:
    python scripts/download_documents.py
    python scripts/download_documents.py --dry-run   # chỉ liệt kê, không tải
"""
import argparse
import time
from pathlib import Path

import requests
from tqdm import tqdm

DOCS_DIR = Path("module_rag/data/documents")

# Mỗi doc có thể có nhiều url để fallback theo thứ tự
DOCUMENTS = [
    {
        "filename": "01_mud_crab_aquaculture_FAO_TP567.pdf",
        "title": "Mud Crab Aquaculture — FAO Technical Paper 567",
        "source": "FAO",
        "urls": [
            # FAO chặn script — thử Wayback Machine
            "https://web.archive.org/web/2024/https://www.fao.org/4/ba0110e/ba0110e.pdf",
            "https://www.fao.org/4/ba0110e/ba0110e.pdf",
        ],
        "manual": "https://openknowledge.fao.org/handle/20.500.14219/9006",
    },
    {
        "filename": "02_mud_crab_capture_based_FAO.pdf",
        "title": "Capture-Based Aquaculture of Mud Crabs (Scylla spp.)",
        "source": "FAO",
        "urls": [
            "https://web.archive.org/web/2024/https://www.fao.org/4/i0254e/i0254e13.pdf",
            "https://www.fao.org/4/i0254e/i0254e13.pdf",
        ],
        "manual": "https://www.fao.org/publications/card/en/c/i0254e",
    },
    {
        "filename": "03_crustacean_diseases_NACA.pdf",
        "title": "Crustacean Diseases & Diagnostic Guide (Shrimp & Crab)",
        "source": "NACA",
        "urls": [
            "https://library.enaca.org/NACA-Publications/ADG-CrustaceanDiseases.pdf",
        ],
        "manual": "https://library.enaca.org/NACA-Publications/ADG-CrustaceanDiseases.pdf",
    },
    {
        "filename": "04a_AHPND_diagnosis_WOAH_2023.pdf",
        "title": "AHPND Diagnosis & Detection — WOAH Aquatic Manual 2023",
        "source": "WOAH (OIE)",
        "urls": [
            "https://www.woah.org/fileadmin/Home/eng/Health_standards/aahm/current/2.2.01_AHPND.pdf",
        ],
        "manual": None,
    },
    {
        "filename": "04b_AHPND_chapter_WOAH_legacy.pdf",
        "title": "AHPND Chapter — WOAH Aquatic Manual (legacy)",
        "source": "WOAH (OIE)",
        "urls": [
            "https://www.woah.org/fileadmin/Home/eng/Health_standards/aahm/current/chapitre_ahpnd.pdf",
        ],
        "manual": None,
    },
    {
        "filename": "05_seed_production_mudcrab_NACA.pdf",
        "title": "Seed Production of Mud Crab Scylla spp.",
        "source": "NACA",
        "urls": [
            "https://library.enaca.org/AquacultureAsia/Articles/July-Sept-2002/Seed_production_mudcrab.pdf",
        ],
        "manual": None,
    },
    {
        "filename": "06_probiotics_shrimp_PMC_2023.pdf",
        "title": "The Role of Probiotics in Shrimp Aquaculture (PMC Open Access)",
        "source": "PubMed Central",
        "urls": [
            # PMC direct PDF — open access, không cần login
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC10082739/pdf/vetworld-16-548.pdf",
            "https://europepmc.org/articles/PMC10082739?pdf=render",
        ],
        "manual": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10082739/",
    },
    {
        "filename": "07_shrimp_systems_vietnam_worldfish.pdf",
        "title": "Evolution of Shrimp Aquaculture Systems — Bangladesh & Vietnam",
        "source": "WorldFish",
        "urls": [
            "https://digitalarchive.worldfishcenter.org/bitstreams/78276259-b0e8-4896-a6bd-907075cbfa3a/download",
        ],
        "manual": None,
    },
    {
        "filename": "08_mangrove_fishery_farming_IUCN.pdf",
        "title": "Integrated Mangrove-Fishery Farming System",
        "source": "IUCN",
        "urls": [
            "https://iucn.org/sites/default/files/content/documents/2016/imffs_sgf_project_report.pdf",
        ],
        "manual": None,
    },
    {
        "filename": "09_vi_rimf_tom_su_cua_bien_ca_hoi_2024.pdf",
        "title": "Kỹ thuật nuôi thương phẩm tôm sú, cua biển và cá hói",
        "source": "RIMF",
        "urls": [
            "https://www.rimf.org.vn/Media/Default/Bantin/2024/%E1%BA%A4n%20ph%E1%BA%A9m%20qu%C3%BD%204.2024-2.pdf",
        ],
        "manual": None,
    },
    {
        "filename": "10_vi_rimf_tom_su_ca_mang_ben_tre_2025.pdf",
        "title": "Kỹ thuật nuôi tôm sú kết hợp cá măng trong ao đất",
        "source": "RIMF",
        "urls": [
            "https://www.rimf.org.vn/Media/Default/AnPham/%E1%BA%A4n%20ph%E1%BA%A9m%20qu%C3%BD%202.2025.pdf",
        ],
        "manual": None,
    },
    {
        "filename": "11_vi_ria2_tom_lua_dbscl_2013.pdf",
        "title": "Nuôi tôm-lúa ĐBSCL: hiện trạng, bệnh và năng suất tôm/cua/cá",
        "source": "RIA2",
        "urls": [
            "https://vienthuysan2.org.vn/wp-content/uploads/2022/05/pdf-1.pdf",
        ],
        "manual": None,
    },
    {
        "filename": "12_vi_ria2_benh_tom_dbscl_2019.pdf",
        "title": "Sự hiện diện của WSSV, Vibrio parahaemolyticus và EHP trên tôm giống và tôm nuôi nước lợ ở ĐBSCL",
        "source": "RIA2",
        "urls": [
            "https://vienthuysan2.org.vn/wp-content/uploads/2022/05/pdf-16.pdf",
        ],
        "manual": None,
    },
    {
        "filename": "13_vi_ria2_wssv_ahpnd_ehp_dbscl_2021.pdf",
        "title": "Sự hiện diện của WSSV, Vibrio parahaemolyticus và EHP trên tôm giống cung cấp cho ĐBSCL và tôm nuôi thương phẩm",
        "source": "RIA2",
        "urls": [
            "https://vienthuysan2.org.vn/wp-content/uploads/2022/07/TCNC_So-21-2021-2.pdf",
        ],
        "manual": None,
    },
]

# Headers giả lập Chrome để qua rate limiter của nhiều trang
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,application/octet-stream,*/*;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def make_session(referer: str | None = None) -> requests.Session:
    session = requests.Session()
    headers = BROWSER_HEADERS.copy()
    if referer:
        headers["Referer"] = referer
    session.headers.update(headers)
    return session


def try_download(session: requests.Session, url: str, save_path: Path) -> bool:
    """Thử tải 1 URL. Trả về True nếu thành công."""
    try:
        resp = session.get(url, timeout=60, stream=True, allow_redirects=True)
        resp.raise_for_status()

        content_type = resp.headers.get("content-type", "").lower()
        # Chấp nhận PDF, octet-stream, hoặc binary không xác định
        ok_types = ("pdf", "octet-stream", "binary", "download")
        if not any(t in content_type for t in ok_types):
            # Nếu URL là archive.org thì bỏ qua kiểm tra content-type
            if "archive.org" not in url:
                return False

        total = int(resp.headers.get("content-length", 0))
        with open(save_path, "wb") as f, tqdm(
            total=total, unit="B", unit_scale=True,
            desc=f"  {save_path.name}", leave=False,
        ) as bar:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))

        # Kiểm tra file thực sự là PDF (header magic bytes)
        if save_path.stat().st_size < 1024:
            save_path.unlink(missing_ok=True)
            return False
        with open(save_path, "rb") as f:
            if f.read(4) != b"%PDF":
                save_path.unlink(missing_ok=True)
                return False

        return True

    except Exception:
        save_path.unlink(missing_ok=True)
        return False


def download_doc(doc: dict) -> bool:
    save_path = DOCS_DIR / doc["filename"]

    if save_path.exists():
        size_kb = save_path.stat().st_size / 1024
        print(f"  ✓ Đã có: {save_path.name} ({size_kb:.0f} KB)")
        return True

    for i, url in enumerate(doc["urls"]):
        referer = "https://www.fao.org/" if "fao.org" in url else None
        session = make_session(referer)

        if try_download(session, url, save_path):
            size_kb = save_path.stat().st_size / 1024
            print(f"  ✓ {save_path.name} ({size_kb:.0f} KB)")
            return True

        if i < len(doc["urls"]) - 1:
            time.sleep(2)

    # Tất cả URL đều thất bại
    print(f"  ✗ Tải thất bại — tải thủ công tại:")
    print(f"     {doc.get('manual') or doc['urls'][0]}")
    print(f"     Lưu vào: {DOCS_DIR}/{doc['filename']}")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Liệt kê danh sách, không tải")
    args = parser.parse_args()

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        print("Danh sách tài liệu:")
        for doc in DOCUMENTS:
            exists = "✓" if (DOCS_DIR / doc["filename"]).exists() else "○"
            print(f"  {exists} [{doc['source']}] {doc['title']}")
        return

    print(f"Tải {len(DOCUMENTS)} tài liệu về {DOCS_DIR}/\n")

    success, failed = 0, 0
    manual_needed = []

    for doc in DOCUMENTS:
        print(f"[{doc['source']}] {doc['title']}")
        if download_doc(doc):
            success += 1
        else:
            failed += 1
            manual_needed.append(doc)
        time.sleep(1.5)

    print(f"\n{'='*60}")
    print(f"Hoàn tất: {success} thành công, {failed} thất bại")

    if manual_needed:
        print(f"\nCần tải thủ công ({len(manual_needed)} file):")
        print("(Mở URL trong trình duyệt → Save as PDF → đặt vào module_rag/data/documents/)")
        for doc in manual_needed:
            url = doc.get("manual") or doc["urls"][0]
            print(f"\n  [{doc['source']}] {doc['title']}")
            print(f"  URL: {url}")
            print(f"  Tên file: {doc['filename']}")

    if success > 0:
        print(f"\nBước tiếp theo:")
        print(f"  python scripts/ingest_documents.py   # đưa vào RAG vector store")


if __name__ == "__main__":
    main()
