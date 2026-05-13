# PolyAqua Agent — Kế hoạch triển khai chi tiết

> **Mục tiêu:** Xây dựng hệ thống AI hỗ trợ nông dân nuôi tôm sú & cua biển xen kẽ (polyculture) tại vùng ngập mặn ĐBSCL.
> **Mô hình kinh doanh:** SaaS App (freemium) + Affiliate đại lý vật tư thủy sản.

---

## Tổng quan kiến trúc

```
┌──────────────────────────────────────────────────────────┐
│                      Mobile / Web App                    │
│          (React Native / Next.js + Tailwind)             │
└────────────────────┬─────────────────────────────────────┘
                     │ REST / WebSocket
┌────────────────────▼─────────────────────────────────────┐
│                    FastAPI Backend                        │
│  ┌─────────────┐  ┌───────────────┐  ┌────────────────┐  │
│  │ Module      │  │ Module        │  │ Module RAG     │  │
│  │ Vision      │  │ Calculator    │  │ "Brain"        │  │
│  │ (YOLOv8)   │  │ (Rule+ML)     │  │ (LLM+VectorDB) │  │
│  └─────────────┘  └───────────────┘  └────────────────┘  │
└──────────────────────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│              Data Layer                                  │
│   PostgreSQL  │  MinIO (ảnh)  │  ChromaDB (vectors)      │
└──────────────────────────────────────────────────────────┘
```

---

## PHASE 0 — Chuẩn bị & Nghiên cứu (Tuần 1–2)

### Mục tiêu
- Xác định rõ scope MVP
- Thiết lập môi trường phát triển
- Thu thập tài liệu kỹ thuật ban đầu

### Bước 0.1 — Thiết lập môi trường
```bash
# Python environment
python -m venv .venv && source .venv/bin/activate
pip install torch torchvision ultralytics          # Vision
pip install langchain chromadb sentence-transformers # RAG
pip install fastapi uvicorn sqlalchemy psycopg2    # Backend
pip install pandas numpy scikit-learn              # Calculator
```

### Bước 0.2 — Thu thập tài liệu kỹ thuật cho RAG corpus
Ưu tiên các tài liệu:
- [ ] Quy chuẩn kỹ thuật nuôi tôm sú thương phẩm (TCVN 9117:2011)
- [ ] Kỹ thuật nuôi cua biển xen kẽ tôm sú (Sở NN&PTNT Cà Mau, Bạc Liêu)
- [ ] Hướng dẫn sử dụng men vi sinh Bacillus trong ao nuôi
- [ ] Bảng chẩn đoán bệnh tôm sú phổ biến (NACA, FAO)
- [ ] Kỹ thuật cân bằng pH, độ kiềm, độ mặn vùng ngập mặn

### Bước 0.3 — Định nghĩa nhãn bệnh (Label Schema)

**Tôm sú — 7 lớp bệnh:**
| Nhãn | Mô tả |
|------|-------|
| `healthy_shrimp` | Tôm khỏe mạnh |
| `black_gill` | Đen mang |
| `white_spot` | Đốm trắng (WSSV) |
| `red_body` | Đỏ thân |
| `soft_shell` | Vỏ mềm bất thường |
| `empty_gut` | Ruột rỗng |
| `yellow_head` | Đầu vàng (YHV) |

**Cua biển — 5 lớp bệnh:**
| Nhãn | Mô tả |
|------|-------|
| `healthy_crab` | Cua khỏe mạnh |
| `black_gill_crab` | Đen mang |
| `barnacle` | Đóng rong/hà |
| `limb_loss` | Rụng càng, gãy chân |
| `fungal_crab` | Nấm trên mai |

### Deliverable Phase 0
- [ ] `.env` file cấu hình đầy đủ
- [ ] `docs/label_schema.md` — bảng nhãn hoàn chỉnh
- [ ] `docs/rag_corpus_list.md` — danh sách tài liệu cần thu thập
- [ ] `scripts/setup_env.sh` — script tự động cài môi trường

---

## PHASE 1 — Module Vision: Bác sĩ AI (Tuần 3–7)

### Mục tiêu
Xây dựng mô hình nhận diện bệnh tôm/cua từ ảnh chụp bằng điện thoại.

