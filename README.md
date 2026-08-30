# llm-reviewer-path

Cloneable 10-minute hiring-manager index. Not a product. Not a RAG app.

```bash
git clone https://github.com/ChunkyTortoise/llm-reviewer-path
cd llm-reviewer-path
uv sync --group dev
uv run pytest
```

No API key. No network.

## Provenance

| Claim | Source | Extracted | Newly added |
|---|---|---|---|
| Retrieval failure modes + eval gate | [DocExtract](https://github.com/ChunkyTortoise/docextract) `scripts/eval_offline_replay.py`, `scripts/eval_gate.py`, [ADR-0020](https://github.com/ChunkyTortoise/docextract/blob/main/docs/adr/0020-indirect-prompt-injection-defense.md) | Failure classes and eval-as-merge-block | Mock retriever and local fixtures |
| Hard action rule | `receipts/hard_action/loop.py` | Retry and failure isolation pattern | Approval-token boundary (`new in this repo`) |
| Intentional-fail eval | DocExtract [PR #32](https://github.com/ChunkyTortoise/docextract/pull/32) | Red-gate idea | In-repo mutation so default CI stays green |
| FDE scoping story | [jorge_real_estate_bots](https://github.com/ChunkyTortoise/jorge_real_estate_bots) | Paid Acuity facts in METRICS-SOT | Redacted markdown only |

## JD matrix

| JD signal | Local receipt | Command or file | Parent proof |
|---|---|---|---|
| Eval as release gate | `receipts/eval_gate` | `uv run pytest tests/test_eval_gate.py` | DocExtract eval-gate workflow |
| Hard action rule | `receipts/hard_action` | `uv run pytest tests/test_hard_action.py` | Local retry boundary; approval token is new here |
| Retrieval failure modes | `receipts/retrieval_failure_modes` | `uv run pytest tests/test_retrieval_failure_modes.py` | DocExtract adversarial / ADR-0020 |
| FDE scoping | `receipts/fde_scope/ACUITY.md` | read (narrative, not pytest) | jorge_real_estate_bots |

## Walk (10 minutes)

1. Provenance table and parents above.
2. Eval gate: good candidate passes; `MUTATION` is rejected; default CI is green because that rejection is expected.
3. Hard action: `search_contact -> propose_update -> denied_without_approval -> approved -> execute_once -> duplicate_retry_suppressed`.
4. Retrieval failure-mode tests extracted from DocExtract. Mock retriever, no network. This is a test suite, not a RAG app.
5. Narrative receipt: `receipts/fde_scope/ACUITY.md`.

Parents stay the production systems. This repo is the cloneable index.
