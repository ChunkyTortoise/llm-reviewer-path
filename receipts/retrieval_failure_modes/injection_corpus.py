"""Labeled prompt-injection corpus and a report over the real detector.

Labels describe what the text IS (`injection` or `benign`), never what the
detector does. `detector_gap` records a known disagreement between label and
detector, and is used to mark the test as a strict xfail.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from receipts.retrieval_failure_modes.retriever import _looks_like_injection

LABELS = frozenset({"injection", "benign"})

CORPUS_PATH = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "injection_corpus.json"


@dataclass(frozen=True)
class CorpusCase:
    case_id: str
    technique: str
    label: str
    text: str
    detector_gap: str | None


def load_corpus(path: Path = CORPUS_PATH) -> list[CorpusCase]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    cases = [
        CorpusCase(r["id"], r["technique"], r["label"], r["text"], r["detector_gap"]) for r in rows
    ]
    for c in cases:
        if c.label not in LABELS:
            raise ValueError(f"{c.case_id}: unknown label {c.label!r}")
    return cases


def render_report(cases: list[CorpusCase]) -> str:
    lines = [
        "| Case | Technique | Label | Detector |",
        "|---|---|---|---|",
    ]
    caught = missed = false_pos = injections = 0
    for c in cases:
        flagged = _looks_like_injection(c.text)
        if c.label == "injection":
            injections += 1
            result = "caught" if flagged else "missed"
            caught += flagged
            missed += not flagged
        else:
            result = "false positive" if flagged else "correct (not flagged)"
            false_pos += flagged
        lines.append(f"| `{c.case_id}` | {c.technique} | {c.label} | {result} |")
    lines.append("")
    fp_word = "false positive" if false_pos == 1 else "false positives"
    lines.append(f"Caught {caught} of {injections} injections, {false_pos} {fp_word}.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render_report(load_corpus()))
