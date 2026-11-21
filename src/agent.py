import json
import logging
import re
from typing import Any, Generator

from src.config import MAX_AGENT_STEPS
from src.exceptions import LLMError
from src.llm_client import chat_completion
from src.tools import execute_tool, get_tool_schemas

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful assistant. "
    "Answer greetings, conversational messages, and general knowledge questions directly without tools. "
    "Use the calculator tool for any arithmetic or math calculation. "
    "Use the get_weather tool for current weather inquiries about any location. "
    "Use the wikipedia_search tool to look up factual information, history, people, or entities. "
    "When multiple questions are asked in one prompt, you may call multiple tools in parallel or sequence. "
    "When a tool returns an error message starting with 'error:', explain the problem clearly to the user. "
    "Never generate placeholder text like '[insert ...]' or '[your ...]'. "
    "Always provide complete, factual answers."
)

_PLACEHOLDER_PATTERN = re.compile(
    r"\[(?:insert|your|add|put|enter|provide|fill)\b", re.IGNORECASE
)


def _contains_placeholder(text: str) -> bool:
    return bool(_PLACEHOLDER_PATTERN.search(text))


def _parse_tool_arguments(raw_arguments: str, tool_call_id: str) -> dict[str, Any]:
    if not raw_arguments or not raw_arguments.strip():
        logger.warning("Empty tool arguments for call id=%s", tool_call_id)
        return {}
    try:
        result = json.loads(raw_arguments)
        if not isinstance(result, dict):
            logger.warning("Tool arguments not a dict for call id=%s", tool_call_id)
            return {}
        return result
    except json.JSONDecodeError as exc:
        logger.error("Malformed tool arguments for id=%s: %s", tool_call_id, exc, exc_info=True)
        return {}


def _build_assistant_message(message: Any, tool_calls: list[Any]) -> dict[str, Any]:
    msg: dict[str, Any] = {"role": "assistant", "content": message.content}
    if tool_calls:
        msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in tool_calls
        ]
    return msg


def _execute_tool_calls(
    tool_calls: list[Any],
    messages: list[dict[str, Any]],
) -> list[str]:
    called_tools: list[str] = []
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        arguments = _parse_tool_arguments(tool_call.function.arguments, tool_call.id)
        result = execute_tool(function_name, arguments)
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
        )
        called_tools.append(function_name)
    return called_tools


def _validate_and_retry_text(
    text: str,
    messages: list[dict[str, Any]],
    tool_schemas: list[dict[str, Any]],
) -> str:
    if not _contains_placeholder(text):
        return text
    logger.warning("Placeholder detected in model response, retrying once.")
    messages.append({"role": "assistant", "content": text})
    messages.append(
        {
            "role": "user",
            "content": (
                "Your previous response contained a placeholder like '[insert ...]'. "
                "Please give a complete answer without any placeholders."
            ),
        }
    )
    try:
        retry_response = chat_completion(messages, tools=tool_schemas)
        text = retry_response.choices[0].message.content or ""
    except LLMError:
        return "I was unable to generate a complete answer. Please try again."
    if _contains_placeholder(text):
        return "I was unable to generate a complete answer without placeholders."
    return text


def _agent_loop(
    history: list[dict[str, Any]],
) -> Generator[tuple[str, list[str]], None, None]:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        *history,
    ]
    tool_schemas = get_tool_schemas()
    all_tools_called: list[str] = []

    for step in range(MAX_AGENT_STEPS):
        logger.info("Agent step %d/%d", step + 1, MAX_AGENT_STEPS)

        try:
            response = chat_completion(messages, tools=tool_schemas)
        except LLMError as exc:
            yield (f"Sorry, I encountered an error: {exc}", all_tools_called)
            return

        choice = response.choices[0]
        message = choice.message
        tool_calls = message.tool_calls or []

        if not tool_calls:
            text = _validate_and_retry_text(
                message.content or "", messages, tool_schemas
            )
            yield (text, all_tools_called)
            return

        messages.append(_build_assistant_message(message, tool_calls))
        called = _execute_tool_calls(tool_calls, messages)
        all_tools_called.extend(called)

    logger.warning("Agent reached max steps (%d)", MAX_AGENT_STEPS)
    yield ("I was unable to complete the task within the allowed number of steps.", all_tools_called)


def run_agent(
    history: list[dict[str, Any]],
) -> Generator[str, None, None]:
    for text, _ in _agent_loop(history):
        yield text


def run_agent_blocking(
    history: list[dict[str, Any]],
    user_message: str,
) -> tuple[str, list[str]]:
    full_history = list(history) + [{"role": "user", "content": user_message}]
    for text, tools_called in _agent_loop(full_history):
        return text, tools_called
    return "", []
