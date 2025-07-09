from src.core.types.response import OllamaResponse, Message
import json
from datetime import datetime, timezone


def non_stream_response(model, response):
    message = Message(
        role=response.choices.message.role,
        content=response.choices.message.content,
        tool_calls=response.choices.message.tool_calls,
    )
    return OllamaResponse(model=model, message=message, done=True, done_reason="stop")


def stream_response(model, response):
    for chunk in response:
        yield json.dumps(
            {
                "model": model,
                "create_at": datetime.now(timezone.utc).isoformat(),
                "message": {
                    "role": chunk.choices[0].delta.role,
                    "content": chunk.choices[0].delta.content or "",
                },
                "done": False,
            }
        ) + "\n"

    yield json.dumps(
        {
            "model": model,
            "create_at": datetime.now(timezone.utc).isoformat(),
            "message": {"role": chunk.message.role, "content": ""},
            "done": True,
            "done_reason": "stop",
        }
    ) + "\n"
