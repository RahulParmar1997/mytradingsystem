from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.accounts import router as accounts_router
from app.api.auth import router as auth_router
from app.api.auth import users_router
from app.api.cancel import router as cancel_router
from app.api.fills import router as fills_router
from app.api.orders import router as orders_router
from app.api.positions import router as positions_router
from app.api.risk import router as risk_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title="MyTradingSystem API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(accounts_router)
app.include_router(positions_router)
app.include_router(orders_router)
app.include_router(risk_router)
app.include_router(fills_router)
app.include_router(cancel_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness() -> dict[str, str]:
    return {"status": "ready"}
