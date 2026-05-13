"""
Ingest tài liệu PDF vào ChromaDB vector store cho RAG module.

Usage:
    python scripts/ingest_documents.py
    python scripts/ingest_documents.py --reset   # xoá vectordb cũ, ingest lại từ đầu
"""
import argparse
import shutil
import uuid
from pathlib import Path

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

DOCS_DIR        = Path("module_rag/data/documents")
VECTORDB_DIR    = Path("module_rag/data/vectordb")
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
COLLECTION_NAME = "polyaqua_knowledge"
CHUNK_SIZE      = 500
CHUNK_OVERLAP   = 50

# E5 yêu cầu prefix "passage: " khi encode document (không phải query)
PASSAGE_PREFIX  = "passage: "


def load_pdfs(docs_dir: Path) -> list[dict]:
    pages = []
    pdf_files = sorted(docs_dir.glob("**/*.pdf"))
    for pdf_path in tqdm(pdf_files, desc="  Reading PDFs"):
        try:
            reader = PdfReader(str(pdf_path))
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append({"text": text, "source": str(pdf_path), "page": i + 1})
        except Exception as e:
            print(f"  ⚠  Bỏ qua {pdf_path.name}: {e}")
    return pages


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        start += size - overlap
    return [c for c in chunks if len(c) > 50]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Xoá vectordb cũ, ingest lại")
    args = parser.parse_args()

    pdf_files = list(DOCS_DIR.glob("**/*.pdf"))
    if not pdf_files:
        print(f"✗ Không tìm thấy PDF trong {DOCS_DIR}")
        print("  Hãy chạy: python scripts/download_documents.py")
        return

    print(f"Tìm thấy {len(pdf_files)} file PDF\n")

    if args.reset and VECTORDB_DIR.exists():
        shutil.rmtree(VECTORDB_DIR)
        print("  ✓ Đã xoá vectordb cũ\n")

    VECTORDB_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/4] Đọc PDF...")
    pages = load_pdfs(DOCS_DIR)
    print(f"  → {len(pages)} trang\n")

    print("[2/4] Chia chunk...")
    docs, metas, ids = [], [], []
    for p in pages:
        for chunk in chunk_text(p["text"]):
            docs.append(chunk)
            metas.append({"source": p["source"], "page": p["page"]})
            ids.append(str(uuid.uuid4()))
    print(f"  → {len(docs)} chunks\n")

    print(f"[3/4] Tạo embeddings (model: {EMBEDDING_MODEL})...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    # E5 cần prefix "passage: " cho document khi ingest
    prefixed_docs = [PASSAGE_PREFIX + d for d in docs]
    embeddings = model.encode(
        prefixed_docs,
        normalize_embeddings=True,
        batch_size=32,          # e5-base lớn hơn MiniLM, giảm batch size
        show_progress_bar=True,
    ).tolist()
    print()

    print(f"[4/4] Lưu vào ChromaDB ({VECTORDB_DIR})...")
    client     = chromadb.PersistentClient(path=str(VECTORDB_DIR))
    # Xoá collection cũ nếu có (khi --reset)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    batch_size = 500
    for i in range(0, len(docs), batch_size):
        collection.add(
            documents=docs[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            metadatas=metas[i:i + batch_size],
            ids=ids[i:i + batch_size],
        )
    print(f"  ✓ {collection.count()} vectors đã lưu\n")

    # Verify
    print("[Verify] Test query...")
    test_queries = [
        "tôm bị đen mang phải xử lý như thế nào",
        "mud crab disease treatment",
        "pH water quality shrimp",
    ]
    model = SentenceTransformer(EMBEDDING_MODEL)
    for q in test_queries:
        emb = model.encode(q, normalize_embeddings=True).tolist()
        res = collection.query(query_embeddings=[emb], n_results=1)
        src = Path(res["metadatas"][0][0].get("source", "?")).name
        print(f"  [{q[:40]}] → {src}")

    print(f"\n{'='*55}")
    print(f"✓ Ingest hoàn tất! {collection.count()} vectors")
    print(f"  python scripts/ingest_documents.py --reset  # nếu muốn ingest lại")


if __name__ == "__main__":
    main()
