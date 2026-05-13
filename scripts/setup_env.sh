#!/usr/bin/env bash
# Setup script for PolyAqua Agent development environment
set -e

echo "=========================================="
echo "  PolyAqua Agent — Environment Setup"
echo "=========================================="

# ── 1. Kiểm tra Python ────────────────────────────────────────────────────────
echo ""
echo "[1/6] Kiểm tra Python >= 3.10..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required="3.10"
if python3 -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)"; then
  echo "  ✓ Python $python_version"
else
  echo "  ✗ Cần Python >= 3.10 (hiện tại: $python_version)"
  exit 1
fi

# ── 2. Tạo virtual environment ────────────────────────────────────────────────
echo ""
echo "[2/6] Tạo virtual environment..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "  ✓ .venv tạo xong"
else
  echo "  ✓ .venv đã tồn tại"
fi

# Activate venv
source .venv/bin/activate

# ── 3. Upgrade pip & cài dependencies ────────────────────────────────────────
echo ""
echo "[3/6] Cài đặt dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "  ✓ Dependencies đã cài xong"

# ── 4. Tạo .env từ .env.example ──────────────────────────────────────────────
echo ""
echo "[4/6] Cấu hình .env..."
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "  ✓ .env tạo từ .env.example"
  echo "  ⚠  Hãy điền ANTHROPIC_API_KEY vào file .env trước khi chạy!"
else
  echo "  ✓ .env đã tồn tại"
fi

# ── 5. Kiểm tra Docker ────────────────────────────────────────────────────────
echo ""
echo "[5/6] Kiểm tra Docker..."
if command -v docker &> /dev/null; then
  echo "  ✓ Docker $(docker --version | awk '{print $3}' | tr -d ',')"
  echo "  Khởi động services (PostgreSQL, MinIO, ChromaDB)..."
  docker compose up -d --quiet-pull 2>/dev/null || docker-compose up -d 2>/dev/null
  echo "  ✓ Services đã khởi động"
else
  echo "  ⚠  Docker chưa cài — bỏ qua services, cần cài Docker để chạy đầy đủ"
fi

# ── 6. Download sentence-transformer model ────────────────────────────────────
echo ""
echo "[6/6] Tải pre-trained embedding model..."
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
print('  ✓ Embedding model đã tải về')
"

echo ""
echo "=========================================="
echo "  Setup hoàn tất!"
echo "=========================================="
echo ""
echo "  Bước tiếp theo:"
echo "  1. Điền ANTHROPIC_API_KEY vào .env"
echo "  2. Tải ảnh tôm/cua: python scripts/crawl_inaturalist.py"
echo "  3. Ingest tài liệu:  python scripts/ingest_documents.py"
echo "  4. Chạy API:         uvicorn api.main:app --reload"
echo ""
