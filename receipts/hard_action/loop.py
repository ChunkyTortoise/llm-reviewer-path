from __future__ import annotations

import secrets
from typing import Any


class ApprovalError(ValueError):
    pass


def _validated_patch(patch: object) -> dict[str, str]:
    """Copy a patch once into a plain dict of exact str keys and values.

    Rejecting containers and str subclasses keeps the stored, returned and approved
    copies independent of any object the caller still holds.
    """
    if type(patch) is not dict:
        raise TypeError("patch must be a dict")
    copied: dict[str, str] = {}
    for key, value in patch.items():
        if type(key) is not str or type(value) is not str:
            raise TypeError("patch keys and values must be plain str")
        copied[key] = value
    return copied


class ActionLoop:
    def __init__(self) -> None:
        self._contacts = {"ada": {"name": "Ada", "city": "NY"}}
        self._previews: dict[str, dict[str, Any]] = {}
        self._approvals: dict[str, str] = {}
        self._approved_specs: dict[str, dict[str, Any]] = {}
        self._executed: set[str] = set()
        self.audit: list[dict[str, str]] = []

    def search_contact(self, query: str) -> dict[str, Any]:
        row = self._contacts[query.lower()]
        self.audit.append({"kind": "search_contact", "query": query})
        return {"ok": True, **row}

    def propose_update(self, query: str, patch: dict[str, str]) -> dict[str, Any]:
        normalized = query.lower()
        if normalized not in self._contacts:
            raise KeyError(query)
        stored = _validated_patch(patch)
        preview_id = secrets.token_hex(8)
        self._previews[preview_id] = {"query": normalized, "patch": stored}
        self.audit.append({"kind": "propose_update", "preview_id": preview_id})
        return {"status": "preview", "preview_id": preview_id, "patch": dict(stored)}

    def issue_approval(self, preview_id: str) -> str:
        if preview_id in self._executed:
            raise ApprovalError("preview already executed")
        spec = self._previews[preview_id]
        self._approved_specs[preview_id] = {
            "query": spec["query"],
            "patch": dict(spec["patch"]),
        }
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
        if (
            expected is None
            or not isinstance(approval, str)
            or not secrets.compare_digest(
                approval.encode("utf-8", "surrogatepass"), expected.encode("utf-8")
            )
        ):
            self.audit.append(
                {"kind": "denied_untrusted_approval", "preview_id": preview_id}
            )
            raise ApprovalError("untrusted approval")
        spec = self._previews[preview_id]
        if spec != self._approved_specs[preview_id]:
            self.audit.append(
                {"kind": "denied_changed_proposal", "preview_id": preview_id}
            )
            raise ApprovalError("proposal changed after approval")
        if preview_id in self._executed:
            self.audit.append(
                {"kind": "duplicate_retry_suppressed", "preview_id": preview_id}
            )
            return {"status": "duplicate_retry_suppressed"}
        self._contacts[spec["query"]].update(spec["patch"])
        self._executed.add(preview_id)
        self.audit.append({"kind": "execute_once", "preview_id": preview_id})
        return {"status": "execute_once"}
