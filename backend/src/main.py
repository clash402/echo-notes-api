from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.src.core.logging import configure_logging
from backend.src.core.middleware import request_context_middleware
from backend.src.db.engine import init_db
from backend.src.routers.audio import router as audio_router
from backend.src.routers.echo import router as echo_router
from backend.src.routers.health import router as health_router
from backend.src.routers.notes import router as notes_router
from backend.src.schemas.envelope import Envelope, envelope
from backend.src.schemas.root import RootPayload


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_db()
    yield


app = FastAPI(title="Echo Notes API", lifespan=lifespan)
app.middleware("http")(request_context_middleware)
app.include_router(health_router)
app.include_router(audio_router)
app.include_router(echo_router)
app.include_router(notes_router)


@app.get("/", response_model=Envelope[RootPayload])
async def root() -> Envelope[RootPayload]:
    return envelope(RootPayload())
