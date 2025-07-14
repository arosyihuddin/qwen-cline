import os
from fastapi import APIRouter, Request
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock
from qwen_api.core.types.chat_model import ChatModel
from qwen_api import Qwen
from src.utils.prompt import PARAMETER, TEMPLATE
from .response import non_stream_response, stream_response
from fastapi.responses import StreamingResponse
from src.core.loggging import logger
import json
from datetime import datetime, timezone


router = APIRouter()
client = Qwen(log_level="DEBUG")


@router.get("/api/tags")
async def models():
    unique_models = set(ChatModel.__args__)
    model_list = [
        {
            "name": model_name,
            "model": model_name,
        }
        for model_name in unique_models
    ]

    return {"models": model_list}


@router.post("/api/show")
async def ollama_show(request: Request):
    payload = await request.json()
    model = payload["model"]
    return {
        "parameters": PARAMETER,
        "template": TEMPLATE,
        "model_info": {"general.architecture": model},
        "capabilities": ["completion", "tools"],
    }


@router.post("/api/chat")
async def ollama_chat(request: Request):
    payload = await request.json()
    print(payload)
    try:
        stream = payload["stream"]
    except:
        stream = True

    get_msg = payload["messages"]
    model = payload["model"]
    tools = payload.get("tools", None)
    messages = []
    thinking = True if os.getenv("THINKING") == "true" else False
    search = True if os.getenv("WEB_SEARCH") == "true" else False
    web_development = True if os.getenv("WEB_DEVELOPMENT") == "true" else False
    thinking_budget = None
    if model == "qwen3-235b-a22b":
        thinking_budget = int(os.getenv("THINKING_BUDGET"))

    unique_models = set(ChatModel.__args__)
    if model not in unique_models:
        model = os.getenv("CONTINUE_AGENT_MODEL")

    for i in get_msg:
        if type(i["content"]) == str:
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
            continue
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

    response = client.chat.create(
        model=model,
        messages=messages,
        stream=stream,
        tools=tools if tools is not None else None,
    )

    if stream:
        return StreamingResponse(
            stream_response(model=model, response=response),
            media_type="text/event-stream",
        )
    else:
        return non_stream_response(model=model, response=response)


@router.post("/api/generate")
async def completions(request: Request):
    payload = await request.json()
    model = payload["model"]
    unique_models = set(ChatModel.__args__)
    if model not in unique_models:
        model = os.getenv("CONTINUE_AGENT_MODEL")
    prompt = payload["prompt"]
    messages = [ChatMessage(role="user", content=prompt)]

    stream = await client.chat.acreate(
        model=model,
        messages=messages,
        stream=True,
    )

    async def event_generator():
        async for chunk in stream:
            # Ambil content dari chunk streaming (adjust sesuai API-mu)
            content = chunk.choices[0].delta.content or ""

            yield json.dumps(
                {
                    "model": model,
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "response": content,
                    "done": False,
                }
            ) + "\n"

        yield json.dumps(
            {
                "model": model,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "response": "",
                "done": True,
                "done_reason": "stop",
                "total_duration": 1234567890,
                "load_duration": 123456789,
                "prompt_eval_count": 100,
                "prompt_eval_duration": 456789000,
                "eval_count": 5,
                "eval_duration": 987654321,
            }
        ) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
