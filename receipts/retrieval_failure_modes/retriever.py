import json
from dataclasses import dataclass

from receipts.retrieval_failure_modes.cases import CASES


@dataclass(frozen=True)
class ClassifyResult:
    ok: bool
    failure: str | None


def _looks_like_injection(text: str) -> bool:
    lowered = text.lower()
    return "ignore prior instructions" in lowered or "ignore previous" in lowered


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Nonstandard JSON constant: {value}")


def _is_valid_json_object(raw: str) -> bool:
    try:
        parsed = json.loads(raw, parse_constant=_reject_json_constant)
    except ValueError:
        return False
    return isinstance(parsed, dict)


def classify(case_id: str) -> ClassifyResult:
    case = CASES[case_id]
    if case.retrieved.strip() == "":
        return ClassifyResult(False, "empty_retrieval")
    if "Total is $10" in case.retrieved and "Total is $99" in case.retrieved:
        return ClassifyResult(False, "conflicting_evidence")
    if _looks_like_injection(case.retrieved):
        return ClassifyResult(False, "prompt_injection")
    if not _is_valid_json_object(case.expected_json):
        return ClassifyResult(False, "malformed_structured_output")
    return ClassifyResult(True, None)
