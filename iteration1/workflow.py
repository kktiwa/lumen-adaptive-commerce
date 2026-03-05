import json
import re
from typing import TypedDict, Any, Optional

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from common.config import initialize_arize_tracing, settings
from .prompts import adaptive_product_prompt
from .eval.llm_eval_framework import evaluate_sections, normalize_section_inputs

# Initialize Arize tracing BEFORE importing workflow
initialize_arize_tracing(settings)


class SearchState(TypedDict, total=False):
    user_profile: dict
    product: dict
    generated: str
    eval_report: Optional[dict]


llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.openai_api_key,
    temperature=0.7,
)


def generate_description(state: SearchState):
    formatted = adaptive_product_prompt.format_messages(
        user_profile=state["user_profile"],
        product=state["product"],
    )
    result = llm.invoke(formatted)
    state["generated"] = result.content
    return state


def evaluate_description(state: SearchState):
    """Run LLM-as-judge evaluation on the generated product description and store report."""
    generated = state.get("generated", "") or ""
    if not generated:
        state["eval_report"] = {
            "timestamp": "",
            "sections_evaluated": 0,
            "overall_average": 0.0,
            "results": [],
            "error": "No generated content to evaluate",
        }
        return state

    text = str(generated).strip()
    # Extract JSON from markdown code blocks if present
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1)

    try:
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            parsed = {"summary": str(parsed)}
    except json.JSONDecodeError:
        parsed = {"summary": generated}

    inputs = normalize_section_inputs(parsed)
    try:
        report = evaluate_sections(
            inputs=inputs,
            api_key=settings.openai_api_key,
            model="gpt-4o-mini",
            parallel=True,
        )
    except Exception as e:
        report = {
            "timestamp": "",
            "sections_evaluated": 0,
            "overall_average": 0.0,
            "results": [],
            "error": str(e),
        }
    state["eval_report"] = report
    return state


workflow = StateGraph(SearchState)
workflow.add_node("generate", generate_description)
workflow.add_node("evaluate", evaluate_description)
workflow.set_entry_point("generate")
workflow.add_edge("generate", "evaluate")
workflow.add_edge("evaluate", END)

graph = workflow.compile()