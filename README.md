# llm-reviewer-path

**Run an evaluation gate, reject an unapproved write, and inspect a duplicate retry.** A small offline index for applied AI and backend engineering: 19 tests, local fixtures, no API keys. Tests run without network access after setup.

This repository is an index, not a product. [DocExtract](https://github.com/ChunkyTortoise/docextract) stays the production system for the eval and retrieval claims below.

[![Tests](https://github.com/ChunkyTortoise/llm-reviewer-path/actions/workflows/ci.yml/badge.svg)](https://github.com/ChunkyTortoise/llm-reviewer-path/actions/workflows/ci.yml)

[Run the offline checks](#run) · [Read the captured receipt](docs/offline-receipt.md)

<p align="center">
  <img src="./docs/assets/reviewer-receipt.svg" width="460" alt="Eval-gate receipt showing a good candidate passing, a mutation failing, and the hard-action approval sequence." />
</p>

The figure summarizes actual local output. It is an editorial diagram, not a product screenshot. [Read the receipt and its limits](docs/offline-receipt.md).

## Run

Python 3.10 or newer, and [uv](https://docs.astral.sh/uv/getting-started/installation/). There is no Makefile. The commands match `pyproject.toml` (`requires-python`, dev group `pytest>=8`, `addopts = "-q"`) and [`.github/workflows/ci.yml`](.github/workflows/ci.yml) (`uv sync --group dev`, then `uv run pytest`).

```bash
git clone https://github.com/ChunkyTortoise/llm-reviewer-path.git
cd llm-reviewer-path
uv sync --group dev
uv run pytest
```

`uv.lock` pins pytest 9.1.1. Quiet mode hides the platform and Python banner.

<details>
<summary><b>Expected terminal output (19 passed)</b></summary>

80-column capture. The stable result is `19 passed`. The seconds value moves (this capture was 0.02s).

```text
...................                                                      [100%]
19 passed in 0.02s
```

| File | Tests |
|---|---:|
| `tests/test_eval_gate.py` | 3 |
| `tests/test_hard_action.py` | 10 |
| `tests/test_missing_fixture_fails_closed.py` | 1 |
| `tests/test_retrieval_failure_modes.py` | 5 |
| **Total** | **19** |

</details>

> **Evidence boundary:** This repository is an index, not a product or a RAG app. It documents the offline tests and receipts below. It does not claim unlisted production behavior, client details, metrics, or features. The local eval gate is a boolean on 5 fixtures. It is not branch protection on DocExtract.

## JD matrix

| Hiring signal | What the local receipt shows | Command or file | Parent proof |
|---|---|---|---|
| Eval as a CI check | 5 labels, floor `1.00`. `GOOD` scores 1.00 and `gate()` is true. `MUTATION` labels the injection case as clean and `gate()` is false. An unknown case id raises `KeyError` (the run fails closed; it does not skip). | `uv run pytest tests/test_eval_gate.py tests/test_missing_fixture_fails_closed.py` (4 tests) | [`scripts/eval_offline_replay.py`](https://github.com/ChunkyTortoise/docextract/blob/main/scripts/eval_offline_replay.py) (`--floor 0.85`), [`scripts/eval_gate.py`](https://github.com/ChunkyTortoise/docextract/blob/main/scripts/eval_gate.py) (exit 1 on a threshold breach), [`eval-gate.yml`](https://github.com/ChunkyTortoise/docextract/blob/main/.github/workflows/eval-gate.yml), [`docs/eval-gate-proof.md`](https://github.com/ChunkyTortoise/docextract/blob/main/docs/eval-gate-proof.md), open red PR [#32](https://github.com/ChunkyTortoise/docextract/pull/32). This index does not change DocExtract branch protection. DocExtract records that a 2026-09-19 audit found the default branch unprotected. |
| Approval boundary on writes | `search_contact` needs no token. `propose_update` returns a preview. `execute` with no token returns `denied_without_approval`. Model-written approval text raises `ApprovalError`. `issue_approval` mints a token; `execute` with that token returns `execute_once` once, then `duplicate_retry_suppressed`. The compare uses `secrets.compare_digest`. The contact row is in memory, not a live CRM call. | `uv run pytest tests/test_hard_action.py` (10 tests) | None. The approval-token boundary is local to this index. |
| Retrieval failure modes | Mock `classify()` on 5 fixtures: `empty_retrieval`, `conflicting_evidence`, `prompt_injection`, `malformed_structured_output`, and one clean pass. No network. | `uv run pytest tests/test_retrieval_failure_modes.py` (5 tests) | Indirect prompt injection in untrusted document text: [ADR-0020](https://github.com/ChunkyTortoise/docextract/blob/main/docs/adr/0020-indirect-prompt-injection-defense.md) and the prompt-injection row in [`docs/eval-failure-analysis.md`](https://github.com/ChunkyTortoise/docextract/blob/main/docs/eval-failure-analysis.md). The parent control is [`app/services/injection_guard.py`](https://github.com/ChunkyTortoise/docextract/blob/main/app/services/injection_guard.py). `receipts/retrieval_failure_modes/retriever.py` is a local mock, not that guard. |
| Field-engineering scope | Redacted scope note: customer problem, constraints, first slice, exclusions, kill-check, and handoff. Pytest does not collect it. | [`receipts/fde_scope/ACUITY.md`](receipts/fde_scope/ACUITY.md) | `ChunkyTortoise/jorge_real_estate_bots` is not a public repository (HTTP 404). `METRICS-SOT.md` is not in this repo. The markdown in this index is the receipt. |

## Architecture and approval boundaries

### Hard-action receipt

`receipts/hard_action/loop.py` isolates a write behind an approval token. Reads stay open. A preview is not an execution. Text from the model is not a token. A used token cannot run the write again. The updated row lives in an in-memory dict. This is a single-process teaching example, not a production authorization service. Approval issuance is callable by the same Python process; callers must supply that trust boundary. Incoming and returned patches are copied. A token is bound to a snapshot of its target query and patch; changing the stored proposal after approval raises `ApprovalError` before any write. Durable storage, concurrent execution, token expiry and a separately authenticated approver remain outside this example.

```mermaid
sequenceDiagram
    autonumber
    actor Approver
    actor Agent
    participant Loop as ActionLoop

    Agent->>Loop: search_contact("ada")
    Loop-->>Agent: ok, contact fields

    Agent->>Loop: propose_update("ada", patch)
    Loop-->>Agent: status=preview, preview_id

    Agent->>Loop: execute(preview_id, approval=None)
    Loop-->>Agent: denied_without_approval

    Agent->>Loop: execute(preview_id, model text)
    Loop-->>Agent: ApprovalError untrusted approval

    Approver->>Loop: issue_approval(preview_id)
    Loop-->>Approver: tok_...

    Agent->>Loop: execute(preview_id, token)
    Loop-->>Agent: execute_once

    Agent->>Loop: execute(preview_id, token)
    Loop-->>Agent: duplicate_retry_suppressed
```

### Eval-gate receipt

`receipts/eval_gate/gate.py` scores five local labels. `gate()` returns true only when `score >= 1.00`. Default CI on this repo stays green because the mutation test expects `gate()` to be false. That is a different demonstration from DocExtract PR #32, which is left open so the parent workflow stays red.

```mermaid
flowchart LR
    subgraph Gate["Local evaluation gate"]
        Cand["GOOD or MUTATION labels"] --> Replay["5-case replay"]
        Replay --> Eval["score = hits / n"]
        Eval --> Floor{"score >= 1.00?"}
        Floor -->|Pass| Allow["gate() returns true"]
        Floor -->|Fail| Block["gate() returns false"]
    end
```

Unknown case ids never reach that floor check. `evaluate()` raises `KeyError` first (`tests/test_missing_fixture_fails_closed.py`).

## Provenance

Checked against DocExtract `main` and the public GitHub account on 2026-09-23.

| Claim | Source | Taken from the parent | Added in this repo |
|---|---|---|---|
| Eval gate | DocExtract [`scripts/eval_offline_replay.py`](https://github.com/ChunkyTortoise/docextract/blob/main/scripts/eval_offline_replay.py), [`scripts/eval_gate.py`](https://github.com/ChunkyTortoise/docextract/blob/main/scripts/eval_gate.py), [`docs/eval-gate-proof.md`](https://github.com/ChunkyTortoise/docextract/blob/main/docs/eval-gate-proof.md), [PR #32](https://github.com/ChunkyTortoise/docextract/pull/32) | Offline replay as a CI check, and a public red regression | 5-label floor at 1.00. The mutation is asserted here, so this repo's CI stays green. |
| Retrieval failure modes | DocExtract [ADR-0020](https://github.com/ChunkyTortoise/docextract/blob/main/docs/adr/0020-indirect-prompt-injection-defense.md), [`docs/eval-failure-analysis.md`](https://github.com/ChunkyTortoise/docextract/blob/main/docs/eval-failure-analysis.md) | Indirect prompt injection in untrusted document text | Local mock and five fixtures: empty, conflict, injection, malformed, clean |
| Hard action | `receipts/hard_action/loop.py` | No DocExtract parent | Approval token, denial, `compare_digest`, one execution, duplicate suppression |
| FDE scoping | [`receipts/fde_scope/ACUITY.md`](receipts/fde_scope/ACUITY.md) | `ChunkyTortoise/jorge_real_estate_bots` is not public (HTTP 404). `METRICS-SOT.md` is not in this repo. | Redacted markdown only. Not a pytest. |

## Walk (10 minutes)

1. Run the clone, `uv sync --group dev`, and `uv run pytest`. Confirm `19 passed`.
2. Read the provenance table before treating any parent number as a result from this repo.
3. Eval gate: `GOOD` passes, `MUTATION` fails, an unknown id raises `KeyError`.
4. Hard action: `search_contact`, `propose_update`, `denied_without_approval`, `ApprovalError` on model text, `issue_approval`, `execute_once`, `duplicate_retry_suppressed`.
5. Retrieval: five fixture ids in `receipts/retrieval_failure_modes/cases.py`.
6. Scope: read `receipts/fde_scope/ACUITY.md`. It is narrative. The public parent URL is not available.

Parents that are public stay the production systems. This repo is the cloneable index.
