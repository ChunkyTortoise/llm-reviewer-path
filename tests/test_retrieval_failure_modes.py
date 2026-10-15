import pytest

from receipts.retrieval_failure_modes.cases import CASES, Case
from receipts.retrieval_failure_modes.retriever import (
    _is_valid_json_object,
    classify,
)


def test_empty_retrieval() -> None:
    result = classify("empty")
    assert result.ok is False
    assert result.failure == "empty_retrieval"


def test_conflicting_evidence() -> None:
    result = classify("conflict")
    assert result.ok is False
    assert result.failure == "conflicting_evidence"


def test_injection_in_retrieved_text() -> None:
    result = classify("injection")
    assert result.ok is False
    assert result.failure == "prompt_injection"


def test_malformed_structured_output() -> None:
    result = classify("malformed")
    assert result.ok is False
    assert result.failure == "malformed_structured_output"
    assert _is_valid_json_object("{bad:json}") is False
    assert _is_valid_json_object("[1, 2, 3]") is False


def test_clean_pass() -> None:
    result = classify("clean")
    assert result.ok is True
    assert result.failure is None


@pytest.mark.parametrize(
    ("raw", "valid"),
    [
        ('{"total":NaN}', False),
        ('{"total":Infinity}', False),
        ('{"total":-Infinity}', False),
        ('{"total":15,"note":"NaN is text"}', True),
    ],
)
def test_json_constants_through_classifier(
    monkeypatch: pytest.MonkeyPatch, raw: str, valid: bool
) -> None:
    monkeypatch.setitem(CASES, "probe", Case("probe", "Invoice total 15", raw))
    result = classify("probe")
    assert result.ok is valid
    assert result.failure == (None if valid else "malformed_structured_output")
