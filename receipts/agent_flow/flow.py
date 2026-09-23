"""Offline LangGraph receipt over the local approval loop.

`build_flow` compiles a `StateGraph` with an in-memory checkpointer.
It does not call a model and it does not use the network.
Writes go through `ActionLoop`.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from receipts.hard_action.loop import ActionLoop, ApprovalError


class FlowState(TypedDict, total=False):
    query: str
    patch: dict[str, str]
    preview_id: str
    approval: str | None
    contact_name: str
    status: str


def build_flow(loop: ActionLoop):
    """Search, preview, then pause until a resume decides the write."""

    def search(state: FlowState) -> dict[str, str]:
        found = loop.search_contact(state["query"])
        return {"contact_name": found["name"], "status": "searched"}

    def propose(state: FlowState) -> dict[str, str]:
        preview = loop.propose_update(state["query"], state["patch"])
        return {"preview_id": preview["preview_id"], "status": "preview"}

    def await_approval(state: FlowState) -> dict[str, str | None]:
        decision = interrupt(
            {"preview_id": state["preview_id"], "status": "awaiting_approval"}
        )
        return {
            "approval": _approval_from_resume(decision),
            "status": "awaiting_approval",
        }

    def route_after_approval(state: FlowState) -> Literal["commit", "refuse"]:
        preview_id = state.get("preview_id")
        if not isinstance(preview_id, str):
            return "refuse"
        if loop.approval_matches(preview_id, state.get("approval")):
            return "commit"
        return "refuse"

    def refuse(state: FlowState) -> dict[str, str]:
        try:
            result = loop.execute(state["preview_id"], approval=state.get("approval"))
        except ApprovalError:
            return {"status": "denied_untrusted_approval"}
        return {"status": result["status"]}

    def commit(state: FlowState) -> dict[str, str]:
        result = loop.execute(state["preview_id"], approval=state.get("approval"))
        return {"status": result["status"]}

    graph = StateGraph(FlowState)
    graph.add_node("search", search)
    graph.add_node("propose", propose)
    graph.add_node("await_approval", await_approval)
    graph.add_node("refuse", refuse)
    graph.add_node("commit", commit)
    graph.add_edge(START, "search")
    graph.add_edge("search", "propose")
    graph.add_edge("propose", "await_approval")
    graph.add_conditional_edges(
        "await_approval",
        route_after_approval,
        {"commit": "commit", "refuse": "refuse"},
    )
    graph.add_edge("commit", END)
    graph.add_edge("refuse", END)
    return graph.compile(checkpointer=InMemorySaver())


def _approval_from_resume(decision: object) -> str | None:
    if not isinstance(decision, dict):
        return None
    approval = decision.get("approval")
    if isinstance(approval, str):
        return approval
    return None
