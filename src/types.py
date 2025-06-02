from typing import Optional
from pydantic import BaseModel


class DeltaResponse(BaseModel):
    type: Optional[str] = ""
    text: Optional[str] = ""
    stop_reason: Optional[str] = ""
    stop_sequence: Optional[str] = ""


class ResponseAutoCompletions(BaseModel):
    type: str
    message: Optional[str] = ""
    index: Optional[int] = 0
    delta: DeltaResponse
    role: Optional[str] = None


class Message(BaseModel):
    role: str
    content: str


class OllamaResponse(BaseModel):
    model: str
    create_at: str = ""
    message: Message
    done_reason: Optional[str] = None
    done: bool
