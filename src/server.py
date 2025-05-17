from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from qwen_api.types.chat import ChatMessage
from qwen_api.types.chat_model import ChatModel
from llama_index.core.base.llms.types import TextBlock
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
    get_msg = payload.get("messages", [])
    messages = []
    for i in get_msg:
        if type(i["content"]) == str:
            messages.append(ChatMessage(role=i['role'], content=i['content']))
            continue
        else:
            for y in i['content']:
                messages.append(ChatMessage(role=i['role'], blocks=[
                                TextBlock(block_type=y["type"], text=y["text"])]))

    stream = await client.chat.acreate(messages=messages, stream=True)

    async def event_generator():
        async for chunk in stream:
            yield f"data: {chunk.json()}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
