import os
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Request, UploadFile, File
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock
from fastapi.responses import StreamingResponse
from src.core.loggging import logger
from src.utils.file_handler import FileHandler

router = APIRouter()
client = Qwen()


@router.get("/")
async def home():
    return HTMLResponse(content="<h2>Qwen Cline Is running</h2>")


@router.post("/api/v1/qwen/upload")
async def upload(file: UploadFile = File(...)):
    temp_path = await FileHandler.save_temp_file(file)
    getdataImage = client.chat.upload_file(file_path=temp_path)
    FileHandler.cleanup_temp_file(temp_path)
    return getdataImage


@router.post("/api/v1/qwen/completions")
async def completions(request: Request):
    payload = await request.json()
    messages = []
    for msg in payload["messages"]:
        if type(msg["content"]) == str:
            messages.append(ChatMessage(role=msg["role"], content=msg["content"]))
        else:
            for y in msg["content"]:
                if y["type"] == "image":
                    messages.append(
                        ChatMessage(
                            role=msg["role"],
                            blocks=[ImageBlock(block_type="image", url=y["image"])],
                        )
                    )
                else:
                    messages.append(
                        ChatMessage(
                            role=msg["role"],
                            blocks=[TextBlock(block_type="text", text=y["text"])],
                        )
                    )

    response = await client.chat.acreate(
        model=payload["model"],
        messages=messages,
        stream=False,
    )

    return response


@router.post("/v1/completions")
async def completions(request: Request):
    payload = await request.json()
    model = (
        payload["model"]
        if payload["model"] != "gpt-4o"
        else os.getenv("QWEN_AGENT_MODEL")
    )
    thinking = True if os.getenv("THINKING") == "true" else False
    search = True if os.getenv("WEB_SEARCH") == "true" else False
    web_development = True if os.getenv("WEB_DEVELOPMENT") == "true" else False
    thinking_budget = None
    if model == "qwen3-235b-a22b":
        thinking_budget = int(os.getenv("THINKING_BUDGET"))
    messages = [
        ChatMessage(
            role="user",
            content=payload["prompt"],
            thinking=thinking,
            web_search=search,
            thinking_budget=thinking_budget,
            web_development=web_development,
        )
    ]

    stream = await client.chat.acreate(
        model=model,
        messages=messages,
        stream=True,
    )

    async def event_generator():
        logger.info("Starting to stream response")
        async for chunk in stream:
            yield f"data: {chunk.json()}\n\n"
        yield "data: [DONE]\n\n"
        logger.info("Done streaming response")

    return StreamingResponse(event_generator(), media_type="text/event-stream")
