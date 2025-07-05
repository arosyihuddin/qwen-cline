import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.loggging import logger
from src.api.lm_studio import lmstudio
from src.api.ollama import ollama
from src.api import qwen_cline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Check if required environment variables are set before proceeding
required_env_vars = [
    "THINKING",
    "WEB_SEARCH",
    "WEB_DEVELOPMENT",
    "CONTINUE_AGENT_MODE",
    "CONTINUE_AGENT_MODEL",
    "QWEN_AUTH_TOKEN",
    "QWEN_COOKIE",
]

missing_env_vars = [var for var in required_env_vars if os.getenv(var) is None]

if missing_env_vars:
    logger.error("Missing required environment variables:")
    for var in missing_env_vars:
        logger.error(f" - {var}")
    raise EnvironmentError(
        "Some environment variables are missing. Check the logs for details."
    )

# Proceed with logger the environment variable values
logger.info(f"Thinking Mode\t\t:{os.getenv('THINKING')}")
logger.info(f"Web Search Mode\t:{os.getenv('WEB_SEARCH')}")
logger.info(f"Web Development\t:{os.getenv('WEB_DEVELOPMENT')}")
logger.info(f"Continue Agent Mode\t:{os.getenv('CONTINUE_AGENT_MODE')}")
logger.info(f"Continue Agent Model\t:{os.getenv('CONTINUE_AGENT_MODEL')}")
logger.info(f"Qwen Auth Token\t:{os.getenv('QWEN_AUTH_TOKEN')}")
logger.info(f"Qwen Cookie\t:{os.getenv('QWEN_COOKIE')}")

app.include_router(lmstudio.router, tags=["lmstudio"])
app.include_router(ollama.router, tags=["ollama"])
app.include_router(qwen_cline.router, tags=["qwen_cline"])
