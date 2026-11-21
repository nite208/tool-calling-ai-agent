import logging
from typing import Any, Callable

import src.tools.calculator as calculator
import src.tools.weather as weather
import src.tools.wikipedia as wikipedia

logger = logging.getLogger(__name__)

TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "calculator": {
        "schema": calculator.SCHEMA,
        "handler": calculator.handle,
    },
    "get_weather": {
        "schema": weather.SCHEMA,
        "handler": weather.handle,
    },
    "wikipedia_search": {
        "schema": wikipedia.SCHEMA,
        "handler": wikipedia.handle,
    },
}


def get_tool_schemas() -> list[dict[str, Any]]:
    return [entry["schema"] for entry in TOOL_REGISTRY.values()]


def execute_tool(name: str, arguments: dict[str, Any]) -> str:
    logger.info("Executing tool name=%r arguments=%r", name, arguments)
    entry = TOOL_REGISTRY.get(name)
    if entry is None:
        logger.warning("Unknown tool requested: %r", name)
        return f"error: unknown tool '{name}'."
    handler: Callable[[dict[str, Any]], str] = entry["handler"]
    result = handler(arguments)
    logger.info("Tool %r result length=%d", name, len(result))
    return result
