import pytest

from receipts.eval_gate.gate import GOOD, MUTATION, evaluate, gate
from receipts.retrieval_failure_modes import retriever


def test_good_candidate_clears_threshold() -> None:
    report = evaluate(GOOD)
    assert report.n == 5
    assert report.score == 1.0
    assert gate(report) is True


def test_mutation_is_rejected() -> None:
    report = evaluate(MUTATION)
    assert report.n == 5
    assert report.score == 0.8
    assert gate(report) is False


def test_four_failure_ids_are_the_baseline() -> None:
    assert {"empty", "conflict", "injection", "malformed"} <= set(GOOD.labels)


def test_gate_fails_when_the_classifier_stops_detecting_injection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Break the classifier, not the labels: with the injection check disabled the
    # correct label set no longer scores at the floor, so the gate must close.
    monkeypatch.setattr(retriever, "_looks_like_injection", lambda text: False)
    report = evaluate(GOOD)
    assert report.score == 0.8
    assert gate(report) is False
