import os
import requests
import json
from dotenv import load_dotenv


load_dotenv()

API_URL     = os.getenv("LLM_GATEWAY_URL", "https://imllm.intermesh.net/v1/chat/completions")
LLM_API_KEY = os.getenv("LLM_GATEWAY_API_KEY")

MASTER_MODEL = "google/gemini-2.5-pro"
SKILL_MODEL  = "google/gemini-2.5-flash"

def call_llm(system_prompt: str, user_prompt: str, model: str = SKILL_MODEL) -> dict:
    """
    Returns dict with keys:
      - 'thinking': raw internal reasoning (str or None)
      - 'response': final response text (str)
      - 'usage': token counts
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt}
    ]

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 20000
    }

    # Enable thinking only for master model (gemini-2.5-pro)
    if model == MASTER_MODEL:
        payload["thinking"] = {
            "type": "enabled",
            "budget_tokens": 15000
        }

    url = API_URL
    if "/chat/completions" not in url:
        url = f"{url.rstrip('/')}/chat/completions"

    resp = requests.post(url, headers=headers, json=payload, timeout=180)
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"API Error Response: {resp.text}")
        raise e
    data = resp.json()

    thinking_text = None
    response_text = ""

    # Try to extract thinking from response
    choice = data["choices"][0]
    message = choice["message"]

    # Method 1: thinking as separate field on message (some gateways)
    if "thinking" in message:
        thinking_text = message["thinking"]

    # Method 2: content is a list of blocks (native Anthropic-style or some gateways)
    if isinstance(message.get("content"), list):
        for block in message["content"]:
            if isinstance(block, dict):
                if block.get("type") == "thinking":
                    thinking_text = block.get("thinking") or block.get("text", "")
                elif block.get("type") == "text":
                    response_text += block.get("text", "")
    else:
        # Method 3: content is plain string (standard OpenAI format)
        response_text = message.get("content", "")

    # Method 4: reasoning_content field (some gateways use this)
    if not thinking_text and "reasoning_content" in message:
        thinking_text = message["reasoning_content"]

    usage = data.get("usage", {})

    return {
        "thinking": thinking_text,
        "response": response_text,
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0)
        }
    }
