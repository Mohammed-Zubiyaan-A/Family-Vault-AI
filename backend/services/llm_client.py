"""
Wraps Ollama for both local and cloud inference behind one interface, so
callers never know or care which mode is active — see ARCHITECTURE.md
'Model configuration'.

IMPORTANT: this is the only place in the codebase that should read
OLLAMA_MODE / OLLAMA_MODEL_LOCAL / OLLAMA_MODEL_CLOUD. Everything else
calls generate()/chat() and gets the active mode via active_mode().
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from ollama import Client

from core.config import get_settings

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """
    Raised for any failure talking to Ollama (local or cloud) — timeout,
    connection refused, bad response, etc. Callers should catch this and
    turn it into a user-visible error (document status=error, or a 502
    from the QA endpoint) rather than letting a request hang or 500 with
    a raw traceback.
    """


@dataclass
class ModeInfo:
    mode: str  # "local" | "cloud"
    model: str


class LLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._mode = settings.OLLAMA_MODE
        timeout = settings.OLLAMA_TIMEOUT_SECONDS

        if self._mode == "cloud":
            self._client = Client(
                host="https://ollama.com",
                headers={"Authorization": f"Bearer {settings.OLLAMA_API_KEY}"},
                timeout=timeout,
            )
            self._model = settings.OLLAMA_MODEL_CLOUD
            logger.warning(
                "LLMClient initialized in CLOUD mode (model=%s, timeout=%ss). "
                "Document content will be sent to Ollama Cloud. "
                "This should only happen as an explicit hardware fallback.",
                self._model,
                timeout,
            )
        else:
            self._client = Client(host=settings.OLLAMA_HOST, timeout=timeout)
            self._model = settings.OLLAMA_MODEL_LOCAL
            logger.info(
                "LLMClient initialized in LOCAL mode (model=%s, host=%s, timeout=%ss).",
                self._model,
                settings.OLLAMA_HOST,
                timeout,
            )

    def active_mode(self) -> ModeInfo:
        """Powers GET /system/mode, which drives the frontend mode badge."""
        return ModeInfo(mode=self._mode, model=self._model)

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        """One-shot text generation. Used for explanation + extraction."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat(model=self._model, messages=messages)
        except Exception as exc:  # noqa: BLE001 - deliberately broad, see LLMError docstring
            raise LLMError(
                f"Ollama request failed in {self._mode} mode (model={self._model}): {exc}"
            ) from exc
        return response["message"]["content"]

    def generate_json(self, prompt: str, *, system: str | None = None) -> str:
        """
        Same as generate(), but asks Ollama's structured-output mode for
        raw JSON back. Caller is still responsible for validating/parsing
        against the Pydantic schemas in models/schemas.py.
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat(
                model=self._model,
                messages=messages,
                format="json",
            )
        except Exception as exc:  # noqa: BLE001 - deliberately broad, see LLMError docstring
            raise LLMError(
                f"Ollama request failed in {self._mode} mode (model={self._model}): {exc}"
            ) from exc
        return response["message"]["content"]


_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """
    Lazily-constructed singleton so the mode/model is picked up once at
    startup, not re-read on every call. Restart the service to pick up
    an OLLAMA_MODE change (this is deliberate — mode switches should be a
    conscious restart, not silently hot-swapped mid-session).
    """
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
