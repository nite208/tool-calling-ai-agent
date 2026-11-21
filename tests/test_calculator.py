import pytest
from src.tools.calculator import evaluate, handle
from src.exceptions import CalculatorError


def test_addition():
    assert evaluate("2 + 3") == "5"


def test_subtraction():
    assert evaluate("10 - 4") == "6"


def test_multiplication():
    assert evaluate("6 * 7") == "42"


def test_integer_division():
    assert evaluate("10 / 2") == "5"


def test_float_division():
    result = evaluate("1 / 3")
    assert float(result) == pytest.approx(1 / 3)


def test_floor_division():
    assert evaluate("7 // 2") == "3"


def test_modulo():
    assert evaluate("10 % 3") == "1"


def test_exponentiation():
    assert evaluate("2 ** 8") == "256"


def test_parentheses():
    assert evaluate("(2 + 3) * 4") == "20"


def test_unary_negation():
    assert evaluate("-5 + 10") == "5"


def test_nested_expression():
    assert evaluate("(1 + 2) * (3 + 4)") == "21"


def test_empty_expression_raises():
    with pytest.raises(CalculatorError, match="Empty"):
        evaluate("")


def test_whitespace_only_raises():
    with pytest.raises(CalculatorError, match="Empty"):
        evaluate("   ")


def test_division_by_zero_raises():
    with pytest.raises(CalculatorError, match="Division by zero"):
        evaluate("5 / 0")


def test_floor_division_by_zero_raises():
    with pytest.raises(CalculatorError, match="Division by zero"):
        evaluate("5 // 0")


def test_modulo_by_zero_raises():
    with pytest.raises(CalculatorError, match="Modulo by zero"):
        evaluate("5 % 0")


def test_invalid_syntax_raises():
    with pytest.raises(CalculatorError, match="Syntax error"):
        evaluate("2 +* 3")


def test_string_literal_raises():
    with pytest.raises(CalculatorError):
        evaluate("'hello'")


def test_function_call_raises():
    with pytest.raises(CalculatorError):
        evaluate("abs(-1)")


def test_name_reference_raises():
    with pytest.raises(CalculatorError):
        evaluate("x + 1")


def test_large_numbers():
    assert evaluate("1000000 * 1000000") == "1000000000000"


def test_negative_result():
    assert evaluate("3 - 10") == "-7"


@pytest.mark.parametrize(
    "bad_expr",
    [
        "2 + 2; import os",
        "__import__('os').system('echo hacked')",
        "2 ** 99999999",
        "10 / 0",
        "",
        "abc",
        "1 + " * 125 + "1",
    ],
)
def test_calculator_structured_error_and_never_number(bad_expr):
    result = handle({"expression": bad_expr})
    assert result.startswith("error:")
    try:
        float(result)
        is_number = True
    except ValueError:
        is_number = False
    assert not is_number