### Bước 1.1 — Thu thập & Gán nhãn dữ liệu ảnh

**Chiến lược thu thập:**
```
Nguồn 1: Crawl Google Images, iNaturalist theo từ khóa (tôm đen mang, white spot disease shrimp)
Nguồn 2: Liên hệ Sở NN&PTNT hoặc trại giống địa phương xin ảnh thực tế
Nguồn 3: Synthetic Data — dùng Stable Diffusion tạo ảnh tôm bệnh bổ sung
```

**Mục tiêu dataset tối thiểu:**
- 200 ảnh/lớp × 12 lớp = ~2,400 ảnh raw
- Sau augmentation: ~10,000 ảnh

**Tool gán nhãn:** Roboflow (free tier) hoặc Label Studio (self-hosted)

### Bước 1.2 — Augmentation Pipeline

File: `module_vision/src/dataset/augmentation.py`

```python
# Augmentation đặc biệt cho ảnh chụp ao nuôi ngoài trời
transforms = [
    RandomHorizontalFlip(p=0.5),
    RandomBrightness(limit=0.3),       # ánh sáng mặt trời thay đổi
    RandomGaussianBlur(blur_limit=3),   # ảnh chụp tay bị rung
    RandomShadow(),                     # bóng đổ trên mặt nước
    ColorJitter(hue=0.1),              # màu sắc thay đổi theo độ mặn
]
```

### Bước 1.3 — Train YOLOv8

```bash
# Fine-tune YOLOv8n (nano) — nhẹ nhất, phù hợp mobile
yolo train model=yolov8n.pt data=configs/polyaqua.yaml epochs=100 imgsz=640

# Hoặc YOLOv8s (small) nếu cần độ chính xác cao hơn
yolo train model=yolov8s.pt data=configs/polyaqua.yaml epochs=100 imgsz=640
```

**File config:** `module_vision/configs/polyaqua.yaml`
```yaml
path: ../data
train: labeled/train
val: labeled/val
nc: 12
names: [healthy_shrimp, black_gill, white_spot, red_body, soft_shell,
        empty_gut, yellow_head, healthy_crab, black_gill_crab,
        barnacle, limb_loss, fungal_crab]
```

### Bước 1.4 — Test-Time Augmentation (TTA) khi inference

```python
# module_vision/src/inference/predict.py
def predict_with_tta(model, image_path, conf=0.5):
    results = []
    for augment in [False, True]:  # TTA bật/tắt
        result = model.predict(image_path, augment=augment, conf=conf)
        results.append(result)
    return ensemble_results(results)
```

### Bước 1.5 — Export sang ONNX / CoreML cho mobile

```bash
yolo export model=best.pt format=onnx   # Android
yolo export model=best.pt format=coreml # iOS
```

### Metrics mục tiêu
| Metric | Mục tiêu |
|--------|----------|
| mAP@50 | ≥ 0.80 |
| Inference time (CPU) | ≤ 500ms |
| Inference time (GPU) | ≤ 100ms |

### Deliverable Phase 1
- [ ] Dataset đã gán nhãn, upload lên Roboflow
- [ ] Checkpoint `module_vision/models/best.pt`
- [ ] `module_vision/models/best.onnx` (cho mobile)
- [ ] Notebook đánh giá: `module_vision/notebooks/evaluation.ipynb`
- [ ] API endpoint: `POST /api/v1/vision/diagnose`

---

## PHASE 2 — Module Calculator: Tính toán Ao nuôi (Tuần 6–9)

### Mục tiêu
Tính toán chính xác mật độ thả giống, liều lượng hóa chất, lịch thăm ao.

### Bước 2.1 — Công thức cốt lõi (Rule-based)

File: `module_calculator/src/stocking_calculator.py`

**Mật độ thả giống tối ưu (nuôi xen kẽ):**
```python
SHRIMP_DENSITY_PER_HA = 15  # con/m² — mật độ tôm sú xen kẽ
CRAB_DENSITY_PER_HA = 0.5   # con/m² — mật độ cua biển

def calculate_stocking(area_ha: float, model: str = "extensive"):
    """
    model: 'extensive' (quảng canh), 'semi_intensive' (bán thâm canh)
    """
    area_m2 = area_ha * 10_000
    if model == "extensive":
        shrimp_count = int(area_m2 * 5)   # 5 PL/m²
        crab_count   = int(area_m2 * 0.3) # 0.3 cua/m²
    else:
        shrimp_count = int(area_m2 * 15)
        crab_count   = int(area_m2 * 0.5)
    return {"shrimp_pl": shrimp_count, "crab_juveniles": crab_count}
```

