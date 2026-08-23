from receipts.eval_gate.gate import GOOD, MUTATION, evaluate, gate


def test_good_candidate_clears_threshold():
    report = evaluate(GOOD)
    assert report.score >= 1.0
    assert gate(report) is True


def test_mutation_is_rejected():
    report = evaluate(MUTATION)
    assert gate(report) is False


def test_four_failure_ids_are_the_baseline():
    assert {"empty", "conflict", "injection", "malformed"} <= set(GOOD.labels)
