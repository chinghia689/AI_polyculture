# PolyAqua Agent

Hệ thống AI hỗ trợ nuôi tôm sú & cua biển xen kẽ (polyculture) tại vùng ngập mặn ĐBSCL.

## Tính năng

| Module | Mô tả |
|--------|-------|
| **Vision — Bác sĩ AI** | Chụp ảnh → nhận diện 12 loại bệnh tôm/cua bằng YOLOv8 |
| **Calculator — Tính ao** | Nhập diện tích, pH, độ mặn → liều vôi, vi sinh, mật độ thả giống |
| **RAG Brain — Chuyên gia** | Tổng hợp chẩn đoán + chỉ số môi trường → phác đồ điều trị tự nhiên |

## Cấu trúc dự án

```
AI_Polyculture/
├── module_vision/          # Computer Vision — nhận diện bệnh
│   ├── data/               # Dataset ảnh tôm/cua
│   ├── models/             # Checkpoint YOLOv8 (.pt, .onnx)
│   ├── notebooks/          # Jupyter — train & evaluation
│   └── src/
│       ├── dataset/        # Augmentation pipeline
│       ├── train/          # Training scripts
│       ├── inference/      # Predict + TTA
│       └── utils/
├── module_calculator/      # Tính toán liều lượng & lịch thăm ao
│   ├── src/                # Stocking, lime, probiotic, schedule
│   ├── configs/            # Bảng tra cứu rule-based
│   └── tests/
├── module_rag/             # RAG Brain — hệ chuyên gia
│   ├── data/
│   │   ├── documents/      # Tài liệu kỹ thuật thủy sản (PDF)
│   │   └── vectordb/       # ChromaDB index
│   ├── notebooks/
│   └── src/
│       ├── ingestion/      # PDF → Vector store
│       ├── retrieval/      # Semantic search
│       ├── generation/     # LLM chain (Claude API)
│       └── utils/
├── api/                    # FastAPI backend
│   ├── routers/            # Endpoints
│   ├── schemas/            # Pydantic models
│   └── services/           # Orchestrator (3 module)
├── frontend/               # Next.js / React Native
├── scripts/                # Setup, ingest, evaluate
├── docs/                   # Label schema, corpus list
├── tests/                  # Vision, Calculator, RAG, Integration
├── PLAN.md                 # Kế hoạch triển khai chi tiết (đọc trước)
└── docker-compose.yml
```

## Bắt đầu nhanh

```bash
# 1. Clone & cài đặt
git clone <repo>
cd AI_Polyculture
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Cấu hình
cp .env.example .env
# Điền ANTHROPIC_API_KEY vào .env

# 3. Khởi động services
docker-compose up -d   # PostgreSQL + MinIO + ChromaDB
_hybrid_retrieve
# 4. Ingest tài liệu kỹ thuật vào RAG
python scripts/ingest_documents.py

# 5. Chạy API
uvicorn api.main:app --reload
```

## Kế hoạch chi tiết

Xem **[PLAN.md](PLAN.md)** — roadmap 7 phase, 24 tuần, đầy đủ code snippets.

## Tech Stack

- **Vision:** YOLOv8 (Ultralytics), ONNX
- **RAG:** LangChain + ChromaDB + sentence-transformers
- **LLM:** Claude claude-sonnet-4-6 (Anthropic)
- **Backend:** FastAPI + PostgreSQL
- **Mobile:** React Native + Expo
