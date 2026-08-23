from __future__ import annotations

import secrets
from typing import Any


class ApprovalError(ValueError):
    pass


class ActionLoop:
    def __init__(self) -> None:
        self._contacts = {"ada": {"name": "Ada", "city": "NY"}}
        self._previews: dict[str, dict[str, Any]] = {}
        self._approvals: dict[str, str] = {}
        self._executed: set[str] = set()
        self.audit: list[dict[str, str]] = []

    def search_contact(self, query: str) -> dict[str, Any]:
        row = self._contacts[query.lower()]
        self.audit.append({"kind": "search_contact", "query": query})
        return {"ok": True, **row}

    def propose_update(self, query: str, patch: dict[str, str]) -> dict[str, Any]:
        preview_id = secrets.token_hex(8)
        self._previews[preview_id] = {"query": query.lower(), "patch": patch}
        self.audit.append({"kind": "propose_update", "preview_id": preview_id})
        return {"status": "preview", "preview_id": preview_id, "patch": patch}

    def issue_approval(self, preview_id: str) -> str:
        token = "tok_" + secrets.token_hex(8)
        self._approvals[preview_id] = token
        self.audit.append({"kind": "issued_approval", "preview_id": preview_id})
        return token

    def execute(self, preview_id: str, approval: str | None) -> dict[str, Any]:
        if approval is None:
            self.audit.append(
                {"kind": "denied_without_approval", "preview_id": preview_id}
            )
            return {"status": "denied_without_approval"}
        expected = self._approvals.get(preview_id)
        if expected is None or approval != expected:
            raise ApprovalError("untrusted approval")
        if preview_id in self._executed:
            self.audit.append(
                {"kind": "duplicate_retry_suppressed", "preview_id": preview_id}
            )
            return {"status": "duplicate_retry_suppressed"}
        spec = self._previews[preview_id]
        self._contacts[spec["query"]].update(spec["patch"])
        self._executed.add(preview_id)
        self.audit.append({"kind": "execute_once", "preview_id": preview_id})
        return {"status": "execute_once"}
