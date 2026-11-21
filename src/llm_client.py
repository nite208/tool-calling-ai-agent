import logging
import os
from typing import Any

from groq import Groq, APIError, APITimeoutError, RateLimitError

import src.config as config
from src.exceptions import LLMError

logger = logging.getLogger(__name__)


def _get_client() -> Groq:
    api_key = config.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
    return Groq(api_key=api_key)


def chat_completion(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> Any:
    kwargs: dict[str, Any] = {
        "model": config.GROQ_MODEL,
        "messages": messages,
        "max_tokens": config.MAX_TOKENS,
        "temperature": config.TEMPERATURE,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    logger.info("Calling Groq model=%s messages=%d", config.GROQ_MODEL, len(messages))
    try:
        client = _get_client()
        response = client.chat.completions.create(**kwargs)
        logger.info("Groq response finish_reason=%s", response.choices[0].finish_reason)
        return response
    except RateLimitError as exc:
        logger.error("Groq rate limit: %s", exc, exc_info=True)
        raise LLMError("Groq rate limit reached. Please wait and try again.") from exc
    except APITimeoutError as exc:
        logger.error("Groq timeout: %s", exc, exc_info=True)
        raise LLMError("Groq request timed out.") from exc
    except APIError as exc:
        logger.error("Groq API error: %s", exc, exc_info=True)
        raise LLMError(f"Groq API error: {exc.message}") from exc
