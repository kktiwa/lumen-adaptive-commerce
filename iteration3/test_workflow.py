"""Quick test harness to simulate a user conversation and verify workflow transitions.
This script uses unittest.mock to patch llm.invoke with predictable responses.
"""
from unittest.mock import patch, MagicMock
from iteration3.agentic_workflow import initialize_state, process_message
import asyncio


class MockResponse:
    def __init__(self, content):
        self.content = content

def mock_llm_invoke(messages, **kwargs):
    """Mock LLM invoke that returns predictable responses based on prompt content."""
    content = messages[-1].content if messages else ""
    if "Analyze this conversation and extract" in content:
        return MockResponse('{"occasion": "birthday", "category": "toys", "age_group": "8-10", "budget_range": "$50-100", "quantity_needed": 1, "specific_needs": [], "preferred_features": []}')
    elif "Based on this conversation, we need to find the right product" in content:
        return MockResponse("What is the occasion?")
    elif "You are an expert at extracting" in content or "You are an expert" in content:
        return MockResponse('{}')
    else:
        return MockResponse('{}')


async def run_test():
    state = initialize_state()
    # Simulate user providing category, age, budget in one message
    user_message = "I'm shopping for toys for an 8-10 year old, budget $50-100, for a birthday."
    
    # Patch the entire llm object (ChatOpenAI is a Pydantic model, so we can't patch .invoke directly)
    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(side_effect=mock_llm_invoke)
    with patch('iteration3.agentic_workflow.llm', mock_llm):
        new_state = await process_message(state, user_message)

    print("Next action:", new_state["next_action"]) 
    print("Selected product:", new_state.get("selected_product"))
    print("Assistant response:\n", new_state.get("assistant_response"))
    print("Current order:", new_state.get("current_order"))

if __name__ == '__main__':
    asyncio.run(run_test())
