import json
import logging
import re
from typing import Dict, List, Optional, Sequence

import requests

from conf import AI_PROVIDER_SETTINGS, AI_ROLE_PROMPT

logger = logging.getLogger(__name__)

DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "glm-4.6": "https://open.bigmodel.cn/api/paas/v4",
}

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "deepseek": "deepseek-chat",
    "glm-4.6": "glm-4.6",
}

VALID_TARGETS = {"title", "topics", "xhs_title"}

PROVIDER_ALIASES = {
    "gpt": "openai",
    "openai": "openai",
    "deepseek": "deepseek",
    "deep-seek": "deepseek",
    "glm": "glm-4.6",
    "glm4.6": "glm-4.6",
    "glm-4.6": "glm-4.6",
}


class AIServiceError(ValueError):
    """Raised when AI generation fails."""


def generate_ai_content(targets: Sequence[str], context: Optional[Dict] = None) -> Dict:
    normalized_targets = _normalize_targets(targets)
    if not normalized_targets:
        raise AIServiceError("targets 参数不能为空")

    context = context or {}
    messages = _build_prompt(normalized_targets, context)
    raw_response = _call_chat_completion(messages)
    payload = _parse_response(raw_response)
    result = _extract_targets(payload, normalized_targets)

    missing = [item for item in normalized_targets if item not in result]
    if missing:
        raise AIServiceError(f"AI 未能生成所需内容: {', '.join(missing)}")

    return result


def _normalize_targets(targets: Sequence[str]) -> List[str]:
    seen = set()
    ordered = []
    for target in targets or []:
        if not isinstance(target, str):
            continue
        key = target.strip().lower()
        if key in VALID_TARGETS and key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


