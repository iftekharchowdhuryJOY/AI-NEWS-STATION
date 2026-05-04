from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch

from .state import AgentState

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

model = ChatOpenAI(model="gpt-4o")
search_tool = TavilySearch(max_results=3)


def researcher(state: AgentState):
    query = state["messages"][-1].content
    results = search_tool.invoke({"query": query})
    return {
        "messages": [("assistant", "Search complete.")],
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
    last_post = state["messages"][-1].content
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
    input_tokens_details.update(usage.get("prompt_tokens_details") or {})
    return input_tokens_details


def update_output_tokens_details(state: AgentState, response):
    usage = response.response_metadata.get("token_usage", {})
    output_tokens_details = state.get("output_tokens_details", {})
    output_tokens_details = dict(output_tokens_details)
    output_tokens_details.update(usage.get("completion_tokens_details") or {})
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
