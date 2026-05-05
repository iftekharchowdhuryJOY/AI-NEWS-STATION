import uuid
from typing import Literal

import uvicorn
from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.agents import researcher, editor, critic
from dotenv import load_dotenv

_ = load_dotenv()

# --- GRAPH SETUP ---
builder = StateGraph(AgentState)
builder.add_node("researcher", researcher)
builder.add_node("editor", editor)
builder.add_node("critic", critic)

builder.add_edge(START, "researcher")
builder.add_edge("researcher", "editor")
builder.add_edge("editor", "critic")

def _message_content(message: object) -> str:
    content = getattr(message, "content", "")
    return content if isinstance(content, str) else str(content)


def _has_messages(config: RunnableConfig) -> bool:
    state = graph.get_state(config=config)
    messages = state.values.get("messages", [])
    return isinstance(messages, list) and len(messages) > 0


def router(state: AgentState):
    decision = str(state.get("review_decision", "")).strip().lower()
    if decision == "revise":
        return "editor"
    if decision == "approve":
        return END
    if "REVISE" in _message_content(state["messages"][-1]).upper():
        return "editor"
    return END

builder.add_conditional_edges("critic", router)

# Enable HITL: Interrupt BEFORE the critic node
memory = MemorySaver()
graph = builder.compile(checkpointer=memory, interrupt_before=["critic"])

# --- API SETUP ---
app = FastAPI(title="AI News Station API")

class NewsRequest(BaseModel):
    topic: str


class ReviewRequest(BaseModel):
    decision: Literal["revise", "approve"]
    feedback: str = ""


@app.post("/start")
async def start_research(request: NewsRequest):
    thread_id = str(uuid.uuid4())
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    inputs: AgentState = {
        "messages": [HumanMessage(content=request.topic)],
        "raw_news": "",
    }
    graph.invoke(inputs, config=config)

    # Get current state to show the user what was drafted
    state = graph.get_state(config=config)
    return {
        "thread_id": thread_id,
        "draft": _message_content(state.values["messages"][-1]),
        "status": "PAUSED_FOR_REVIEW",
        "tokens_so_far": state.values.get("total_tokens")
    }


@app.post("/review/{thread_id}")
async def review_post(thread_id: str, request: ReviewRequest):
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    if not _has_messages(config):
        raise HTTPException(
            status_code=404,
            detail="Thread not found or expired. Start a new run via /start.",
        )
    graph.update_state(
        config=config,
        values={
            "review_decision": request.decision,
            "review_feedback": request.feedback.strip(),
        },
    )
    graph.invoke(None, config=config)

    state = graph.get_state(config=config)
    is_paused_for_revise = request.decision == "revise"
    return {
        "thread_id": thread_id,
        "decision": request.decision,
        "message": _message_content(state.values["messages"][-1]),
        "status": "PAUSED_FOR_REVIEW" if is_paused_for_revise else "COMPLETED",
        "total_tokens": state.values.get("total_tokens"),
    }


@app.post("/approve/{thread_id}")
async def approve_post(thread_id: str):
    return await review_post(thread_id, ReviewRequest(decision="approve"))


@app.get("/draft/{thread_id}")
async def get_draft(thread_id: str):
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    if not _has_messages(config):
        raise HTTPException(
            status_code=404,
            detail="Thread not found or expired. Start a new run via /start.",
        )

    state = graph.get_state(config=config)
    return {
        "thread_id": thread_id,
        "message": _message_content(state.values["messages"][-1]),
        "status": "PAUSED_FOR_REVIEW" if state.next is not None else "COMPLETED",
        "total_tokens": state.values.get("total_tokens"),
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)