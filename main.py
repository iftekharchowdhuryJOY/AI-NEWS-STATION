import uuid

import uvicorn
from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.agents import researcher, editor, critic
from dotenv import load_dotenv

load_dotenv()

# --- GRAPH SETUP ---
builder = StateGraph(AgentState)
builder.add_node("researcher", researcher)
builder.add_node("editor", editor)
builder.add_node("critic", critic)

builder.add_edge(START, "researcher")
builder.add_edge("researcher", "editor")
builder.add_edge("editor", "critic")

def router(state: AgentState):
    if "REVISE" in state["messages"][-1].content.upper():
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
        "draft": state.values["messages"][-1].content,
        "status": "PAUSED_FOR_REVIEW",
        "tokens_so_far": state.values.get("total_tokens")
    }

@app.post("/approve/{thread_id}")
async def approve_post(thread_id: str):
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    graph.invoke(None, config=config)

    state = graph.get_state(config=config)
    return {
        "final_message": state.values["messages"][-1].content,
        "total_tokens": state.values.get("total_tokens"),
        "status": "COMPLETED"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)