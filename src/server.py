import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock
from qwen_api.core.types.chat_model import ChatModel
from qwen_api import Qwen
from src.types import OllamaResponse, Message

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s'
)

app = FastAPI()
client = Qwen()

logging.info(f"Thinking Mode\t\t:{os.getenv('THINKING')}")
logging.info(f"Web Search Mode\t:{os.getenv('WEB_SEARCH')}")
logging.info(f"Web Development\t:{os.getenv('WEB_DEVELOPMENT')}")
logging.info(f"Qwen Auth Token\t:{os.getenv('QWEN_AUTH_TOKEN')}")
logging.info(f"Qwen Cookie\t:{os.getenv('QWEN_COOKIE')}")


@app.get("/")
async def home():
    return HTMLResponse(content="<h2>Qwen Cline Is running</h2>")


# LM Studio API
@app.get("/v1/models")
async def models():
    unique_models = set(ChatModel.__args__)
    model_list = [
        {
            "id": model_name,
            "object": "model",
        }
        for model_name in unique_models
    ]

    return {"data": model_list, "object": "list"}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    payload = await request.json()
    get_msg = payload["messages"]
    model = payload['model'] if payload['model'] != "gpt-4o" else os.getenv(
        'QWEN_AGENT_MODEL')
    messages = []
    thinking = True if os.getenv("THINKING") == "true" else False
    search = True if os.getenv("WEB_SEARCH") == "true" else False
    web_development = True if os.getenv("WEB_DEVELOPMENT") == "true" else False
    thinking_budget = None
    if model == "qwen3-235b-a22b":
        thinking_budget = int(os.getenv("THINKING_BUDGET"))

    for i in get_msg:
        if type(i["content"]) == str:
            messages.append(ChatMessage(
                role=i['role'], content=i['content'], thinking=thinking, web_search=search, thinking_budget=thinking_budget, web_development=web_development))
            continue
        else:
            for y in i['content']:
                if y["type"] == "image_url":
                    getImageData = await client.chat.async_upload_file(base64_data=y["image_url"]["url"])
                    messages.append(ChatMessage(role=i['role'], blocks=[
                                    ImageBlock(block_type="image", url=getImageData.file_url)], thinking=thinking, web_search=search, web_development=web_development))
                else:
                    messages.append(ChatMessage(role=i['role'], blocks=[
                        TextBlock(block_type=y["type"], text=y["text"])], thinking=thinking, web_search=search, web_development=web_development)
                    )

    stream = await client.chat.acreate(
        model=model,
        messages=messages,
        stream=True,
    )

    async def event_generator():
        logging.info("Starting to stream response")
        async for chunk in stream:
            yield f"data: {chunk.json()}\n\n"
        yield "data: [DONE]\n\n"
        logging.info("Done streaming response")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Ollama Route


@app.get("/api/tags")
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


@app.post("/api/chat")
async def ollama_chat(request: Request):
    payload = await request.json()
    get_msg = payload["messages"]
    model = payload['model']
    messages = []
    thinking = True if os.getenv("THINKING") == "true" else False
    search = True if os.getenv("WEB_SEARCH") == "true" else False
    web_development = True if os.getenv("WEB_DEVELOPMENT") == "true" else False
    thinking_budget = None
    if model == "qwen3-235b-a22b":
        thinking_budget = int(os.getenv("THINKING_BUDGET"))

    for i in get_msg:
        if type(i["content"]) == str:
            messages.append(ChatMessage(
                role=i['role'], content=i['content'], thinking=thinking, web_search=search, thinking_budget=thinking_budget, web_development=web_development))
            continue
        else:
            for y in i['content']:
                if y["type"] == "image_url":
                    getImageData = await client.chat.async_upload_file(base64_data=y["image_url"]["url"])
                    messages.append(ChatMessage(role=i['role'], blocks=[
                                    ImageBlock(block_type="image", url=getImageData.file_url)], thinking=thinking, web_search=search, web_development=web_development))
                else:
                    messages.append(ChatMessage(role=i['role'], blocks=[
                        TextBlock(block_type=y["type"], text=y["text"])], thinking=thinking, web_search=search, web_development=web_development)
                    )

    stream = await client.chat.acreate(
        model=model,
        messages=messages,
        stream=False,
    )

    message = Message(role=stream.choices.message.role,
                      content=stream.choices.message.content)
    return OllamaResponse(model=model, message=message, done=True, done_reason="stop")

# Continue Extentions API Route


# @app.post("/v1/api/generate")
# async def completions(request: Request):
#     payload = await request.json()
#     print(payload)
#     model = payload['model']
#     prompt = payload['prompt']
#     messages = [ChatMessage(role="user", content=prompt)]

#     stream = await client.chat.acreate(
#         model=model,
#         messages=messages,
#         stream=True,
#     )

#     async def event_generator():
#         logging.info("Starting to stream response")
#         async for chunk in stream:
#             yield f"data: {chunk.json()}\n\n"
#         yield "data: [DONE]\n\n"
#         logging.info("Done streaming response")

#     return StreamingResponse(event_generator(), media_type="text/event-stream")
