"""
Real LLM backends for running experiments with actual language models.

Supported providers:
- OpenAI (GPT-4o, GPT-4o-mini, o1, etc.)
- Anthropic (Claude 3.5 Sonnet, Haiku, etc.)
- Ollama (Llama 3.1, Mistral, Qwen, etc. -- local, free)
- Any OpenAI-compatible API (vLLM, Together, Groq, etc.)

All backends implement the LLMBackend protocol:
    def generate(self, prompt: str, max_tokens: int = 512) -> str

Usage:
    from ai_universe25.agents.llm_backends import OpenAIBackend, OllamaBackend

    # OpenAI
    backend = OpenAIBackend(model="gpt-4o-mini", api_key="sk-...")

    # Ollama (local)
    backend = OllamaBackend(model="llama3.1:8b")

    # Any OpenAI-compatible endpoint
    backend = OpenAIBackend(
        model="meta-llama/Llama-3.1-8B-Instruct",
        api_key="...",
        base_url="https://api.together.xyz/v1",
    )

    # Use with agents
    agent = create_agent(AgentRole.HERALD, llm_backend=backend)
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


DEFAULT_SYSTEM_PROMPT = (
    "You are an agent in a collaborative wiki-writing system. "
    "Follow your role instructions precisely. Produce well-structured, "
    "citation-ready content. Be concise."
)


@dataclass
class ModelConfig:
    """Configuration for a model backend."""

    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_retries: int = 3
    retry_delay: float = 1.0
    system_prompt: str = DEFAULT_SYSTEM_PROMPT


class OpenAIBackend:
    """
    OpenAI-compatible LLM backend.

    Works with OpenAI, Azure OpenAI, Together, Groq, vLLM, LiteLLM,
    and any other provider exposing the /v1/chat/completions endpoint.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or "https://api.openai.com/v1"
        self.temperature = temperature
        self.max_retries = max_retries
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

        self._token_usage = {"prompt": 0, "completion": 0}
        self._call_count = 0

        try:
            import httpx
            self._client = httpx.Client(timeout=60.0)
        except ImportError:
            self._client = None
            logger.warning("httpx not available; install it for OpenAIBackend")

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        if self._client is None:
            raise RuntimeError("httpx is required for OpenAIBackend")

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

        for attempt in range(self.max_retries):
            try:
                resp = self._client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": self.temperature,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                usage = data.get("usage", {})
                self._token_usage["prompt"] += usage.get("prompt_tokens", 0)
                self._token_usage["completion"] += usage.get("completion_tokens", 0)
                self._call_count += 1

                return data["choices"][0]["message"]["content"]

            except Exception as e:
                logger.warning(f"OpenAI call failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

    @property
    def usage_summary(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "calls": self._call_count,
            "prompt_tokens": self._token_usage["prompt"],
            "completion_tokens": self._token_usage["completion"],
            "total_tokens": sum(self._token_usage.values()),
        }


class OllamaBackend:
    """
    Ollama backend for local LLM inference.

    Requires Ollama running locally (default: http://localhost:11434).
    Models: llama3.1:8b, mistral:7b, qwen2.5:7b, gemma2:9b, etc.
    """

    def __init__(
        self,
        model: str = "llama3.1:8b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ):
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self._call_count = 0

        try:
            import httpx
            self._client = httpx.Client(timeout=120.0)
        except ImportError:
            self._client = None

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        if self._client is None:
            raise RuntimeError("httpx is required for OllamaBackend")

        resp = self._client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": max_tokens,
                },
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self._call_count += 1
        return data["message"]["content"]

    @property
    def usage_summary(self) -> Dict[str, Any]:
        return {"model": self.model, "calls": self._call_count, "cost": 0.0}


class AnthropicBackend:
    """
    Anthropic Claude backend.

    Models: claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, etc.
    """

    def __init__(
        self,
        model: str = "claude-3-5-haiku-20241022",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.temperature = temperature
        self.max_retries = max_retries
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self._token_usage = {"input": 0, "output": 0}
        self._call_count = 0

        try:
            import httpx
            self._client = httpx.Client(timeout=60.0)
        except ImportError:
            self._client = None

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        if self._client is None:
            raise RuntimeError("httpx is required for AnthropicBackend")

        for attempt in range(self.max_retries):
            try:
                resp = self._client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": max_tokens,
                        "system": self.system_prompt,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.temperature,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                usage = data.get("usage", {})
                self._token_usage["input"] += usage.get("input_tokens", 0)
                self._token_usage["output"] += usage.get("output_tokens", 0)
                self._call_count += 1

                return data["content"][0]["text"]

            except Exception as e:
                logger.warning(f"Anthropic call failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

    @property
    def usage_summary(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "calls": self._call_count,
            "input_tokens": self._token_usage["input"],
            "output_tokens": self._token_usage["output"],
        }


# ---------------------------------------------------------------------------
# Model registry for experiment configs
# ---------------------------------------------------------------------------

RECOMMENDED_MODELS = {
    "local_free": {
        "llama3.1:8b": "Best overall local model. Good instruction-following, fast.",
        "mistral:7b": "Excellent structured output. Lower resource usage.",
        "qwen2.5:7b": "Strong reasoning. Good for verification roles.",
        "gemma2:9b": "Google's open model. Good for style/neutrality tasks.",
    },
    "api_cheap": {
        "gpt-4o-mini": "OpenAI's cheapest capable model. ~$0.15/1M input tokens.",
        "claude-3-5-haiku-20241022": "Anthropic's fast model. ~$0.25/1M input.",
        "gemini-1.5-flash": "Google's fast model. Free tier available.",
    },
    "api_frontier": {
        "gpt-4o": "OpenAI's flagship. ~$2.50/1M input. Named in paper's CQP.",
        "claude-3-5-sonnet-20241022": "Anthropic frontier. ~$3/1M input. Named in CQP.",
        "gemini-1.5-pro": "Google frontier. ~$1.25/1M input. Named in CQP.",
    },
}


def create_backend(
    provider: str,
    model: str,
    **kwargs,
):
    """
    Factory function to create an LLM backend.

    Args:
        provider: "openai", "anthropic", "ollama", or "simulated"
        model: Model identifier
        **kwargs: Additional config (api_key, base_url, temperature, etc.)

    Examples:
        create_backend("simulated", "deterministic", seed=42)
        create_backend("ollama", "llama3.1:8b")
        create_backend("openai", "gpt-4o-mini", api_key="sk-...")
        create_backend("openai", "meta-llama/Llama-3.1-8B-Instruct",
                        base_url="https://api.together.xyz/v1",
                        api_key="...")
    """
    from ai_universe25.agents.base import SimulatedLLMBackend

    if provider == "simulated":
        return SimulatedLLMBackend(seed=kwargs.get("seed", 42))
    elif provider == "openai":
        return OpenAIBackend(model=model, **kwargs)
    elif provider == "anthropic":
        return AnthropicBackend(model=model, **kwargs)
    elif provider == "ollama":
        return OllamaBackend(model=model, **kwargs)
    else:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Use 'simulated', 'openai', 'anthropic', or 'ollama'."
        )
