from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.config import get_settings
from app.db import init_db
from app.api import trips, incidents, simulate, stream

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")
    yield
    logger.info("Shutting down...")

app = FastAPI(title="GeoAgentic Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trips.router, prefix="/trips", tags=["trips"])
app.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
app.include_router(simulate.router, prefix="/simulate", tags=["simulate"])
app.include_router(stream.router, tags=["stream"])

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
