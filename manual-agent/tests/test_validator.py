import pytest

from agent.errors import DecisionError
from agent.validator import validate_decision


def test_valid_lookup():
    validate_decision({"action": "lookup_http_method", "arguments": {"name": "get"}})


def test_valid_check_property():
    validate_decision(
        {"action": "check_property", "arguments": {"method": "put", "property": "idempotent"}}
    )


@pytest.mark.parametrize(
    "decision",
    [
        {"action": "search_google", "arguments": {}},  # дії немає у білому списку
        {"action": "lookup_http_method", "arguments": {}},  # бракує аргументу
        {"action": "lookup_http_method", "arguments": {"name": 42}},  # хибний тип
        {"action": "finish"},  # немає arguments
        {"action": "check_property", "arguments": {"method": "put"}},  # бракує property
        {"action": "check_property", "arguments": {"method": "put", "property": "fast"}},
        {"action": "finish", "arguments": {"answer": "   "}},  # порожній рядок
    ],
)
def test_invalid_decisions(decision):
    with pytest.raises(DecisionError):
        validate_decision(decision)
