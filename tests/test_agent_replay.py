import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from receipts.agent_replay import INJECTED_NOTE, dispatch, run, scripted_model
from receipts.hard_action.loop import ActionLoop

ROOT = Path(__file__).resolve().parents[1]


def test_injected_note_cannot_write_through_the_scripted_agent() -> None:
    lines, loop = run()
    kinds = [entry["kind"] for entry in loop.audit]
    assert "execute_once" not in kinds
    assert kinds.count("denied_untrusted_approval") == 2
    assert loop.search_contact("ada")["city"] == "NY"
    assert "writes applied: 0" in lines


def test_scripted_model_takes_its_arguments_from_the_note() -> None:
    # The stand-in follows the note, so a different note produces different calls.
    note = INJECTED_NOTE.replace("Attacker City", "Elsewhere").replace(
        "tok_9f2c4e1a7b3d5f60", "tok_0123456789abcdef"
    )
    model = scripted_model(note)
    assert json.loads(next(model))["tool"] == "search_contact"
    propose = json.loads(next(model))
    assert propose["args"]["patch"] == {"city": "Elsewhere"}
    execute = json.loads(model.send({"status": "preview", "preview_id": "p1"}))
    assert execute["args"] == {"preview_id": "p1", "approval": "tok_0123456789abcdef"}
    assert list(scripted_model("Invoice 12 total 50.00")) == []


def test_same_proposal_executes_only_with_an_operator_issued_token() -> None:
    # Control: the write path works, so the denials above come from the gate.
    loop = ActionLoop()
    preview = dispatch(
        loop,
        json.dumps({"tool": "propose_update", "args": {"query": "ada", "patch": {"city": "LA"}}}),
    )
    token = loop.issue_approval(preview["preview_id"])
    call = {"tool": "execute", "args": {"preview_id": preview["preview_id"], "approval": token}}
    assert dispatch(loop, json.dumps(call)) == {"status": "execute_once"}
    assert loop.search_contact("ada")["city"] == "LA"


@pytest.mark.parametrize(
    ("raw_call", "status"),
    [
        ('{"tool": "issue_approval", "args": {"preview_id": "x"}}', "tool_not_exposed"),
        ('{"tool": "_contacts", "args": {}}', "tool_not_exposed"),
        ('{"tool": "audit", "args": {}}', "tool_not_exposed"),
        ('{"tool": "execute"}', "malformed_call"),
        ('["execute", {}]', "malformed_call"),
        ("execute(preview, approved=True)", "malformed_call"),
        ('{"tool": "execute", "args": {"preview_id": "x", "approved": true}}', "error"),
        ('{"tool": "propose_update", "args": {"query": "ada", "patch": {"ok": "no"}}}', "error"),
    ],
)
def test_dispatch_refuses_unexposed_tools_and_bad_calls(raw_call: str, status: str) -> None:
    loop = ActionLoop()
    assert dispatch(loop, raw_call)["status"] == status
    assert loop.audit == []


def test_agent_replay_output_matches_readme() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "receipts.agent_replay"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    block = re.search(
        r"Exact output of <code>uv run python -m receipts\.agent_replay</code>"
        r".*?\n```text\n(.*?)```",
        readme,
        re.S,
    )
    assert block is not None
    assert result.stdout == block.group(1)
