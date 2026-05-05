from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .agents import supervisor, researcher, editor, summarizer

workflow = StateGraph(AgentState)

# 1. Add Nodes
_ = workflow.add_node("manager", supervisor)
_ = workflow.add_node("researcher", researcher)
_ = workflow.add_node("editor", editor)
_ = workflow.add_node("summarizer", summarizer)

# 2. Define the Hub-and-Spoke Flow
_ = workflow.add_edge(START, "manager")

# All workers go back to manager after finishing
_ = workflow.add_edge("researcher", "manager")
_ = workflow.add_edge("editor", "manager")
_ = workflow.add_edge("summarizer", "manager")

# 3. Manager's Decision (Conditional Edge)
def route(state: AgentState):
    next_step = str(state.get("next", "")).strip().lower()
    if next_step == "finish":
        return END
    if next_step in {"researcher", "editor", "summarizer"}:
        return next_step
    # Default to a safe worker if manager output is missing/invalid.
    return "researcher"

_ = workflow.add_conditional_edges("manager", route)

app = workflow.compile()