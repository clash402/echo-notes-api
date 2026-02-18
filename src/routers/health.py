from fastapi import APIRouter

from src.schemas.envelope import Envelope, envelope
from src.schemas.health import HealthPayload

router = APIRouter(tags=["health"])


@router.get("/health", response_model=Envelope[HealthPayload])
async def health() -> Envelope[HealthPayload]:
    return envelope(HealthPayload())
