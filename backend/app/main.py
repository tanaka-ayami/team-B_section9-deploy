from fastapi import FastAPI

from app.api.v1.documents import router as documents_router

app = FastAPI()

app.include_router(documents_router)


@app.get("/")
def read_root():
    return {"status": "ok"}