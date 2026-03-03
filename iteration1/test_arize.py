"""
Simple LLM call to test Arize project registration.
Run with: python -m iteration1.test_arize
"""
from common.config import initialize_arize_tracing, settings

# Initialize Arize tracing BEFORE any LLM calls
initialize_arize_tracing(settings)

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.openai_api_key,
    temperature=0,
)


def test_arize_tracing() -> None:
    """Make a simple LLM call to generate trace data for Arize."""
    print("\n[Test] Making LLM call (trace will be sent to Arize)...")
    response = llm.invoke("Say 'Arize test' in exactly 3 words.")
    print(f"[Test] Response: {response.content}")
    print("\n[Test] Done. Check Arize dashboard for the trace (may take 30-60 seconds).\n")


if __name__ == "__main__":
    test_arize_tracing()
