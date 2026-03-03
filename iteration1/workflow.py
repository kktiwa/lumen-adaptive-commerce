from typing import TypedDict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from common.config import settings
from .prompts import adaptive_product_prompt

class SearchState(TypedDict):
    user_profile: dict
    product: dict
    generated: str

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.openai_api_key,
    temperature=0.7
)

def generate_description(state: SearchState):
    formatted = adaptive_product_prompt.format_messages(
        user_profile=state["user_profile"],
        product=state["product"]
    )
    result = llm.invoke(formatted)
    state["generated"] = result.content
    return state

workflow = StateGraph(SearchState)
workflow.add_node("generate", generate_description)
workflow.set_entry_point("generate")
workflow.add_edge("generate", END)

graph = workflow.compile()