import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
XHS_SERVER = "http://127.0.0.1:11901"
LOCAL_CHROME_PATH = ""   # change me necessary for example C:/Program Files/Google/Chrome/Application/chrome.exe

try:
    _default_ai_timeout = int(os.getenv("AI_TIMEOUT", 30))
except (TypeError, ValueError):
    _default_ai_timeout = 30

AI_PROVIDER_SETTINGS = {
    "provider": os.getenv("AI_PROVIDER") or "openai",  # openai、deepseek、glm-4.6
    "api_key": os.getenv("AI_API_KEY") or "",
    "model": os.getenv("AI_MODEL") or "",
    "base_url": os.getenv("AI_BASE_URL") or "",
    "timeout": _default_ai_timeout,
}

AI_ROLE_PROMPT = (
    os.getenv("AI_ROLE_PROMPT")
    or "你是一名资深短视频运营顾问，擅长根据素材、产品与平台特性生成吸引人的中文标题和热门话题。请保持口吻自然、贴合平台内容生态，严格遵守用户提供的约束。"
)
