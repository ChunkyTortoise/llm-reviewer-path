from dataclasses import dataclass

from receipts.retrieval_failure_modes.cases import CASES
from receipts.retrieval_failure_modes.retriever import classify

THRESHOLD = 1.0
REQUIRED_CASE_IDS = frozenset(CASES)


class CoverageError(ValueError):
    """The candidate did not supply the complete fixed fixture set."""


@dataclass(frozen=True)
class Candidate:
    labels: dict[str, str | None]


@dataclass(frozen=True)
class Report:
    score: float
    n: int
    case_ids: frozenset[str] = frozenset()


def evaluate(candidate: Candidate) -> Report:
    supplied = frozenset(candidate.labels)
    unknown = supplied - REQUIRED_CASE_IDS
    if unknown:
        raise KeyError(", ".join(sorted(unknown)))
    missing = REQUIRED_CASE_IDS - supplied
    if missing:
        raise CoverageError(f"Missing case IDs: {', '.join(sorted(missing))}")

    hits = 0
    n = 0
    for case_id, expected_failure in candidate.labels.items():
        n += 1
        got = classify(case_id)
        if expected_failure is None:
            if got.ok:
                hits += 1
        elif (not got.ok) and got.failure == expected_failure:
            hits += 1
    return Report(score=(hits / n if n else 0.0), n=n, case_ids=supplied)


def gate(report: Report) -> bool:
    return (
        report.case_ids == REQUIRED_CASE_IDS
        and report.n == len(REQUIRED_CASE_IDS)
        and THRESHOLD <= report.score <= 1.0
    )


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