**Tính liều lượng vôi theo pH:**
```python
LIME_TABLE = {
    # pH_range: (kg_dolomite/ha, kg_agricultural_lime/ha)
    (0, 4.0): (3000, 2000),
    (4.0, 5.0): (2000, 1500),
    (5.0, 6.0): (1000, 750),
    (6.0, 6.5): (500, 300),
    (6.5, 7.5): (0, 0),       # pH lý tưởng
    (7.5, 8.5): (0, 0),
    (8.5, 9.0): (200, 0),     # dùng thạch cao hạ pH
}

def calculate_lime_dose(current_ph: float, area_ha: float) -> dict:
    for (low, high), (dolomite, lime) in LIME_TABLE.items():
        if low <= current_ph < high:
            return {
                "dolomite_kg": dolomite * area_ha,
                "lime_kg": lime * area_ha,
                "warning": "pH nguy hiểm" if current_ph < 5.0 else None
            }
```

**Liều lượng vi sinh Bacillus:**
```python
def calculate_probiotic_dose(area_ha: float, temperature_c: float,
                              days_since_last_dose: int) -> dict:
    base_dose_kg_per_ha = 1.0
    # Nhiệt độ cao → vi khuẩn nhân nhanh hơn → giảm liều
    temp_factor = 1.2 if temperature_c < 28 else 0.8
    urgency_factor = min(days_since_last_dose / 7, 2.0)
    dose = base_dose_kg_per_ha * temp_factor * urgency_factor * area_ha
    return {"probiotic_kg": round(dose, 2), "apply_time": "18:00–20:00"}
```

### Bước 2.2 — Lịch thăm ao thông minh

File: `module_calculator/src/schedule_engine.py`

```python
# Lịch thăm ao mặc định (tuỳ theo giai đoạn)
SCHEDULE_RULES = {
    "month_1_2": {"check_trap_days": 3, "water_test_days": 2},
    "month_3_4": {"check_trap_days": 2, "water_test_days": 2},
    "harvest_season": {"check_trap_days": 1, "water_test_days": 1},
}

def generate_schedule(start_date, area_ha, stocking_model):
    # Trả về lịch JSON để app push notification
    ...
```

### Bước 2.3 — ML nâng cao (Optional — sau MVP)
Dùng XGBoost hoặc LightGBM train trên dữ liệu lịch sử ao nuôi để:
- Dự báo năng suất thu hoạch
- Phát hiện bất thường sớm từ chuỗi dữ liệu môi trường

### Deliverable Phase 2
- [ ] `module_calculator/src/stocking_calculator.py`
- [ ] `module_calculator/src/lime_calculator.py`
- [ ] `module_calculator/src/probiotic_calculator.py`
- [ ] `module_calculator/src/schedule_engine.py`
- [ ] `module_calculator/tests/` — unit tests đầy đủ
- [ ] API endpoint: `POST /api/v1/calculator/recommend`

---

## PHASE 3 — Module RAG Brain: Hệ chuyên gia (Tuần 8–13)

### Mục tiêu
Tổng hợp output từ Vision + Calculator → sinh ra phác đồ xử lý ngôn ngữ tự nhiên.

### Bước 3.1 — Xây dựng RAG Pipeline

**Stack:**
```
Documents (PDF/DOCX) → LangChain Loader → Text Splitter
→ Embedding (sentence-transformers/paraphrase-multilingual) 
→ ChromaDB (Vector Store, self-hosted)
→ Retriever → LLM (Claude claude-sonnet-4-6 via API)
→ Response
```

### Bước 3.2 — Ingestion Pipeline

File: `module_rag/src/ingestion/ingest.py`

