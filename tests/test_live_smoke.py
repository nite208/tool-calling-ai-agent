import os
import re
import pytest
from dotenv import load_dotenv

load_dotenv()

from src.agent import run_agent_blocking, _contains_placeholder

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE") != "1",
        reason="Live tests require RUN_LIVE=1",
    ),
]


def test_live_greeting_calls_no_tool():
    text, tools = run_agent_blocking([], "hi")
    assert tools == []
    assert len(text.strip()) > 0


def test_live_calculator_percentage():
    text, tools = run_agent_blocking([], "what is 15% of 2480")
    assert "calculator" in tools
    assert "372" in text


def test_live_weather_pune():
    text, tools = run_agent_blocking([], "weather in Pune")
    assert "get_weather" in tools
    assert len(text.strip()) > 0


def test_live_weather_unknown_city():
    text, tools = run_agent_blocking([], "weather in Xyzabcqq")
    assert "get_weather" in tools
    clean_text = text.replace(chr(0x2019), "'").replace(chr(0x2018), "'").lower()
    assert any(
        phrase in clean_text
        for phrase in [
            "not find",
            "not found",
            "could not find",
            "couldn't find",
            "unable to find",
            "unknown",
            "doesn't exist",
            "does not exist",
            "no weather",
            "no results",
            "location",
        ]
    )


def test_live_divide_by_zero():
    text, tools = run_agent_blocking([], "what is 10 divided by 0")
    lower_text = text.lower()
    assert any(
        phrase in lower_text
        for phrase in [
            "zero",
            "undefined",
            "cannot divide",
            "division by zero",
            "not possible",
            "error",
        ]
    )


def test_live_alan_turing_wikipedia():
    text, tools = run_agent_blocking([], "who was Alan Turing")
    assert "wikipedia_search" in tools
    assert "403" not in text
    assert "turing" in text.lower()


def test_live_mumbai_multi_tool():
    text, tools = run_agent_blocking(
        [], "what is the weather in Mumbai and who is the mayor of Mumbai"
    )
    assert "get_weather" in tools
    assert "wikipedia_search" in tools
    assert not _contains_placeholder(text)
    assert not re.search(r"\[(?:insert|your|add|placeholder)\]", text, re.IGNORECASE)


def test_live_calculator_injection_fails():
    text, tools = run_agent_blocking([], "2 + 2; import os")
    lower_text = text.lower()
    assert "imported" not in lower_text
    assert "hacked" not in lower_text
