from __future__ import annotations

from typing import Any, Dict, List, Protocol, Tuple

import httpx

from .config import settings


ChatMessage = Dict[str, str]


class LLMClient(Protocol):
    provider: str
    mock: bool

    async def generate(self, messages: List[ChatMessage]) -> Tuple[str, Dict[str, Any]]:
        ...


class MockLLMClient:
    provider = "mock"
    mock = True

    async def generate(self, messages: List[ChatMessage]) -> Tuple[str, Dict[str, Any]]:
        last_user = next(
            (msg["content"] for msg in reversed(messages) if msg.get("role") == "user"),
            "",
        )
        synthetic = (
            "Mock response generated without contacting an external LLM. "
            f"Echoing your request: {last_user}"
        )
        return synthetic, {"mock_reason": "MOCK_MODE enabled or API key missing"}


class OpenAIChatClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.provider = "openai"
        self.mock = False

    async def generate(self, messages: List[ChatMessage]) -> Tuple[str, Dict[str, Any]]:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return choice, {"model": self.model, "usage": usage}


class GeminiChatClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.provider = "gemini"
        self.mock = False

    async def generate(self, messages: List[ChatMessage]) -> Tuple[str, Dict[str, Any]]:
        contents: List[Dict[str, Any]] = []
        system_instructions: List[str] = []

        for message in messages:
            role = message.get("role", "user")
            text = message.get("content", "")

            if role == "system":
                system_instructions.append(text)
                continue

            if role == "assistant":
                role = "model"
            else:
                role = "user"

            contents.append({"role": role, "parts": [{"text": text}]})

        payload: Dict[str, Any] = {"contents": contents}
        if system_instructions:
            payload["system_instruction"] = {
                "parts": [{"text": "\n\n".join(system_instructions)}]
            }

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("No candidates returned from Gemini.")

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts)
        usage = data.get("usageMetadata", {})
        return text, {"model": self.model, "usage": usage}


def build_llm_client() -> LLMClient:
    if settings.use_mock:
        return MockLLMClient()
    if settings.llm_provider.lower() == "openai" and settings.openai_api_key:
        return OpenAIChatClient(settings.openai_api_key, settings.openai_model)
    if settings.llm_provider.lower() == "gemini" and settings.gemini_api_key:
        return GeminiChatClient(settings.gemini_api_key, settings.gemini_model)
    # Default safely to mock mode if provider unsupported or credentials missing.
    return MockLLMClient()
