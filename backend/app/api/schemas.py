from pydantic import BaseModel


class ErrorEnvelope(BaseModel):
    error: str
    code: str
    detail: str = ""
