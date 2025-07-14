import os
import json
import time
from fastapi import APIRouter, Request
from qwen_api.core.types.chat_model import ChatModel
from fastapi.responses import StreamingResponse
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock
from src.core.loggging import logger

router = APIRouter()
client = Qwen(log_level="DEBUG")


@router.get("/v1/models")
async def models():
    unique_models = set(ChatModel.__args__)
    model_list = []

    # Add original models
    for model_name in unique_models:
        model_list.append(
            {
                "id": model_name,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "user",
                "permission": [],
                "root": model_name,
                "parent": None,
            }
        )

    # Add some OpenAI models that support function calling
    openai_models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]

    for model_name in openai_models:
        model_list.append(
            {
                "id": model_name,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "openai",
                "permission": [],
                "root": model_name,
                "parent": None,
            }
        )

    return {"data": model_list, "object": "list"}


def extract_content_from_qwen_response(qwen_data):
    """Extract content from Qwen response format"""
    content = ""
    if "message" in qwen_data and "blocks" in qwen_data["message"]:
        for block in qwen_data["message"]["blocks"]:
            if block.get("block_type") == "text":
                content += block.get("text", "")
    return content


def extract_content_from_qwen_chunk(qwen_data):
    """Extract content from Qwen streaming chunk"""
    content = ""
    if "choices" in qwen_data and len(qwen_data["choices"]) > 0:
        choice = qwen_data["choices"][0]
        if "delta" in choice and "content" in choice["delta"]:
            content = choice["delta"]["content"]
    return content


def convert_tool_calls_to_openai_format(tool_calls_data):
    """Convert Qwen tool_calls format to OpenAI format"""
    if not tool_calls_data:
        return None

    tool_calls = []
    for i, tool_call in enumerate(tool_calls_data):
        arguments = tool_call["function"]["arguments"]
        if isinstance(arguments, dict):
            arguments = json.dumps(arguments)
        else:
            arguments = str(arguments)

        tool_calls.append(
            {
                "id": f"call_{i}_{int(time.time())}",
                "type": "function",
                "function": {
                    "name": tool_call["function"]["name"],
                    "arguments": arguments,
                },
            }
        )
    return tool_calls


def extract_tool_calls_from_qwen_data(qwen_data):
    """Extract tool_calls from Qwen response data"""
    if (
        "message" in qwen_data
        and "tool_calls" in qwen_data["message"]
        and qwen_data["message"]["tool_calls"]
    ):
        return convert_tool_calls_to_openai_format(qwen_data["message"]["tool_calls"])
    return None


def create_openai_response(model, content, tool_calls=None):
    """Create OpenAI-compatible response format"""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


def create_openai_streaming_chunk(model, created_timestamp, delta, finish_reason=None):
    """Create OpenAI-compatible streaming chunk"""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion.chunk",
        "created": created_timestamp,
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }


async def process_chat_messages(
    get_msg, client, thinking, search, web_development, thinking_budget
):
    """Process and convert messages to Qwen format"""
    messages = []

    for i in get_msg:
        if isinstance(i["content"], str):
            messages.append(
                ChatMessage(
                    role=i["role"],
                    content=i["content"],
                    thinking=thinking,
                    web_search=search,
                    thinking_budget=thinking_budget,
                    web_development=web_development,
                )
            )
        else:
            for y in i["content"]:
                if y["type"] == "image_url":
                    getImageData = await client.chat.async_upload_file(
                        base64_data=y["image_url"]["url"]
                    )
                    messages.append(
                        ChatMessage(
                            role=i["role"],
                            blocks=[
                                ImageBlock(
                                    block_type="image", url=getImageData.file_url
                                )
                            ],
                            thinking=thinking,
                            web_search=search,
                            web_development=web_development,
                        )
                    )
                else:
                    messages.append(
                        ChatMessage(
                            role=i["role"],
                            blocks=[TextBlock(block_type=y["type"], text=y["text"])],
                            thinking=thinking,
                            web_search=search,
                            web_development=web_development,
                        )
                    )
    return messages


@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    payload = await request.json()

    get_msg = payload["messages"]
    stream = payload.get("stream", True)
    tools = payload.get("tools", [])

    # Get model configuration
    model = (
        payload["model"]
        if payload["model"] != "gpt-4o"
        else os.getenv("CONTINUE_AGENT_MODEL")
    )

    # Get environment configurations
    thinking = os.getenv("THINKING") == "true"
    search = os.getenv("WEB_SEARCH") == "true"
    web_development = os.getenv("WEB_DEVELOPMENT") == "true"
    thinking_budget = None
    if model == "qwen3-235b-a22b":
        thinking_budget = int(os.getenv("THINKING_BUDGET"))

    # Process messages
    messages = await process_chat_messages(
        get_msg, client, thinking, search, web_development, thinking_budget
    )

    # Get response from Qwen
    response = await client.chat.acreate(
        model=model, messages=messages, stream=stream, tools=tools
    )

    # Handle non-streaming response
    if not stream:
        qwen_data = response.dict() if hasattr(response, "dict") else response
        content = extract_content_from_qwen_response(qwen_data)
        tool_calls = extract_tool_calls_from_qwen_data(qwen_data)
        return create_openai_response(model, content, tool_calls)

    # Handle streaming response
    async def event_generator():
        logger.info("Starting to stream response")
        created_timestamp = int(time.time())

        async for chunk in response:
            qwen_data = chunk.dict() if hasattr(chunk, "dict") else chunk

            content = extract_content_from_qwen_chunk(qwen_data)
            tool_calls = extract_tool_calls_from_qwen_data(qwen_data)

            # Skip empty chunks unless it's the first chunk or has tool_calls
            if (
                content == ""
                and not tool_calls
                and hasattr(event_generator, "first_chunk_sent")
            ):
                continue

            # Create delta object
            delta = {"content": content}

            # Add role for first chunk
            if not hasattr(event_generator, "first_chunk_sent"):
                delta["role"] = "assistant"
                event_generator.first_chunk_sent = True

            # Add tool_calls if present
            if tool_calls:
                delta["tool_calls"] = tool_calls

            # Create and send chunk
            openai_format = create_openai_streaming_chunk(
                model, created_timestamp, delta
            )
            yield f"data: {json.dumps(openai_format)}\n\n"

        # Send final chunk
        final_chunk = create_openai_streaming_chunk(
            model, created_timestamp, {}, "stop"
        )
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"
        logger.info("Done streaming response")

    return StreamingResponse(event_generator(), media_type="text/event-stream")
