from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.logging import configure_logging
from src.core.middleware import request_context_middleware
from src.core.settings import get_settings
from src.db.engine import init_db
from src.routers.audio import router as audio_router
from src.routers.echo import router as echo_router
from src.routers.health import router as health_router
from src.routers.notes import router as notes_router
from src.schemas.envelope import Envelope, envelope
from src.schemas.root import RootPayload


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_db()
    yield


settings = get_settings()
app = FastAPI(title="Echo Notes API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(request_context_middleware)
app.include_router(health_router)
app.include_router(audio_router)
app.include_router(echo_router)
app.include_router(notes_router)


@app.get("/", response_model=Envelope[RootPayload])
async def root() -> Envelope[RootPayload]:
    return envelope(RootPayload())
