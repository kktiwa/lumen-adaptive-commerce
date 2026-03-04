"""LangGraph workflow for multi-turn conversations"""
from typing import TypedDict, List, Optional
from datetime import datetime
import re
import json
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

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
    """Extract and accumulate conversation context using LLM for semantic understanding"""
    
    # Build conversation history for context
    history_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in state["conversation_history"][-10:]  # Last 10 messages for better context
    ])
    
    # Include previously extracted context in the prompt to maintain continuity
    previous_context_str = f"""
    Previously extracted:
    - Occasion: {state['conversation_context'].get('occasion') or 'not mentioned'}
    - Age Group: {state['conversation_context'].get('age_group') or 'not mentioned'}
    - Quantity: {state['conversation_context'].get('quantity_needed') or 'not mentioned'}
    - Specific Needs: {', '.join(state['conversation_context'].get('specific_needs', [])) or 'none mentioned'}
    """
    
    # Create extraction prompt
    extraction_prompt = f"""
    Based on the user's messages and conversation history, extract and ACCUMULATE information.
    Only update fields where NEW information is mentioned. Keep previously extracted information.
    
    {previous_context_str}
    
    Current conversation:
    {history_text}
    Current user message: {state['current_message']}
    
    Extract and return as JSON:
    {{
        "occasion": "what is the user looking to do/celebrate? Keep previous if not mentioned in current message",
        "age_group": "age of the target child/children? Keep previous if not mentioned",
        "quantity_needed": "how many people or items? Keep previous if not mentioned",
        "specific_needs": ["list of requirements mentioned - ADD to any previously mentioned, don't replace"],
        "clarifications_needed": ["list of questions we still need to ask, or empty if we have enough info"]
    }}
    
    Return ONLY valid JSON, no other text.
    """
    
    try:
        response = llm.invoke([
            {"role": "system", "content": "You are an expert at understanding customer needs. Extract structured information and accumulate context across conversation turns. Return valid JSON only."},
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
        
        # Update context - merge new info with existing
        context = state["conversation_context"]
        
        # Only update if new info provided (not "not mentioned" or None)
        occasion = context_data.get("occasion")
        if occasion and isinstance(occasion, str) and "not mentioned" not in occasion.lower():
            context["occasion"] = occasion
        
        age_group = context_data.get("age_group")
        if age_group and isinstance(age_group, str) and "not mentioned" not in age_group.lower():
            context["age_group"] = age_group
        
        quantity = context_data.get("quantity_needed")
        if quantity:
            context["quantity_needed"] = quantity
        
        # Merge specific needs (add new, keep old)
        new_needs = context_data.get("specific_needs", [])
        if new_needs:
            # Add only new needs that aren't already there
            existing_needs = context.get("specific_needs", [])
            for need in new_needs:
                if need and isinstance(need, str) and need.lower() not in [n.lower() for n in existing_needs]:
                    existing_needs.append(need)
            context["specific_needs"] = existing_needs
        
        context["clarifications_needed"] = context_data.get("clarifications_needed", [])
        
        state["conversation_context"] = context
        
    except json.JSONDecodeError as e:
        # If JSON parsing fails, continue with existing context
        print(f"Error parsing context extraction: {e}")
    
    return state

def generate_response(state: ConversationState) -> ConversationState:
    """Generate assistant response based on conversation state with context awareness"""
    
    # Build conversation history for context
    history_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in state["conversation_history"][-5:]  # Last 5 messages for context window
    ])
    
    # Get system prompt with full context including extracted conversation data
    system_msg = get_system_prompt(
        budget=state["user_preferences"]["budget"],
        interests=state["user_preferences"]["interests"],
        preferences=state["user_preferences"]["preferences"],
        occasion=state["conversation_context"].get("occasion"),
        age_group=state["conversation_context"].get("age_group"),
        quantity_needed=state["conversation_context"].get("quantity_needed"),
        specific_needs=state["conversation_context"].get("specific_needs", []),
        clarifications_needed=state["conversation_context"].get("clarifications_needed", []),
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
    
    # Check if we have enough context AND LLM says ready to recommend
    if "[READY_TO_RECOMMEND]" in response.content:
        # Validate we have sufficient context before setting conversation_complete
        has_sufficient_context = (
            state["conversation_context"].get("occasion") and
            state["conversation_context"].get("age_group") and
            len(state["conversation_context"].get("specific_needs", [])) > 0
        )
        
        if has_sufficient_context:
            state["conversation_complete"] = True
            state["assistant_response"] = state["assistant_response"].replace("[READY_TO_RECOMMEND]", "").strip()
    
    return state

def get_recommendations(state: ConversationState) -> ConversationState:
    """Get product recommendations using semantic search with rich context"""
    
    if not state["conversation_complete"]:
        return state
    
    # Only generate recommendations once - if already generated, skip
    if state.get("product_recommendations"):
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
    
    # Build comprehensive semantic search query from all available context
    search_query_parts = []
    
    # Include occasion with descriptive language
    if context.get("occasion"):
        search_query_parts.append(f"for {context['occasion']}")
    
    # Include age group information
    if context.get("age_group"):
        search_query_parts.append(f"for children {context['age_group']}")
    
    # Include specific needs with all accumulated requirements
    specific_needs = context.get("specific_needs", [])
    if specific_needs:
        needs_str = " and ".join(specific_needs)
        search_query_parts.append(f"that are {needs_str}")
    
    # Include quantity if specified
    if context.get("quantity_needed"):
        qty = context.get("quantity_needed")
        if qty == 1:
            search_query_parts.append("single item")
        else:
            search_query_parts.append(f"suitable for {qty} people")
    
    # Build the comprehensive search query
    if search_query_parts:
        search_query = "Product " + " ".join(search_query_parts)
    else:
        search_query = "Product for children"
    
    # Extract age range for metadata filter
    age_range = None
    if context.get("age_group"):
        age_group_str = context["age_group"]
        # Parse age range from string like "5-7 years" or "5-7"
        import re
        match = re.search(r'(\d+)-(\d+)', age_group_str)
        if match:
            age_range = context["age_group"]
    
    # Search using similarity search with all context
    products = db.similarity_search(
        query=search_query,
        max_price=max_price,
        age_range=age_range,
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
