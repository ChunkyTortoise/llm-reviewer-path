from __future__ import annotations

import copy
import secrets
from collections.abc import Callable
from datetime import datetime, timezone
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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ActionLoop:
    def __init__(self, clock: Callable[[], str] = _utc_now) -> None:
        self._contacts = {"ada": {"name": "Ada", "city": "NY"}}
        self._previews: dict[str, dict[str, Any]] = {}
        self._approvals: dict[str, str] = {}
        self._approved_specs: dict[str, dict[str, Any]] = {}
        self._executed: set[str] = set()
        self._clock = clock
        self._audit: list[dict[str, Any]] = []

    @property
    def audit(self) -> list[dict[str, Any]]:
        """Copy of the audit record; changing the copy does not change the record."""
        return copy.deepcopy(self._audit)

    def _record(self, kind: str, **fields: Any) -> None:
        self._audit.append({"kind": kind, "at": self._clock(), **fields})

    def _record_proposal(self, kind: str, preview_id: str, **fields: Any) -> None:
        # Execute events describe the approved snapshot when one exists, so the
        # record shows what the approver saw even if the stored proposal changed.
        spec = self._approved_specs.get(preview_id, self._previews[preview_id])
        self._record(
            kind,
            preview_id=preview_id,
            target=spec["query"],
            patch=dict(spec["patch"]),
            **fields,
        )

    def _record_execute(
        self, kind: str, preview_id: str, *, presented: bool, accepted: bool, reason: str = ""
    ) -> None:
        # Approval values are never recorded, only whether one was presented and accepted.
        fields: dict[str, Any] = {"approval_presented": presented, "approval_accepted": accepted}
        if reason:
            fields["reason"] = reason
        self._record_proposal(kind, preview_id, **fields)

    def search_contact(self, query: str) -> dict[str, Any]:
        normalized = query.lower()
        row = self._contacts[normalized]
        self._record("search_contact", target=normalized, query=query)
        return {"ok": True, **row}

    def propose_update(self, query: str, patch: dict[str, str]) -> dict[str, Any]:
        normalized = query.lower()
        if normalized not in self._contacts:
            raise KeyError(query)
        stored = _validated_patch(patch)
        for key in stored:
            # Only fields the target contact already has can be patched, so a
            # patch cannot add a field or shadow the "ok" key of the read envelope.
            if key not in self._contacts[normalized]:
                raise KeyError(key)
        preview_id = secrets.token_hex(8)
        self._previews[preview_id] = {"query": normalized, "patch": stored}
        self._record_proposal("propose_update", preview_id)
        return {
            "status": "preview",
            "preview_id": preview_id,
            "query": normalized,
            "patch": dict(stored),
        }

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
        self._record_proposal("issued_approval", preview_id)
        return token

    def execute(self, preview_id: str, approval: str | None) -> dict[str, Any]:
        if preview_id not in self._previews:
            # An id that propose_update never returned is not written to the audit list.
            raise KeyError(preview_id)
        if approval is None:
            self._record_execute(
                "denied_without_approval",
                preview_id,
                presented=False,
                accepted=False,
                reason="no approval presented",
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
            self._record_execute(
                "denied_untrusted_approval",
                preview_id,
                presented=True,
                accepted=False,
                reason=(
                    "no approval issued for this preview"
                    if expected is None
                    else "approval does not match the issued token"
                ),
            )
            raise ApprovalError("untrusted approval")
        spec = self._previews[preview_id]
        if spec != self._approved_specs[preview_id]:
            self._record_execute(
                "denied_changed_proposal",
                preview_id,
                presented=True,
                accepted=False,
                reason="proposal changed after approval",
            )
            raise ApprovalError("proposal changed after approval")
        if preview_id in self._executed:
            self._record_execute(
                "duplicate_retry_suppressed", preview_id, presented=True, accepted=True
            )
            return {"status": "duplicate_retry_suppressed"}
        self._contacts[spec["query"]].update(spec["patch"])
        self._executed.add(preview_id)
        self._record_execute("execute_once", preview_id, presented=True, accepted=True)
        return {"status": "execute_once"}
