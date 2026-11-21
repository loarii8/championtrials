import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()
from app.database import Base, engine, SessionLocal, migrate_sqlite_schema
from app.seed import seed
from app.routers import auth, products, orders, analytics, ai, farmers
from app.routers.community import favorites_router, notifications_router, cart_router
from app.routers.research import router as research_router, admin_router as research_admin_router
from app.research_data import import_research_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrate_sqlite_schema(engine)
    db = SessionLocal()
    try:
        seed(db)
        import_research_data(db)
    finally:
        db.close()
    yield


app = FastAPI(title="PejaMarket API", version="1.0.0", lifespan=lifespan)
upload_directory = Path(__file__).resolve().parents[1] / "uploads"
upload_directory.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_directory), name="product-uploads")


def _configured_cors_origins(value: str | None) -> list[str]:
    origins = [
        origin.strip()
        for origin in (value or "http://127.0.0.1:8501,http://localhost:8501").split(",")
        if origin.strip()
    ]
    if "*" in origins:
        raise RuntimeError("CORS_ALLOWED_ORIGINS must contain explicit origins, not '*'.")
    return origins


cors_origins = _configured_cors_origins(os.getenv("CORS_ALLOWED_ORIGINS"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(analytics.router)
app.include_router(ai.router)
app.include_router(farmers.router)
app.include_router(favorites_router)
app.include_router(notifications_router)
app.include_router(cart_router)
app.include_router(research_router)
app.include_router(research_admin_router)


@app.get("/")
def root():
    return {"name": "PejaMarket API", "status": "running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
