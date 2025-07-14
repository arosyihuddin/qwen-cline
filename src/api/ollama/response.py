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
        # Get role and content from delta
        delta_role = (
            chunk.choices[0].delta.role if chunk.choices[0].delta.role else None
        )
        delta_content = chunk.choices[0].delta.content or ""

        # Get tool_calls from message and convert to dict for JSON serialization
        tool_calls = None
        if chunk.message.tool_calls:
            tool_calls = []
            for tool_call in chunk.message.tool_calls:
                tool_calls.append(
                    {
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        }
                    }
                )

        yield json.dumps(
            {
                "model": model,
                "create_at": datetime.now(timezone.utc).isoformat(),
                "message": {
                    "role": delta_role,
                    "content": delta_content,
                    "tool_calls": tool_calls,
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
