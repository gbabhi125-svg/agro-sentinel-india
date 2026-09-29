from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import doctor, farm, market, risk, schemes, water
from .storage.db import init_db

app = FastAPI(title="AgroSentinel API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(farm.router)
app.include_router(water.router)
app.include_router(market.router)
app.include_router(schemes.router)
app.include_router(risk.router)
app.include_router(doctor.router)
