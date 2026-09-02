# llm-reviewer-path

[![ci](https://github.com/ChunkyTortoise/llm-reviewer-path/actions/workflows/ci.yml/badge.svg)](https://github.com/ChunkyTortoise/llm-reviewer-path/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Cloneable 10-minute hiring-manager index. Not a product. Not a RAG app.

```bash
git clone https://github.com/ChunkyTortoise/llm-reviewer-path
cd llm-reviewer-path
uv run pytest
```

No API key. No network. 14 offline unit tests verify evaluation gating, approval-token hard action isolation, and retrieval failure modes in ~0.01s.

<details>
<summary><b>View expected terminal output (14 passed in 0.01s)</b></summary>

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.1.1, pluggy-1.6.0
collected 14 items

tests/test_eval_gate.py ...                                              [ 21%]
tests/test_hard_action.py .....                                          [ 57%]
tests/test_missing_fixture_fails_closed.py .                             [ 64%]
tests/test_retrieval_failure_modes.py .....                              [100%]

============================== 14 passed in 0.01s ==============================
```

</details>

## Architecture & Approval Boundaries

### 1. Hard Action Approval Token Flow
Demonstrates runtime isolation of dangerous side effects (CRM updates, external calls) behind a cryptographic approval-token gate with duplicate suppression:

```mermaid
sequenceDiagram
    autonumber
    actor Agent as AI Agent
    participant Action as Hard Action Boundary
    participant Token as Approval Token Gate
    participant API as External CRM / State

    Agent->>Action: search_contact(lead_id)
    Action-->>Agent: contact_info (read-only)
    Agent->>Action: propose_update(status="qualified")
    Action->>Token: verify_token()
    Token-->>Action: Token Missing
    Action-->>Agent: ActionBlocked(requires_approval_token)
    
    Note over Agent,Token: Human or System signs approval
    Agent->>Token: sign_approval(request_id)
    Token-->>Agent: valid_approval_token

    Agent->>Action: execute_update(payload, approval_token)
    Action->>Token: verify_token()
    Token-->>Action: Valid
    Action->>API: execute_once()
    API-->>Action: 200 OK
    Action-->>Agent: Success(state="updated")

    Note over Agent,Action: Idempotency & Retry Suppression
    Agent->>Action: execute_update(payload, approval_token) [Duplicate Retry]
    Action-->>Agent: DuplicateExecutionSuppressed
```

### 2. Evaluation Gate as CI Merge Block
Demonstrates how offline fixture replays act as strict deployment and merge gates:

```mermaid
flowchart LR
    subgraph Gate["Evaluation Release Gate"]
        Cand["Candidate Model / Prompt"] --> Replay["28-Fixture Replay Run"]
        Replay --> Eval["Metric Calculation"]
        Eval --> Floor{"Score >= 0.85 Floor?"}
        Floor -->|Pass| Merge["Merge Allowed (CI Green)"]
        Floor -->|Fail / Mutation| Block["Merge Blocked (Release Prevented)"]
    end
```

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
