from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.documents import router as documents_router
from app.api.v1.users import router as users_router
from app.db.base import SessionLocal
from app.db.seed import seed_default_categories


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時：共通カテゴリ（学校・医療・行政・保険・その他）をシーディング（issue #12 MVP外対応）
    db = SessionLocal()
    try:
        seed_default_categories(db)
    finally:
        db.close()
    yield


app = FastAPI(title="書類・プリント管理アプリ API", lifespan=lifespan)

# FEはlocalhost:3000から叩く想定（本番ではVercelのドメインに変更）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(users_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}