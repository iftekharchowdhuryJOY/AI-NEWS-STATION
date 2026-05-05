from typing import Annotated, NotRequired, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Shared graph state for both API and workflow modules."""

    messages: Annotated[list[object], add_messages]
    raw_news: str
    review_decision: NotRequired[str]
    review_feedback: NotRequired[str]
    summary: NotRequired[str]
    next: NotRequired[str]
    stats: NotRequired[dict[str, object]]
    total_tokens: NotRequired[int]
    input_tokens: NotRequired[int]
    output_tokens: NotRequired[int]
    input_tokens_details: NotRequired[dict[str, int]]
    output_tokens_details: NotRequired[dict[str, int]]
    input_cost: NotRequired[float]
    output_cost: NotRequired[float]