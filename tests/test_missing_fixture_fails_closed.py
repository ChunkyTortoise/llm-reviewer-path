import pytest

from receipts.eval_gate.gate import Candidate, evaluate


def test_unknown_case_errors_not_skip():
    cand = Candidate(labels={"nope": "empty_retrieval"})
    with pytest.raises(KeyError):
        evaluate(cand)
