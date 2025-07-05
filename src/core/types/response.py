from typing import Optional
from pydantic import BaseModel
from qwen_api.core.types.response.function_tool import ToolCall
from datetime import datetime


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
    tool_calls: Optional[list[ToolCall]] = None


class OllamaResponse(BaseModel):
    model: str
    create_at: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message: Message
    done_reason: Optional[str] = None
    done: bool
