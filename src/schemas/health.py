from pydantic import BaseModel


class HealthPayload(BaseModel):
    status: str = "healthy"