```python
from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

def ingest_documents(docs_dir: str, persist_dir: str):
    loader = DirectoryLoader(docs_dir, glob="**/*.pdf", loader_cls=PyPDFLoader)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    vectordb = Chroma.from_documents(chunks, embeddings, persist_directory=persist_dir)
    vectordb.persist()
    print(f"Ingested {len(chunks)} chunks from {len(docs)} documents")
```

### Bước 3.3 — Query & Generation Pipeline

File: `module_rag/src/generation/chain.py`

```python
from langchain.chains import RetrievalQA
from langchain_anthropic import ChatAnthropic

SYSTEM_PROMPT = """
Bạn là chuyên gia thủy sản tại vùng ĐBSCL, chuyên về mô hình nuôi tôm sú và cua biển xen kẽ.
Hãy trả lời ngắn gọn, thực tế, dùng đơn vị đo lường phổ biến tại địa phương (ha, kg, lít).
Không dùng thuật ngữ học thuật phức tạp. Nếu cần, hãy đưa ra liều lượng và thời điểm xử lý cụ thể.
Ưu tiên các giải pháp sinh học (men vi sinh, thảo dược) trước khi dùng hóa chất.
"""

def build_rag_chain(vectordb):
    llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=1024)
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    return chain
```

### Bước 3.4 — Orchestration: Kết hợp 3 module

File: `api/services/orchestrator.py`

```python
async def full_diagnosis(image_path: str, farm_params: dict) -> dict:
    # 1. Vision — chẩn đoán bệnh
    vision_result = vision_service.predict(image_path)

    # 2. Calculator — tính liều lượng
    calc_result = calculator_service.recommend(
        disease=vision_result["disease"],
        ph=farm_params["ph"],
        salinity=farm_params["salinity"],
        area_ha=farm_params["area_ha"]
    )

    # 3. RAG Brain — sinh phác đồ tự nhiên
    query = f"""
    Tôm sú bị {vision_result['disease']} (độ tin cậy {vision_result['confidence']:.0%}).
    Ao {farm_params['area_ha']} ha, pH={farm_params['ph']}, độ mặn={farm_params['salinity']}‰.
    Máy tính đề xuất: {calc_result}.
    Hãy đưa ra phác đồ xử lý chi tiết.
    """
    rag_response = rag_chain.run(query)

    return {
        "diagnosis": vision_result,
        "recommendation": calc_result,
        "treatment_plan": rag_response,
        "generated_at": datetime.utcnow().isoformat()
    }
```

### Deliverable Phase 3
- [ ] `module_rag/data/documents/` — ≥ 10 tài liệu kỹ thuật đã ingested
- [ ] `module_rag/data/vectordb/` — ChromaDB đã build
- [ ] `module_rag/src/ingestion/ingest.py`
- [ ] `module_rag/src/generation/chain.py`
- [ ] `api/services/orchestrator.py`
- [ ] API endpoint: `POST /api/v1/diagnose` (tích hợp 3 module)

---

## PHASE 4 — Backend API & Integration (Tuần 12–15)

### Stack
- **Framework:** FastAPI
- **DB:** PostgreSQL (user data, farm data, history)
- **File Storage:** MinIO (lưu ảnh upload)
- **Auth:** JWT + OAuth2
- **Notification:** Zalo OA API (push thông báo lịch thăm ao)

### API Endpoints chính

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login

POST   /api/v1/farms/                    # Tạo hồ sơ ao
GET    /api/v1/farms/{farm_id}
PUT    /api/v1/farms/{farm_id}/params    # Cập nhật pH, độ mặn

POST   /api/v1/diagnose                  # Chẩn đoán (3 module)
GET    /api/v1/diagnose/history/{farm_id}

POST   /api/v1/calculator/stocking      # Tính mật độ thả
POST   /api/v1/calculator/lime          # Tính liều vôi
POST   /api/v1/calculator/probiotic     # Tính liều vi sinh
GET    /api/v1/schedule/{farm_id}       # Lịch thăm ao

