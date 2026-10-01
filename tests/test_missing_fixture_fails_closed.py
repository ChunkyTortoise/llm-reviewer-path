import pytest

from receipts.eval_gate.gate import (
    GOOD,
    REQUIRED_CASE_IDS,
    Candidate,
    CoverageError,
    Report,
    evaluate,
    gate,
)


def test_unknown_case_errors_not_skip():
    with pytest.raises(KeyError):
        evaluate(Candidate(labels={"nope": "empty_retrieval"}))


@pytest.mark.parametrize("omitted", sorted(REQUIRED_CASE_IDS))
def test_every_single_omission_fails_closed(omitted):
    labels = {key: value for key, value in GOOD.labels.items() if key != omitted}
    with pytest.raises(CoverageError, match="Missing case IDs"):
        evaluate(Candidate(labels=labels))


@pytest.mark.parametrize("labels", [{}, {"clean": None}, {"clean": None, "injection": "prompt_injection"}])
def test_empty_and_clean_subsets_fail_closed(labels):
    with pytest.raises(CoverageError):
        evaluate(Candidate(labels=labels))


def test_unknown_case_with_complete_known_set_fails_closed():
    with pytest.raises(KeyError):
        evaluate(Candidate(labels={**GOOD.labels, "unknown": None}))


@pytest.mark.parametrize(
    "report",
    [
        Report(1.0, 1, frozenset({"clean"})),
        Report(1.0, 5),
        Report(1.0, 4, REQUIRED_CASE_IDS),
        Report(1.0, 5, frozenset({"clean", "empty", "conflict", "malformed", "unknown"})),
        Report(1.1, 5, REQUIRED_CASE_IDS),
    ],
)
def test_external_partial_or_invalid_reports_cannot_bypass_gate(report):
    assert gate(report) is False


def test_complete_external_report_can_be_scored():
    assert gate(Report(1.0, 5, REQUIRED_CASE_IDS)) is True
