from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.documents import router as documents_router
from app.api.v1 import auth, categories, groups, invitations, users
from app.core.errors import APIError, api_error_handler
from app.db.base import SessionLocal
from app.db.seed import seed_default_categories


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(auth.router, prefix="/v1")
app.include_router(users.router, prefix="/v1")
app.include_router(groups.router, prefix="/v1")
app.include_router(categories.router, prefix="/v1")
app.include_router(invitations.router, prefix="/v1")


@app.get("/health")
def health():
    return {"status": "ok"}