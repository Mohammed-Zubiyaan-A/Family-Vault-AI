import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import init_db
from routers import documents, qa, system

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="FamilyVault AI", version="0.1.0")

# MVP: wide-open CORS for local dev (frontend on a different port).
# Tighten this before anything resembling a public deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(qa.router)
app.include_router(system.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
