from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List
from dotenv import load_dotenv

load_dotenv(override=True)


class Settings(BaseSettings):
    CORS_ORIGINS: List[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]

    QWEN_AUTH_TOKEN: str
    QWEN_COOKIE: str
    QWEN_AGENT_MODEL: str
    WEB_SEARCH: str
    WEB_DEVELOPMENT: str
    THINKING: str
    THINKING_BUDGET: str

    model_config = ConfigDict(extra="allow")


settings = Settings()
