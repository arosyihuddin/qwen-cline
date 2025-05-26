import dotenv
import os
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock
from qwen_api.core.types.chat_model import ChatModel
from qwen_api import Qwen
dotenv.load_dotenv()

app = FastAPI()
client = Qwen()


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
    model = payload['model']
    messages = []
    thinking = True if os.getenv("THINKING") == "true" else False
    search = True if os.getenv("WEB_SEARCH") == "true" else False
    web_dev = True if os.getenv(
        "WEB_DEV") == "true" or model == "qwen-turbo-2025-02-11" else False
    thinking_budget = None
    if model == "qwen3-235b-a22b":
        thinking_budget = os.getenv("THINKING_BUDGET")

    for i in get_msg:
        if type(i["content"]) == str:
            messages.append(ChatMessage(
                role=i['role'], content=i['content'], thinking=thinking, web_search=search, web_development=web_dev, thinking_budget=thinking_budget))
            continue
        else:
            for y in i['content']:
                if y["type"] == "image_url":
                    getImageData = await client.chat.async_upload_file(base64_data=y["image_url"]["url"])
                    messages.append(ChatMessage(role=i['role'], blocks=[
                                    ImageBlock(block_type="image", url=getImageData.file_url)], thinking=thinking, web_search=search, web_development=web_dev))
                else:
                    messages.append(ChatMessage(role=i['role'], blocks=[
                        TextBlock(block_type=y["type"], text=y["text"])], thinking=thinking, web_search=search, web_development=web_dev)
                    )

    stream = await client.chat.acreate(
        model=model,
        messages=messages,
        stream=True,
    )

    async def event_generator():
        async for chunk in stream:
            if chunk.choices[0].delta.role == "function":
                print("Function call detected, skipping chunk")
                continue
            yield f"data: {chunk.json()}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
