from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.documents import router as documents_router
from app.api.v1.users import router as users_router

app = FastAPI(title="書類・プリント管理アプリ API")

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