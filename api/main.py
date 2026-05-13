from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routers import calculator, diagnose, vision

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Preload embedding model + vectordb khi khởi động
    from module_rag.src.retrieval.retriever import _get_collection, _get_model
    from module_vision.predictor import _get_model as _get_vision_model
    _get_model()
    _get_collection()
    _get_vision_model()
    yield


app = FastAPI(
    title="PolyAqua Agent API",
    description="AI hỗ trợ nuôi tôm sú & cua biển xen kẽ — ĐBSCL",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calculator.router, prefix="/api/v1")
app.include_router(diagnose.router,   prefix="/api/v1")
app.include_router(vision.router,     prefix="/api/v1")

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/app", include_in_schema=False)
def frontend():
    return FileResponse("frontend/index.html")


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "PolyAqua Agent API v0.1.0"}


@app.get("/health", tags=["Health"])
def health():
    import chromadb
    client = chromadb.PersistentClient(path="module_rag/data/vectordb")
    coll   = client.get_collection("polyaqua_knowledge")
    return {"status": "ok", "vectors": coll.count()}
