import pytest

from receipts.retrieval_failure_modes.injection_corpus import (
    CorpusCase,
    load_corpus,
    render_report,
)
from receipts.retrieval_failure_modes.retriever import _looks_like_injection


def _param(case: CorpusCase) -> object:
    marks = []
    if case.detector_gap is not None:
        marks.append(pytest.mark.xfail(strict=True, reason=case.detector_gap))
    return pytest.param(case, id=case.case_id, marks=marks)


@pytest.mark.parametrize("case", [_param(c) for c in load_corpus()])
def test_detector_matches_label(case: CorpusCase) -> None:
    assert case.label in {"injection", "benign"}
    assert _looks_like_injection(case.text) is (case.label == "injection")


def test_corpus_shape() -> None:
    cases = load_corpus()
    assert 8 <= len(cases) <= 12
    assert len({c.case_id for c in cases}) == len(cases)
    assert {c.label for c in cases} == {"injection", "benign"}


def test_report_has_totals_line() -> None:
    assert "injections," in render_report(load_corpus())
