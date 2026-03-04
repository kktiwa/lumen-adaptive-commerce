"""LangGraph workflow for multi-turn conversations"""
from typing import TypedDict, List, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
import json

from common.config import settings, initialize_arize_tracing
from .conversation_types import ConversationState, ConversationMessage, ConversationContext
from .user_preferences import load_user_preferences
from .chat_prompts import get_system_prompt, get_recommendation_prompt
from .product_database import get_product_db

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
    """Extract conversation context using LLM for semantic understanding"""
    
    # Build conversation history for context
    history_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in state["conversation_history"][-5:]  # Last 5 messages
    ])
    
    # Create extraction prompt
    extraction_prompt = f"""
    Based on the user's message and conversation history, extract the following information:
    
    Conversation:
    {history_text}
    Current message: {state['current_message']}
    
    Extract and return as JSON:
    {{
        "occasion": "what is the user looking to do/celebrate? (e.g., 'birthday party', 'camping trip', 'lazy afternoon', 'outdoor adventure')",
        "age_group": "what is the age of the target child/children? (e.g., '5-7 years', '8-10 years', 'mixed ages 5-12')",
        "quantity_needed": "how many people or items? (integer or null if not specified)",
        "specific_needs": ["list of specific requirements mentioned (e.g., 'educational', 'eco-friendly', 'budget-friendly']"],
        "clarifications_needed": ["list of questions we still need to ask to narrow down, or empty list if we have enough info"]
    }}
    
    Return ONLY valid JSON, no other text.
    """
    
    try:
        response = llm.invoke([
            {"role": "system", "content": "You are an expert at understanding customer needs from natural language. Extract structured information and return valid JSON."},
            {"role": "user", "content": extraction_prompt}
        ])
        
        # Parse the response
        response_text = response.content.strip()
        # Clean up markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        context_data = json.loads(response_text)
        
        # Update context
        context = state["conversation_context"]
        context["occasion"] = context_data.get("occasion")
        context["age_group"] = context_data.get("age_group")
        context["quantity_needed"] = context_data.get("quantity_needed")
        context["specific_needs"] = context_data.get("specific_needs", [])
        context["clarifications_needed"] = context_data.get("clarifications_needed", [])
        
        state["conversation_context"] = context
        
    except json.JSONDecodeError as e:
        # If JSON parsing fails, continue with existing context
        print(f"Error parsing context extraction: {e}")
    
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
    """Get product recommendations using semantic search"""
    
    if not state["conversation_complete"]:
        return state
    
    context = state["conversation_context"]
    db = get_product_db()
    
    # Extract max price from budget
    budget = state["user_preferences"]["budget"]
    max_price_map = {
        "$0-50": 50,
        "$50-100": 100,
        "$100-200": 200,
        "$200+": 500
    }
    max_price = max_price_map.get(budget, 100)
    
    # Build semantic search query from context
    search_query_parts = []
    
    if context.get("occasion"):
        search_query_parts.append(f"for {context['occasion']}")
    
    if context.get("age_group"):
        search_query_parts.append(f"for children {context['age_group']}")
    
    if context.get("specific_needs"):
        needs = context.get("specific_needs", [])
        if needs:
            search_query_parts.append(f"that are {', '.join(needs)}")
    
    # Build the semantic search query
    search_query = "Product " + " ".join(search_query_parts) if search_query_parts else "Product for children"
    
    # Search using similarity search
    products = db.similarity_search(
        query=search_query,
        max_price=max_price,
        educational=state["user_preferences"]["preferences"].get("educational", True),
        eco_friendly=state["user_preferences"]["preferences"].get("eco_friendly", False),
        top_k=4
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
