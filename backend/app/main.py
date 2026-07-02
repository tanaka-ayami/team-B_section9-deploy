from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.documents import router as documents_router
from app.api.v1 import auth, billing, categories, groups, invitations, users
from app.core.errors import APIError, api_error_handler
from app.api.v1.notifications import router as notifications_router
from app.db.base import SessionLocal
from app.db.seed import seed_default_categories
from app.core.config import settings
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        seed_default_categories(db)
    finally:
        db.close()
    yield

app = FastAPI(title="書類・プリント管理アプリ API", lifespan=lifespan)
app.add_exception_handler(APIError, api_error_handler)

cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    cors_origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(notifications_router)
app.include_router(auth.router, prefix="/v1")
app.include_router(users.router, prefix="/v1")
app.include_router(groups.router, prefix="/v1")
app.include_router(categories.router, prefix="/v1")
app.include_router(invitations.router, prefix="/v1")
app.include_router(billing.router, prefix="/v1")

@app.get("/health")
def health():
    return {"status": "ok"}