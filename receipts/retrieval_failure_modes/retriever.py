from dataclasses import dataclass

from receipts.retrieval_failure_modes.cases import CASES


@dataclass(frozen=True)
class ClassifyResult:
    ok: bool
    failure: str | None


def _looks_like_injection(text: str) -> bool:
    lowered = text.lower()
    return "ignore prior instructions" in lowered or "ignore previous" in lowered


def classify(case_id: str) -> ClassifyResult:
    case = CASES[case_id]
    if case.retrieved.strip() == "":
        return ClassifyResult(False, "empty_retrieval")
    if "Total is $10" in case.retrieved and "Total is $99" in case.retrieved:
        return ClassifyResult(False, "conflicting_evidence")
    if _looks_like_injection(case.retrieved):
        return ClassifyResult(False, "prompt_injection")
    if not (case.expected_json.startswith("{") and case.expected_json.endswith("}")):
        return ClassifyResult(False, "malformed_structured_output")
    return ClassifyResult(True, None)