GET    /api/v1/marketplace/products     # Affiliate sản phẩm
```

### Deliverable Phase 4
- [ ] `api/` — FastAPI app hoàn chỉnh
- [ ] `docker-compose.yml` — PostgreSQL + MinIO + ChromaDB
- [ ] Postman Collection đầy đủ
- [ ] CI/CD pipeline (GitHub Actions)

---

## PHASE 5 — Frontend / Mobile App (Tuần 14–20)

### Phương án A — Web App (ưu tiên MVP)
- **Stack:** Next.js 14 + Tailwind CSS + shadcn/ui
- Deploy: Vercel (free tier)

### Phương án B — Mobile App (sau MVP)
- **Stack:** React Native + Expo
- Camera integration: `expo-camera`
- Offline mode: SQLite cache cho lịch thăm ao

### Màn hình chính (MVP)
```
1. Trang chủ        — Dashboard tổng quan ao nuôi
2. Chẩn đoán        — Chụp ảnh → AI phân tích → Phác đồ
3. Máy tính         — Nhập thông số → Kết quả tính toán
4. Lịch thăm ao     — Calendar + Push notification
5. Cửa hàng         — Affiliate sản phẩm vật tư
6. Hỏi đáp AI       — Chat với RAG Brain
```

---

## PHASE 6 — Testing & Hardening (Tuần 18–21)

### Kiểm thử Vision Module
```bash
# Đánh giá trên test set thực tế
yolo val model=best.pt data=polyaqua.yaml split=test

# Kiểm tra edge case: ảnh mờ, tối, góc chụp lạ
python scripts/test_edge_cases.py --input tests/vision/edge_cases/
```

### Kiểm thử Calculator
```bash
pytest tests/calculator/ -v --cov=module_calculator
# Mục tiêu: coverage ≥ 90%
```

### Kiểm thử RAG
```bash
# Đánh giá chất lượng câu trả lời (RAGAS framework)
python scripts/evaluate_rag.py --questions tests/rag/eval_questions.json
```

---

## PHASE 7 — Launch & Monetization (Tuần 22–24)

### Go-to-market
- [ ] Pilot với 5–10 hộ nông dân tại Cà Mau / Bạc Liêu
- [ ] Thu thập feedback thực tế → cải thiện model
- [ ] Liên hệ 2–3 đại lý vật tư thủy sản địa phương ký thỏa thuận Affiliate

### Pricing Tier
| Tier | Giá | Tính năng |
|------|-----|-----------|
| Free | 0đ | Chẩn đoán 5 ảnh/tháng, Calculator cơ bản |
| Pro | 99k/tháng | Không giới hạn, lịch thăm ao, push notification |
| Enterprise | Thương lượng | Multi-farm, API access, white-label |

---

## Timeline tổng quan

```
Tuần  1– 2: Phase 0 — Chuẩn bị
Tuần  3– 7: Phase 1 — Module Vision
Tuần  6– 9: Phase 2 — Module Calculator (song song Phase 1)
Tuần  8–13: Phase 3 — Module RAG Brain
Tuần 12–15: Phase 4 — Backend API
Tuần 14–20: Phase 5 — Frontend/Mobile
Tuần 18–21: Phase 6 — Testing
Tuần 22–24: Phase 7 — Launch
```

**Tổng thời gian: ~6 tháng (1 dev full-stack + 1 ML engineer)**

---

## Tech Stack tóm tắt

| Layer | Technology |
|-------|-----------|
| Vision | YOLOv8 (Ultralytics), OpenCV, ONNX |
| ML/Calculator | scikit-learn, XGBoost, pandas |
| RAG | LangChain, ChromaDB, sentence-transformers |
| LLM | Claude claude-sonnet-4-6 (Anthropic API) |
| Backend | FastAPI, PostgreSQL, MinIO, Redis |
| Frontend | Next.js 14, React Native, Expo |
| DevOps | Docker, GitHub Actions, Vercel |
| Notification | Zalo OA API |

---

## Risk & Mitigation

| Rủi ro | Xác suất | Giải pháp |
|--------|----------|-----------|
| Thiếu dữ liệu ảnh bệnh | Cao | Synthetic data + liên hệ trại giống |
| Nông dân không quen app | Trung bình | UX đơn giản, hỗ trợ Zalo OA |
| Chi phí LLM API | Thấp | Cache phổ biến, prompt ngắn gọn |
| Độ chính xác Vision thấp | Trung bình | TTA + ensemble, human-in-the-loop |
| Cạnh tranh từ app lớn | Thấp | Tập trung polyculture — ngách chưa ai làm |
