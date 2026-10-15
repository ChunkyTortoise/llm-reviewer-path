from receipts.eval_gate.gate import GOOD, MUTATION, evaluate, gate


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
