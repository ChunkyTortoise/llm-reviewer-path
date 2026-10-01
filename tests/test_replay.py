import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_replay() -> str:
    result = subprocess.run(
        [sys.executable, "-m", "receipts"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def test_replay_module_shows_scores_approval_flow_and_updated_contact():
    lines = _run_replay().splitlines()
    assert "GOOD: score=1.00, n=5, gate=True" in lines
    assert "MUTATION: score=0.80, n=5, gate=False" in lines
    assert "without token: denied_without_approval" in lines
    assert "model text: ApprovalError untrusted approval" in lines
    assert "approved: execute_once" in lines
    assert "retry: duplicate_retry_suppressed" in lines
    assert lines[-1] == "read after: {'ok': True, 'name': 'Ada', 'city': 'LA'}"
    assert not any("tok_" in line for line in lines)


def test_replay_output_matches_documented_output():
    doc = (ROOT / "docs" / "offline-receipt.md").read_text()
    block = re.search(r"Actual output.*?```text\n(.*?)```", doc, re.S)
    assert block is not None
    assert _run_replay() == block.group(1)
