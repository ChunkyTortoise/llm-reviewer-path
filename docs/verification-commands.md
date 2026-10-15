# Full verification commands

Run from the repository root after the README setup. The README uses shorter pytest selectors so commands fit on a phone. These file-path commands preserve the exact module mapping.

Evaluation and coverage (19 tests):

```bash
uv run pytest tests/test_eval_gate.py tests/test_missing_fixture_fails_closed.py
```

Approval (10 tests):

```bash
uv run pytest tests/test_hard_action.py
```

Retrieval (9 tests):

```bash
uv run pytest tests/test_retrieval_failure_modes.py
```

Receipt and README checks (4 tests):

```bash
uv run pytest tests/test_replay.py
uv run python -m receipts
```

Strict typing and lint (development tools are declared and locked):

```bash
uv run mypy --strict receipts tests
uv run ruff check receipts tests
```

The full suite currently collects 42 tests. Mermaid checks cover headers and balanced subgraphs, not rendering or full syntax. The 2026-10-05 terminal GIF remains a historical 36-test recording; replay stdout is unchanged.
