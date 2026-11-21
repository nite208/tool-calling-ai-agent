from unittest.mock import patch
from src.tools.registry import TOOL_REGISTRY, get_tool_schemas, execute_tool


def test_registry_exposes_exactly_three_tools():
    assert set(TOOL_REGISTRY.keys()) == {
        "calculator",
        "get_weather",
        "wikipedia_search",
    }
    assert len(TOOL_REGISTRY) == 3


def test_every_entry_has_schema_and_handler():
    for name, entry in TOOL_REGISTRY.items():
        assert "schema" in entry, f"{name} missing schema"
        assert "handler" in entry, f"{name} missing handler"
        assert callable(entry["handler"]), f"{name} handler not callable"


def test_schema_structure():
    for name, entry in TOOL_REGISTRY.items():
        schema = entry["schema"]
        assert schema["type"] == "function", f"{name} schema type must be 'function'"
        func = schema["function"]
        assert "name" in func, f"{name} schema missing function.name"
        assert "description" in func, f"{name} schema missing function.description"
        assert "parameters" in func, f"{name} schema missing function.parameters"
        params = func["parameters"]
        assert params["type"] == "object", f"{name} parameters type must be 'object'"
        assert "properties" in params, f"{name} parameters missing properties"
        assert "required" in params, f"{name} parameters missing required"


def test_get_tool_schemas_returns_list():
    schemas = get_tool_schemas()
    assert isinstance(schemas, list)
    assert len(schemas) == len(TOOL_REGISTRY)


def test_execute_tool_calculator():
    result = execute_tool("calculator", {"expression": "2 + 2"})
    assert result == "4"


def test_execute_tool_calculator_error():
    result = execute_tool("calculator", {"expression": "1 / 0"})
    assert result.startswith("error:")


def test_execute_tool_unknown_tool():
    result = execute_tool("nonexistent_tool", {})
    assert "unknown tool" in result


def test_execute_tool_missing_expression():
    result = execute_tool("calculator", {})
    assert result.startswith("error:")


def test_schema_names_match_registry_keys():
    for name, entry in TOOL_REGISTRY.items():
        schema_name = entry["schema"]["function"]["name"]
        assert schema_name == name, (
            f"Registry key {name!r} does not match schema name {schema_name!r}"
        )


def test_register_new_tool_makes_it_appear():
    fake_schema = {
        "type": "function",
        "function": {
            "name": "fake_tool",
            "description": "A fake tool for testing extension.",
            "parameters": {
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
            },
        },
    }

    def fake_handler(arguments):
        return f"fake: {arguments.get('value', '')}"

    test_registry = dict(TOOL_REGISTRY)
    test_registry["fake_tool"] = {
        "schema": fake_schema,
        "handler": fake_handler,
    }

    with patch.dict("src.tools.registry.TOOL_REGISTRY", test_registry, clear=True):
        schemas = get_tool_schemas()
        assert any(s["function"]["name"] == "fake_tool" for s in schemas)
        output = execute_tool("fake_tool", {"value": "hello"})
        assert output == "fake: hello"
