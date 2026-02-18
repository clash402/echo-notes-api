from pydantic import BaseModel


class RootPayload(BaseModel):
    message: str = "Echo Notes API"
