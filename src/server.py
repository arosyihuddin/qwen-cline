from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock
from qwen_api.core.types.chat_model import ChatModel
from qwen_api import Qwen
import dotenv
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
    for i in get_msg:
        if type(i["content"]) == str:
            messages.append(ChatMessage(role=i['role'], content=i['content']))
            continue
        else:
            for y in i['content']:
                if y["type"] == "image_url":
                    getImageData = await client.chat.async_upload_file(base64_data=y["image_url"]["url"])
                    messages.append(ChatMessage(role=i['role'], blocks=[
                                    ImageBlock(block_type="image", url=getImageData.file_url)]))
                else:
                    messages.append(ChatMessage(role=i['role'], blocks=[
                        TextBlock(block_type=y["type"], text=y["text"])])
                    )

    stream = await client.chat.acreate(
        model=model,
        messages=messages,
        stream=True,
    )

    async def event_generator():
        async for chunk in stream:
            yield f"data: {chunk.json()}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
