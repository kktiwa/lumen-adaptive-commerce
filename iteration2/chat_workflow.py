"""LangGraph workflow for multi-turn conversations"""
from typing import TypedDict, List, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from common.config import settings, initialize_arize_tracing
from .conversation_types import ConversationState, ConversationMessage, ConversationContext
from .user_preferences import load_user_preferences
from .chat_prompts import get_system_prompt, get_recommendation_prompt
from .product_database import search_products

# Initialize Arize tracing
initialize_arize_tracing(settings)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.openai_api_key,
    temperature=0.7
)

def process_user_message(state: ConversationState) -> ConversationState:
    """Process the user's current message and update context"""
    message = state["current_message"]
    
    # Add user message to history
    user_msg = ConversationMessage(
        role="user",
        content=message,
        timestamp=datetime.now()
    )
    state["conversation_history"].append(user_msg)
    
    return state

def extract_context(state: ConversationState) -> ConversationState:
    """Extract conversation context from messages"""
    # For now, we'll do simple extraction based on keywords
    # In production, this could use a separate LLM call
    
    message = state["current_message"].lower()
    context = state["conversation_context"]
    
    # Extract occasion
    occasion_keywords = {
        "birthday": "birthday party",
        "party": "birthday party",
        "camping": "camping trip",
        "outdoor": "outdoor activity",
        "rainy": "indoor activity"
    }
    
    for keyword, occasion in occasion_keywords.items():
        if keyword in message:
            context["occasion"] = occasion
            break
    
    # Extract age range
    age_keywords = {
        "5": "5-8",
        "6": "5-8", 
        "7": "5-8",
        "8": "5-10",
        "9": "5-10",
        "10": "5-12",
    }
    
    for keyword, age in age_keywords.items():
        if keyword in message:
            context["age_group"] = age
            break
    
    # Extract quantity if mentioned
    if "kids" in message or "children" in message:
        context["quantity_needed"] = 1  # Will be updated later
    
    state["conversation_context"] = context
    return state

def generate_response(state: ConversationState) -> ConversationState:
    """Generate assistant response based on conversation state"""
    
    # Build conversation history for context
    history_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in state["conversation_history"][-5:]  # Last 5 messages for context
    ])
    
    # Get system prompt with user context
    system_msg = get_system_prompt(
        budget=state["user_preferences"]["budget"],
        interests=state["user_preferences"]["interests"],
        preferences=state["user_preferences"]["preferences"],
        history=history_text
    )
    
    # Generate response
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": state["current_message"]}
    ]
    
    response = llm.invoke(messages)
    state["assistant_response"] = response.content
    
    # Add assistant message to history
    assistant_msg = ConversationMessage(
        role="assistant",
        content=response.content,
        timestamp=datetime.now()
    )
    state["conversation_history"].append(assistant_msg)
    
    # Check if we have enough context to recommend
    if "[READY_TO_RECOMMEND]" in response.content:
        state["conversation_complete"] = True
        state["assistant_response"] = state["assistant_response"].replace("[READY_TO_RECOMMEND]", "").strip()
    
    return state

def get_recommendations(state: ConversationState) -> ConversationState:
    """Get product recommendations based on conversation context"""
    
    if not state["conversation_complete"]:
        return state
    
    context = state["conversation_context"]
    
    # Extract max price from budget
    budget = state["user_preferences"]["budget"]
    max_price_map = {
        "$0-50": 50,
        "$50-100": 100,
        "$100-200": 200,
        "$200+": 500
    }
    max_price = max_price_map.get(budget, 100)
    
    # Search for products
    products = search_products(
        occasion=context.get("occasion"),
        age_range=context.get("age_group"),
        max_price=max_price,
        educational=state["user_preferences"]["preferences"].get("educational", True)
    )
    
    state["product_recommendations"] = products
    
    return state

# Build the graph
workflow = StateGraph(ConversationState)

# Add nodes
workflow.add_node("process_message", process_user_message)
workflow.add_node("extract_context", extract_context)
workflow.add_node("generate_response", generate_response)
workflow.add_node("get_recommendations", get_recommendations)

# Set entry point
workflow.set_entry_point("process_message")

# Add edges
workflow.add_edge("process_message", "extract_context")
workflow.add_edge("extract_context", "generate_response")
workflow.add_edge("generate_response", "get_recommendations")
workflow.add_edge("get_recommendations", END)

# Compile
graph = workflow.compile()

def create_initial_state(profile_id: str = "profile1") -> ConversationState:
    """Create initial conversation state with user preferences loaded"""
    user_prefs = load_user_preferences(profile_id)
    
    return ConversationState(
        user_preferences=user_prefs,
        conversation_history=[],
        conversation_context=ConversationContext(
            occasion=None,
            age_group=None,
            quantity_needed=None,
            specific_needs=[],
            clarifications_needed=[]
        ),
        current_message="",
        assistant_response="",
        product_recommendations=[],
        conversation_complete=False
    )
