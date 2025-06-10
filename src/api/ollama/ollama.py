import os
from fastapi import APIRouter, Request
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock
from qwen_api.core.types.chat_model import ChatModel
from qwen_api import Qwen
from src.core.types.response import OllamaResponse, Message

router = APIRouter()
client = Qwen()


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


@router.post("/api/chat")
async def ollama_chat(request: Request):
    payload = await request.json()
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
        stream=False,
        tools=tools if tools is not None else None,
    )

    message = Message(
        role=response.choices.message.role,
        content=response.choices.message.content,
        tool_calls=response.choices.message.tool_calls,
    )

    return OllamaResponse(model=model, message=message, done=True, done_reason="stop")


# @router.post("/v1/api/generate")
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
