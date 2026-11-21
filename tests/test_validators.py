from unittest.mock import MagicMock, patch

from src.agent import _contains_placeholder, _parse_tool_arguments, run_agent_blocking
from src.tools.registry import execute_tool


def _make_choice(content=None, tool_calls=None):
    choice = MagicMock()
    choice.finish_reason = "stop"
    choice.message.content = content
    choice.message.tool_calls = tool_calls or []
    return choice


def _make_response(content=None, tool_calls=None):
    resp = MagicMock()
    resp.choices = [_make_choice(content=content, tool_calls=tool_calls)]
    return resp


def test_placeholder_detection():
    assert _contains_placeholder("Here is [insert weather here]")
    assert _contains_placeholder("Please provide [your name]")
    assert _contains_placeholder("Value: [add value]")
    assert not _contains_placeholder("The weather in London is 15C.")
    assert not _contains_placeholder("Array index [0] is valid.")


def test_response_validator_retries_and_recovers():
    first_resp = _make_response(content="Here is [insert info]")
    retry_resp = _make_response(content="Here is the real info.")

    with patch("src.agent.chat_completion", side_effect=[first_resp, retry_resp]) as mock_chat:
        text, tools = run_agent_blocking([], "tell me something")
        assert text == "Here is the real info."
        assert mock_chat.call_count == 2


def test_response_validator_fails_after_one_retry():
    first_resp = _make_response(content="Here is [insert info]")
    second_resp = _make_response(content="Still [your placeholder]")

    with patch("src.agent.chat_completion", side_effect=[first_resp, second_resp]) as mock_chat:
        text, tools = run_agent_blocking([], "tell me something")
        assert "unable to generate a complete answer without placeholders" in text
        assert mock_chat.call_count == 2


def test_tool_call_arguments_validator_empty_and_malformed():
    assert _parse_tool_arguments("", "call_1") == {}
    assert _parse_tool_arguments("   ", "call_2") == {}
    assert _parse_tool_arguments("not json", "call_3") == {}
    assert _parse_tool_arguments('{"bad_json: 1', "call_4") == {}
    assert _parse_tool_arguments('"string_not_dict"', "call_5") == {}
    assert _parse_tool_arguments("123", "call_6") == {}
    assert _parse_tool_arguments('{"expression": "2+2"}', "call_7") == {
        "expression": "2+2"
    }


def test_tool_execution_with_malformed_arguments_does_not_crash():
    result = execute_tool("calculator", {})
    assert result.startswith("error:")

    result = execute_tool("get_weather", {})
    assert result.startswith("error:")

    result = execute_tool("wikipedia_search", {})
    assert result.startswith("error:")
