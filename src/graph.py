from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .agents import researcher, editor, critic
from langgraph.checkpoint.memory import MemorySaver

checkpoint = MemorySaver()

def route_after_critic(state: AgentState):
    """Logic to decide: Go back to Editor or Stop?"""
    last_msg = state["messages"][-1].content
    if "REVISE" in last_msg.upper():
        return "editor_agent" # Loop back!
    return END

workflow = StateGraph(AgentState)

workflow.add_node("researcher_agent", researcher)
workflow.add_node("editor_agent", editor)
workflow.add_node("critic_agent", critic) # New Node

# Define the Flow
workflow.add_edge(START, "researcher_agent")
workflow.add_edge("researcher_agent", "editor_agent")
workflow.add_edge("editor_agent", "critic_agent")

# The Magic: A Conditional Edge
workflow.add_conditional_edges(
    "critic_agent",
    route_after_critic
)

app = workflow.compile(
    checkpointer=checkpoint,
    interrupt_before=["critic_agent"] # It will pause here!
)