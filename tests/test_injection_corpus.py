from pathlib import Path

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
    assert _looks_like_injection(case.text) is (case.label == "injection")


def test_corpus_shape() -> None:
    cases = load_corpus()
    assert 8 <= len(cases) <= 12
    assert len({c.case_id for c in cases}) == len(cases)
    assert {c.label for c in cases} == {"injection", "benign"}


def test_load_corpus_rejects_unknown_label(tmp_path: Path) -> None:
    bad = tmp_path / "corpus.json"
    bad.write_text(
        '[{"id": "x", "technique": "t", "label": "injecton", "text": "", "detector_gap": null}]',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown label"):
        load_corpus(bad)


def test_readme_table_matches_report() -> None:
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    assert render_report(load_corpus()) in readme