def _build_prompt(targets: List[str], context: Dict) -> List[Dict[str, str]]:
    platform_name = context.get("platformName") or context.get("platform_name") or "不限平台"
    product_title = context.get("productTitle") or context.get("product_title") or ""
    product_link = context.get("productLink") or context.get("product_link") or ""
    existing_title = context.get("existingTitle") or context.get("existing_title") or ""
    existing_xhs_title = context.get("existingXhsTitle") or context.get("existing_xhs_title") or ""
    existing_topics = context.get("existingTopics") or context.get("existing_topics") or []
    file_names = context.get("fileNames") or context.get("file_names") or []

    target_desc = []
    if "title" in targets:
        target_desc.append("一个不超过100个中文字符、吸引用户的短视频标题")
    if "xhs_title" in targets:
        target_desc.append("一条不超过20个中文字符的小红书专用标题")
    if "topics" in targets:
        target_desc.append("3-5个热门中文话题（不带#符号）")
    target_text = "，并".join(target_desc) if len(target_desc) > 1 else target_desc[0]

    user_prompt = "\n".join([
        f"目标平台：{platform_name}",
        f"商品/作品信息：{product_title or '无'}",
        f"商品链接：{product_link or '无'}",
        f"已有标题：{existing_title or '无'}",
        f"已有话题：{', '.join(existing_topics) or '无'}",
        f"已有小红书标题：{existing_xhs_title or '无'}",
        f"视频素材名称：{', '.join(file_names) or '无'}",
        f"请根据以上信息生成{target_text}。",
        "输出格式必须是 JSON，示例：{\"title\": \"...\", \"xhs_title\": \"...\", \"topics\": [\"话题1\", \"话题2\"]}",
        "只返回 JSON 内容，不要包含解释或代码块。",
        "确保话题项不包含#符号。",
    ])

    return [
        {
            "role": "system",
            "content": AI_ROLE_PROMPT or "你是一个短视频运营助手，负责为视频生成中文标题和热门话题。",
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]


def _call_chat_completion(messages: List[Dict[str, str]]) -> str:
    provider = _resolve_provider()
    api_key = (AI_PROVIDER_SETTINGS.get("api_key") or "").strip()
    if not api_key:
        raise AIServiceError("AI API Key 未配置")

    base_url = (AI_PROVIDER_SETTINGS.get("base_url") or "").rstrip("/")
    if not base_url:
        base_url = DEFAULT_BASE_URLS.get(provider, "").rstrip("/")
    if not base_url:
        raise AIServiceError(f"未找到 {provider} 的 API 地址")

    model = (AI_PROVIDER_SETTINGS.get("model") or "").strip() or DEFAULT_MODELS.get(provider)
    if not model:
        raise AIServiceError(f"{provider} 缺少默认模型配置")

    timeout = AI_PROVIDER_SETTINGS.get("timeout") or 60
    try:
        timeout = int(timeout)
    except (TypeError, ValueError):
        timeout = 30

    retries = AI_PROVIDER_SETTINGS.get("max_retries", 2)
    try:
        retries = int(retries)
    except (TypeError, ValueError):
        retries = 2

    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.6,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    attempt = 0
    last_error = None
    while attempt <= retries:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            response_json = response.json()
            break
        except requests.exceptions.Timeout as exc:
            last_error = exc
            logger.warning("AI provider timeout on attempt %s/%s", attempt + 1, retries + 1)
            if attempt >= retries:
                raise AIServiceError(f"AI 调用超时，请稍后重试 ({timeout}s)") from exc
            attempt += 1
            continue
        except requests.RequestException as exc:
            logger.exception("AI provider request failed")
            raise AIServiceError(f"AI 调用失败: {exc}") from exc
        except ValueError as exc:
            raise AIServiceError("AI 返回数据不是有效的 JSON") from exc
    else:
        # should not reach here; guard for completeness
        raise AIServiceError("AI 调用失败，请稍后重试") from last_error

    choices = response_json.get("choices")
    if not choices:
        raise AIServiceError("AI 返回为空")

    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = (message or {}).get("content")
    if not content:
        raise AIServiceError("AI 未返回内容")
    return content


def _parse_response(content: str) -> Dict:
    text = content.strip()
    if not text:
        raise AIServiceError("AI 返回内容为空")

    # 去除代码块
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        if "```" in text:
            text = text.split("```", 1)[0].strip()

    possible_json = _extract_json_snippet(text)

    if not possible_json:
        raise AIServiceError("AI 返回内容无法解析为 JSON")

    try:
        return json.loads(possible_json)
    except json.JSONDecodeError as exc:
        raise AIServiceError("AI 返回内容不是有效的 JSON") from exc


def _extract_json_snippet(text: str) -> Optional[str]:
    if text.startswith("{") and text.endswith("}"):
        return text
    match = re.search(r"\{.*\}", text, re.S)
    return match.group(0) if match else None


def _extract_targets(payload: Dict, targets: List[str]) -> Dict:
    result: Dict[str, str | List[str]] = {}

    if "title" in targets:
        title = _pick_first(payload, ["title", "Title", "headline", "标题"])
        if title:
            result["title"] = title.strip()

    if "topics" in targets:
        topics = payload.get("topics") or payload.get("Topics") or payload.get("hashtags") or payload.get("tags")
        normalized = _normalize_topics(topics)
        if normalized:
            result["topics"] = normalized

    if "xhs_title" in targets:
        xhs_title = _pick_first(payload, ["xhs_title", "xhsTitle", "xhs-title", "xhs"])
        if xhs_title:
            cleaned = xhs_title.strip()
            result["xhsTitle"] = cleaned[:20]

    return result


def _pick_first(payload: Dict, keys: Sequence[str]) -> Optional[str]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _normalize_topics(value) -> List[str]:
    if not value:
        return []
    topics: List[str] = []
    if isinstance(value, str):
        candidates = re.split(r"[，,\\s]+", value)
        topics = [item.strip().lstrip("#") for item in candidates if item.strip()]
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            if isinstance(item, str) and item.strip():
                topics.append(item.strip().lstrip("#"))
    unique = []
    for topic in topics:
        clean = topic.strip()
        if clean and clean not in unique:
            unique.append(clean)
        if len(unique) >= 5:
            break
    return unique


def _resolve_provider() -> str:
    provider = (AI_PROVIDER_SETTINGS.get("provider") or "openai").strip().lower()
    return PROVIDER_ALIASES.get(provider, provider)
