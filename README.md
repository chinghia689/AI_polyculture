# PolyAqua Agent

Hệ thống AI hỗ trợ nuôi tôm sú & cua biển xen kẽ (polyculture) tại vùng ngập mặn ĐBSCL.

## Tính năng

| Module | Mô tả |
|--------|-------|
| **Vision** | Upload ảnh tôm → nhận diện 4 loại bệnh bằng YOLOv8 (84% accuracy) |
| **Calculator** | Nhập diện tích, pH, độ mặn → liều vôi, vi sinh, mật độ thả giống |
| **RAG Brain** | Kết hợp chẩn đoán + chỉ số ao → phác đồ điều trị từ 13 tài liệu kỹ thuật |

### Bệnh tôm có thể nhận diện

| Class | Tên bệnh |
|-------|----------|
| `healthy_shrimp` | Tôm khỏe mạnh |
| `black_gill` | Bệnh đen mang |
| `white_spot` | Bệnh đốm trắng (WSSV) |
| `wssv_black_gill` | Đốm trắng + Đen mang (đồng nhiễm) |

---

## Cài đặt

### Yêu cầu

- Python 3.10+
- CUDA (khuyến nghị) hoặc CPU
- 8GB RAM trở lên

### Các bước

```bash
# 1. Clone repo
git clone git@github.com:chinghia689/AI_polyculture.git
cd AI_polyculture

# 2. Tạo môi trường
conda create -n ai_env python=3.10
conda activate ai_env
pip install -r requirements.txt

# 3. Cấu hình API key
cp .env.example .env
# Mở .env, điền OPENAI_API_KEY=sk-...
```

---

## Chuẩn bị dữ liệu

### Tài liệu RAG (13 PDF kỹ thuật thủy sản)

```bash
python scripts/download_documents.py
python scripts/ingest_documents.py
```

Kiểm tra vectordb:
```bash
curl http://localhost:8000/health
# → {"status": "ok", "vectors": 4593}
```

### Dataset ảnh tôm (Vision)

```bash
# Tải ShrimpDiseaseBD từ Kaggle: kaggle.com/datasets/lokotwist/shrimp-disease-image-bd
# Giải nén vào thư mục archive/ trong project root

# Gom và split dataset
python scripts/prepare_vision_dataset.py
# → module_vision/data/dataset/ (train/val/test)
```

### Train model Vision

```bash
python scripts/train_vision.py --epochs 30
# Model lưu tại: module_vision/models/shrimp_disease_cls.pt
# Top-1 accuracy: ~84% val / ~78% test
```

---

## Chạy API

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI: `http://localhost:8000/docs`

---

## API Endpoints

### Vision

```bash
# Nhận diện bệnh từ ảnh
POST /api/v1/vision/predict
  Body: form-data, file=<ảnh tôm>
  → { disease, label_vi, confidence, top5, is_healthy }

# Ảnh + thông số ao → phác đồ điều trị đầy đủ
POST /api/v1/vision/diagnose
  Body: form-data
    file=<ảnh tôm>
    ph=6.5          (tùy chọn)
    salinity=15     (tùy chọn)
    temperature=28  (tùy chọn)
    area_ha=1.5     (tùy chọn)
  → { disease, label_vi, confidence, treatment_plan, sources, lime, probiotic }
```

### Calculator

```bash
POST /api/v1/calculator/stocking   # Mật độ thả giống
POST /api/v1/calculator/lime       # Liều vôi theo pH
POST /api/v1/calculator/probiotic  # Liều vi sinh
POST /api/v1/calculator/schedule   # Lịch thăm ao
```

### Diagnose (RAG)

```bash
POST /api/v1/diagnose/chat         # Hỏi đáp tự do
POST /api/v1/diagnose/             # Chẩn đoán có cấu trúc
```

### Ví dụ curl

```bash
# Nhận diện bệnh từ ảnh + thông số ao
curl -X POST http://localhost:8000/api/v1/vision/diagnose \
  -F "file=@anh_tom.jpg" \
  -F "ph=6.5" \
  -F "salinity=15" \
  -F "temperature=28" \
  -F "area_ha=1.5"

# Hỏi đáp trực tiếp
curl -X POST http://localhost:8000/api/v1/diagnose/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "tôm bị đen mang xử lý như thế nào"}'
```

---

## Chạy tests

```bash
# Tất cả tests
python -m pytest tests/ -v

# Chỉ Vision
python -m pytest tests/vision/ -v

# Chỉ Integration
python -m pytest tests/integration/ -v

# Calculator
python -m pytest module_calculator/tests/ -v
```

---

## Cấu trúc dự án

```
AI_Polyculture/
├── api/
│   ├── main.py              # FastAPI app + lifespan
│   ├── routers/             # calculator.py, diagnose.py, vision.py
│   └── schemas/             # Pydantic models
├── module_calculator/
│   ├── src/                 # stocking, lime, probiotic, schedule
│   └── tests/
├── module_rag/
│   ├── src/
│   │   ├── retrieval/       # E5 + BM25 hybrid retriever (RRF)
│   │   └── generation/      # OpenAI chain
│   └── data/
│       ├── documents/       # 13 PDF kỹ thuật (gitignored)
│       └── vectordb/        # ChromaDB 4593 vectors (gitignored)
├── module_vision/
│   ├── predictor.py         # Inference singleton
│   ├── data/                # Dataset ảnh (gitignored)
│   └── models/              # .pt model (gitignored)
├── scripts/
│   ├── download_documents.py
│   ├── ingest_documents.py
│   ├── prepare_vision_dataset.py
│   └── train_vision.py
├── tests/
│   ├── vision/              # Unit tests predictor
│   └── integration/         # API endpoint tests
├── .env.example
├── requirements.txt
└── docker-compose.yml
```

---

## Tech Stack

| Layer | Công nghệ |
|-------|-----------|
| Vision | YOLOv8n-cls (Ultralytics 8.4.49) |
| Embedding | intfloat/multilingual-e5-base |
| Retrieval | ChromaDB + BM25 (RRF fusion) |
| LLM | OpenAI gpt-5.1 |
| Backend | FastAPI + Pydantic v2 |
| Dataset | ShrimpDiseaseBD (Bangladesh) + iNaturalist |
