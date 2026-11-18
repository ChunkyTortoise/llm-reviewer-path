# Full verification commands

Run from the repository root after the README setup. The README uses shorter pytest selectors so commands fit on a phone. These file-path commands preserve the exact module mapping.

Evaluation and coverage (20 tests):

```bash
uv run pytest tests/test_eval_gate.py tests/test_missing_fixture_fails_closed.py
```

Approval (29 tests):

```bash
uv run pytest tests/test_hard_action.py
```

Retrieval (9 tests):

```bash
uv run pytest tests/test_retrieval_failure_modes.py
```

Injection corpus (32 tests, 21 of them strict xfail for known detector gaps):

```bash
uv run pytest tests/test_injection_corpus.py
uv run python -m receipts.retrieval_failure_modes.injection_corpus
```

Scripted agent replay (12 tests):

```bash
uv run pytest tests/test_agent_replay.py
uv run python -m receipts.agent_replay
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

The full suite currently collects 106 tests (85 pass, 21 strict xfail). Mermaid checks cover headers and balanced subgraphs, not rendering or full syntax. The terminal GIF was re-recorded on 2026-11-17 and shows the same 85 passed, 21 xfailed.
