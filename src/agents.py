from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from .state import AgentState

_ = load_dotenv(Path(__file__).resolve().parent.parent / ".env")

model = ChatOpenAI(model="gpt-4o")
search_tool = TavilySearch(max_results=3)
SKILLS_PATH = Path(__file__).resolve().parent.parent / "skills.md"
VALID_NEXT_STEPS = {"researcher", "editor", "summarizer", "finish"}


# --- PILLAR: ISOLATE (Load Skills) ---
def get_skills():
    with open(SKILLS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _coerce_next_step(content: str) -> str:
    normalized = (content or "").strip().lower()
    if normalized in VALID_NEXT_STEPS:
        return normalized
    for step in VALID_NEXT_STEPS:
        if step in normalized:
            return step
    # Safe default keeps flow progressing when LLM output is verbose.
    return "researcher"


def _text_content(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def _message_content(message: object) -> str:
    content = getattr(message, "content", "")
    return _text_content(content)


def supervisor(state: AgentState):
    """The Manager Node: Decides who works next based on skills.md."""
    skills = get_skills()
    prompt = (
        f"You are the Manager. Based on these skills:\n{skills}\n"
        f"Current Summary: {state.get('summary', 'None')}\n"
        "Who should work next? Options: researcher, editor, summarizer, or FINISH.\n"
        "Return exactly one word: researcher, editor, summarizer, or finish."
    )
    response = model.invoke(prompt)
    return {"next": _coerce_next_step(_text_content(response.content))}

# --- PILLAR: COMPRESS (The Summarizer) ---
def summarizer(state: AgentState):
    """Summarizes current messages into the 'summary' key and clears history."""
    current_summary = state.get("summary", "")
    new_data = str(state["messages"])
    
    prompt = f"Existing Summary: {current_summary}\nNew Events: {new_data}\nUpdate the summary."
    response = model.invoke(prompt)
    
    # We return the new summary and a special flag to clear messages
    return {
        "summary": response.content,
        "messages": [], # This clears the 'Hot Memory' to save tokens
        "next": "supervisor"
    }

# (Keep your researcher and editor functions here, but ensure they point back to supervisor)

def researcher(state: AgentState):
    query = _message_content(state["messages"][-1])
    results = search_tool.invoke({"query": query})
    return {
        "messages": [AIMessage(content="Search complete.")],
        "raw_news": str(results),
    }


def editor(state: AgentState):
    news_data = state["raw_news"]
    prompt = f"Take this news: {news_data} and write a 3-bullet point LinkedIn post."
    response = model.invoke(prompt)
    return {
        "messages": [response],
        "total_tokens": update_total_tokens(state, response),
        "input_tokens": update_input_tokens(state, response),
        "output_tokens": update_output_tokens(state, response),
        "input_tokens_details": update_input_tokens_details(state, response),
        "output_tokens_details": update_output_tokens_details(state, response),
        "input_cost": update_input_cost(state, response),
        "output_cost": update_output_cost(state, response),
    }


def critic(state: AgentState):
    last_post = _message_content(state["messages"][-1])
    prompt = (
        f"Review this post: {last_post}. Say 'REVISE' if it needs work, otherwise 'FINISH'."
    )
    response = model.invoke(prompt)
    return {
        "messages": [response],
        "total_tokens": update_total_tokens(state, response),
        "input_tokens": update_input_tokens(state, response),
        "output_tokens": update_output_tokens(state, response),
        "input_tokens_details": update_input_tokens_details(state, response),
        "output_tokens_details": update_output_tokens_details(state, response),
        "input_cost": update_input_cost(state, response),
        "output_cost": update_output_cost(state, response),
    }


def update_input_tokens(state: AgentState, response):
    usage = response.response_metadata.get("token_usage", {})
    input_tokens = state.get("input_tokens", 0)
    input_tokens += usage.get("prompt_tokens", 0)
    return input_tokens


def update_output_tokens(state: AgentState, response):
    usage = response.response_metadata.get("token_usage", {})
    output_tokens = state.get("output_tokens", 0)
    output_tokens += usage.get("completion_tokens", 0)
    return output_tokens


def update_input_tokens_details(state: AgentState, response):
    usage = response.response_metadata.get("token_usage", {})
    input_tokens_details = state.get("input_tokens_details", {})
    input_tokens_details = dict(input_tokens_details)
    for key, value in (usage.get("prompt_tokens_details") or {}).items():
        input_tokens_details[key] = input_tokens_details.get(key, 0) + value
    return input_tokens_details


def update_output_tokens_details(state: AgentState, response):
    usage = response.response_metadata.get("token_usage", {})
    output_tokens_details = state.get("output_tokens_details", {})
    output_tokens_details = dict(output_tokens_details)
    for key, value in (usage.get("completion_tokens_details") or {}).items():
        output_tokens_details[key] = output_tokens_details.get(key, 0) + value
    return output_tokens_details


def update_input_cost(state: AgentState, response):
    usage = response.response_metadata.get("token_usage", {})
    input_cost = state.get("input_cost", 0)
    input_cost += usage.get("prompt_tokens", 0) * 0.0001
    return input_cost


def update_output_cost(state: AgentState, response):
    usage = response.response_metadata.get("token_usage", {})
    output_cost = state.get("output_cost", 0)
    output_cost += usage.get("completion_tokens", 0) * 0.0001
    return output_cost


def update_total_tokens(state: AgentState, response):
    usage = response.response_metadata.get("token_usage", {})
    total_tokens = state.get("total_tokens", 0)
    total_tokens += usage.get("total_tokens", 0)
    return total_tokens



