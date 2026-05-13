from functools import lru_cache
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

VECTORDB_DIR = str(Path(__file__).parents[2] / "data" / "vectordb")
EMBED_MODEL  = "intfloat/multilingual-e5-base"
COLLECTION   = "polyaqua_knowledge"

# E5 yêu cầu prefix cố định:
#   "query: <text>"   → khi encode query lúc retrieval
#   "passage: <text>" → khi encode document lúc ingest  (xử lý trong ingest_documents.py)
_QUERY_PREFIX = "query: "


# ── Singletons (load 1 lần, cache vĩnh viễn) ─────────────────────────────────

@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(EMBED_MODEL)


@lru_cache(maxsize=1)
def _get_client() -> chromadb.PersistentClient:
    # Cache client riêng để tránh bị GC khi _get_collection() return
    return chromadb.PersistentClient(path=VECTORDB_DIR)


@lru_cache(maxsize=1)
def _get_collection() -> chromadb.Collection:
    return _get_client().get_collection(COLLECTION)


@lru_cache(maxsize=1)
def _get_bm25() -> tuple[BM25Okapi, list[str], list[dict]]:
    """
    Load toàn bộ documents từ ChromaDB, build BM25 index.
    Trả về (bm25, ids, metadatas) để lookup sau khi rank.
    """
    coll   = _get_collection()
    result = coll.get(include=["documents", "metadatas"])

    ids    = result["ids"]
    docs   = result["documents"]
    metas  = result["metadatas"]

    # Tokenize đơn giản: lowercase + split
    # Phù hợp cả tiếng Anh lẫn tiếng Việt không dấu; tiếng Việt có dấu vẫn match được
    tokenized = [doc.lower().split() for doc in docs]
    bm25 = BM25Okapi(tokenized)

    return bm25, ids, docs, metas


# ── Core retrieve functions ───────────────────────────────────────────────────

def _semantic_retrieve(query: str, n: int) -> list[tuple[str, float, dict, str]]:
    """Trả về list (id, score, meta, content)."""
    model      = _get_model()
    collection = _get_collection()

    vec     = model.encode(_QUERY_PREFIX + query, normalize_embeddings=True).tolist()
    results = collection.query(
        query_embeddings=[vec],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )
    out = []
    for doc_id, doc, meta, dist in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        score = round(1 - dist, 4)
        out.append((doc_id, score, meta, doc))
    return out


def _bm25_retrieve(query: str, n: int) -> list[tuple[str, float, dict, str]]:
    """Trả về list (id, bm25_score, meta, content)."""
    bm25, ids, docs, metas = _get_bm25()

    tokens = query.lower().split()
    scores = bm25.get_scores(tokens)

    # Lấy top-n index theo score
    top_n_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n]

    return [
        (ids[i], float(scores[i]), metas[i], docs[i])
        for i in top_n_idx
        if scores[i] > 0
    ]


def _rrf(rank: int, k: int = 60) -> float:
    """Reciprocal Rank Fusion score."""
    return 1.0 / (k + rank)


def _hybrid_retrieve(query: str, k: int = 4, n_candidates: int = 20) -> list[dict]:
    """
    RRF fusion: kết hợp semantic + BM25 rank → top-k.
    Không cần cân chỉnh weight, RRF robust hơn linear combination.
    """
    semantic_results = _semantic_retrieve(query, n=n_candidates)
    bm25_results     = _bm25_retrieve(query, n=n_candidates)

    # Gom score RRF theo doc_id
    rrf_scores: dict[str, float] = {}
    doc_lookup: dict[str, tuple[dict, str, float, float]] = {}  # id → (meta, content, sem_score, bm25_score)

    for rank, (doc_id, sem_score, meta, content) in enumerate(semantic_results):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + _rrf(rank)
        doc_lookup[doc_id] = (meta, content, sem_score, 0.0)

    for rank, (doc_id, bm25_score, meta, content) in enumerate(bm25_results):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + _rrf(rank)
        # Cập nhật bm25_score nếu đã có trong lookup
        if doc_id in doc_lookup:
            m, c, s, _ = doc_lookup[doc_id]
            doc_lookup[doc_id] = (m, c, s, bm25_score)
        else:
            doc_lookup[doc_id] = (meta, content, 0.0, bm25_score)

    # Sort theo RRF score, lấy top-k
    top_ids = sorted(rrf_scores, key=rrf_scores.__getitem__, reverse=True)[:k]

    return [
        {
            "content":    doc_lookup[doc_id][1],
            "source":     Path(doc_lookup[doc_id][0].get("source", "")).name,
            "sem_score":  round(doc_lookup[doc_id][2], 3),
            "bm25_score": round(doc_lookup[doc_id][3], 3),
            "rrf_score":  round(rrf_scores[doc_id], 4),
        }
        for doc_id in top_ids
    ]


# ── Public API ────────────────────────────────────────────────────────────────

def retrieve(query: str, k: int = 4, mode: str = "hybrid") -> list[dict]:
    """
    mode: "hybrid" (default) | "semantic" | "bm25"
    """
    if mode == "semantic":
        results = _semantic_retrieve(query, n=k)
        return [
            {"content": c, "source": Path(m.get("source","")).name,
             "score": s, "sem_score": s, "bm25_score": 0.0, "rrf_score": 0.0}
            for _, s, m, c in results
        ]
    if mode == "bm25":
        results = _bm25_retrieve(query, n=k)
        return [
            {"content": c, "source": Path(m.get("source","")).name,
             "score": s, "sem_score": 0.0, "bm25_score": s, "rrf_score": 0.0}
            for _, s, m, c in results
        ]
    return _hybrid_retrieve(query, k=k)
