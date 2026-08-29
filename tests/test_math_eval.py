import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from utils.math_eval import safe_eval


def test_basic_addition():

    assert safe_eval("2 + 3") == 5


def test_basic_subtraction():

    assert safe_eval("10 - 4") == 6


def test_basic_multiplication():

    assert safe_eval("3 * 7") == 21


def test_basic_division():

    assert safe_eval("10 / 2") == 5.0


def test_floor_division():

    assert safe_eval("7 // 2") == 3


def test_modulo():

    assert safe_eval("10 % 3") == 1


def test_power():

    assert safe_eval("2 ** 10") == 1024


def test_negative_number():

    assert safe_eval("-5") == -5


def test_complex_expression():

    assert safe_eval("(2 + 3) * 4") == 20


def test_nested_expression():

    assert safe_eval("((1 + 2) * (3 + 4))") == 21


def test_decimal_numbers():

    assert safe_eval("1.5 + 2.5") == 4.0


def test_integer_result_from_float():

    assert safe_eval("4.0 / 2.0") == 2


def test_division_by_zero():

    assert safe_eval("1 / 0") is None


def test_invalid_expression():

    assert safe_eval("abc") is None


def test_code_injection_blocked():

    assert safe_eval("__import__('os')") is None


def test_function_call_blocked():

    assert safe_eval("print(1)") is None


def test_empty_expression():

    assert safe_eval("") is None


def test_whitespace_only():

    assert safe_eval("   ") is None


def test_only_operators():

    assert safe_eval("+ +") is None


def test_division_by_zero_complex():

    assert safe_eval("10 / (5 - 5)") is None


def test_large_numbers():

    assert safe_eval("999999 * 999999") == (
        999999 * 999999
    )
