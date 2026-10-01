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

Retrieval (5 tests):

```bash
uv run pytest tests/test_retrieval_failure_modes.py
```

Receipt (2 tests):

```bash
uv run pytest tests/test_replay.py
uv run python -m receipts
```
