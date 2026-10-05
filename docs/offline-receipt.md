# Reproduce the local receipt

Replayed on 2026-10-01 in the working branch `codex/four-hero-reviewer-20261001`, based on PR6 head `bc48ffe`. This candidate retains the replay module and adds full fixture coverage. Synthetic in-memory contact, five local classification fixtures, no model calls or network. The README diagram is an editorial summary of this output.

After the README setup, run from the repository root:

```bash
uv run python -m receipts
```

The replay is `receipts/replay.py`. It covers the eval scores and the approval sequence (denied, execute once, duplicate retry suppressed, updated contact). It does not cover the changed-proposal rejection, which is an internal-state test in `tests/test_hard_action.py`.

Actual output (`tests/test_replay.py` asserts this block matches; tokens and random preview IDs are deliberately not printed):

```text
GOOD: score=1.00, n=5, gate=True
MUTATION: score=0.80, n=5, gate=False
read: {'ok': True, 'name': 'Ada', 'city': 'NY'}
propose: preview {'city': 'LA'}
without token: denied_without_approval
model text: ApprovalError untrusted approval
approved: execute_once
retry: duplicate_retry_suppressed
read after: {'ok': True, 'name': 'Ada', 'city': 'LA'}
```

The 2026-10-01 verification ran `python -m pytest` (36 passed) and `python -m receipts` from the isolated worktree using the primary checkout's existing virtual environment. The same module commands also passed through `uv run --no-sync --offline` with `UV_PROJECT_ENVIRONMENT` pointing to that environment. A direct `pytest` executable in this reused environment imports the older primary checkout; use `python -m pytest` for this worktree verification. No packages were installed. The documented setup and CI use `uv sync --group dev` followed by `uv run pytest`, a separate fresh-environment route that this local verification did not exercise.

## Limits observed by interaction

The approval example uses random tokens, not digital signatures. Its contact and execution history live in memory. Any caller in the same process can call `issue_approval`. Incoming and returned patch dictionaries are copied, and the approval token is bound to a snapshot of the target query and patch. Changing the stored proposal after approval raises `ApprovalError` before writing; `tests/test_hard_action.py` checks this by editing private state, and the replay does not. Tests also verify that a duplicate retry does not apply the patch again. This is a local example, not a distributed authorization boundary; durable storage, concurrent execution, token expiry and a separately authenticated approver are not implemented.

The classification cases are fixed local fixtures. The mutation changes the expected injection label; this is not a model-quality benchmark or a live RAG run.

## Visual asset provenance

`docs/assets/reviewer-receipt.svg` is a hand-authored editorial diagram summarizing the output above (two fixture runs and an in-memory approval sequence) plus one panel labeled `Internal-state test` for the changed-proposal rejection, which the replay does not run. It is not a terminal capture. `docs/assets/terminal-demo.gif` is a real terminal capture of `uv sync --group dev`, `uv run pytest` and `uv run python -m receipts` in a fresh checkout of this commit, recorded 2026-10-05 with `docs/demo.tape` (vhs 0.11.0); the tape re-renders the GIF and the commands print the same output as the block above. `docs/assets/social-preview.svg` is an editorial social card; `social-preview.png` is its unmodified 1280x640 Chrome rasterization, captured on 2026-09-26. No generated application output or client data is used.

The evaluation boundary rejects missing fixtures with `CoverageError` and unknown IDs with `KeyError` before scoring. The gate also checks the exact case IDs and count on externally constructed reports. The report describes fixed-fixture results; supplying a complete report does not prove an external evaluation was honest.
