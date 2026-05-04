from typing import Annotated, Any, NotRequired, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Graph state. Avoid keys reserved by LangGraph (e.g. ``checkpoint_id``)."""

    messages: Annotated[list[Any], add_messages]
    raw_news: str
    stats: NotRequired[dict[str, Any]]
    total_tokens: NotRequired[Any]
    input_tokens: NotRequired[Any]
    output_tokens: NotRequired[Any]
    input_tokens_details: NotRequired[dict[str, Any]]
    output_tokens_details: NotRequired[dict[str, Any]]
    input_cost: NotRequired[Any]
    output_cost: NotRequired[Any]
