from fastapi import APIRouter

from src.schemas.envelope import Envelope, envelope
from src.schemas.reflection import EchoRequest, Reflection
from src.services.reflection import reflect_transcript

router = APIRouter(tags=["echo"])


@router.post("/echo", response_model=Envelope[Reflection])
async def echo(payload: EchoRequest) -> Envelope[Reflection]:
    reflection_result = reflect_transcript(payload.transcript)
    return envelope(reflection_result.reflection)
