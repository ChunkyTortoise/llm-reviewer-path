from dataclasses import dataclass

from receipts.retrieval_failure_modes.cases import CASES
from receipts.retrieval_failure_modes.retriever import classify

THRESHOLD = 1.0


@dataclass(frozen=True)
class Candidate:
    labels: dict[str, str | None]


@dataclass(frozen=True)
class Report:
    score: float
    n: int


def evaluate(candidate: Candidate) -> Report:
    hits = 0
    n = 0
    for case_id, expected_failure in candidate.labels.items():
        if case_id not in CASES:
            raise KeyError(case_id)
        n += 1
        got = classify(case_id)
        if expected_failure is None:
            if got.ok:
                hits += 1
        elif (not got.ok) and got.failure == expected_failure:
            hits += 1
    return Report(score=(hits / n if n else 0.0), n=n)


def gate(report: Report) -> bool:
    return report.score >= THRESHOLD


GOOD = Candidate(
    labels={
        "empty": "empty_retrieval",
        "conflict": "conflicting_evidence",
        "injection": "prompt_injection",
        "malformed": "malformed_structured_output",
        "clean": None,
    }
)

# Mutation: pretends injection is clean. Must fail the gate.
MUTATION = Candidate(
    labels={
        "empty": "empty_retrieval",
        "conflict": "conflicting_evidence",
        "injection": None,
        "malformed": "malformed_structured_output",
        "clean": None,
    }
)
