"""Local Ollama client and prompt helpers."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


class OllamaUnavailableError(RuntimeError):
    """Raised when Ollama cannot be reached or returns an invalid response."""


@dataclass(frozen=True)
class OllamaConfig:
    model: str = "llama3.1"
    base_url: str = "http://localhost:11434"
    timeout_seconds: int = 60

    def validated(self) -> "OllamaConfig":
        model = self.model.strip()
        base_url = self.base_url.strip().rstrip("/")
        if not model:
            raise ValueError("Choose an Ollama model before generating a draft.")
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("Ollama URL must start with http:// or https://.")
        return OllamaConfig(model=model, base_url=base_url, timeout_seconds=self.timeout_seconds)


class OllamaClient:
    def __init__(self, config: OllamaConfig):
        self.config = config.validated()

    def generate(self, prompt: str) -> str:
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        payload = json.dumps(
            {"model": self.config.model, "prompt": prompt, "stream": False}
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.config.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request, timeout=self.config.timeout_seconds
            ) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise OllamaUnavailableError(
                "Ollama is unavailable. Start Ollama locally and confirm the model is pulled."
            ) from exc
        except json.JSONDecodeError as exc:
            raise OllamaUnavailableError("Ollama returned an unreadable response.") from exc

        text = str(body.get("response", "")).strip()
        if not text:
            raise OllamaUnavailableError("Ollama returned an empty draft.")
        return text


def grounded_prompt(task: str, facts: dict[str, str]) -> str:
    facts_lines = "\n".join(f"- {key}: {value}" for key, value in facts.items())
    return (
        "You are BizPilot AI, a local-first assistant for small businesses.\n"
        "Use only the business details listed below. Do not invent prices, names, "
        "dates, addresses, client details, policies, or payment terms. If a needed "
        "detail is missing, write [missing: detail name].\n\n"
        f"Task: {task}\n\n"
        f"Provided business details:\n{facts_lines}\n\n"
        "Draft:"
    )
