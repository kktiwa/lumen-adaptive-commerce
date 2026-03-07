"""Autonomous agentic workflow using LangGraph with agent loop"""
from typing import Optional, Dict, Any
from datetime import datetime
import json
import logging

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from common.config import settings, initialize_arize_tracing
from .agentic_types import (
    AgenticState,
    AgentActionType,
    ConversationMessage,
    ConversationContext,
    OrderStatus,
)
from .agentic_prompts import (
    get_system_prompt,
    get_initial_greeting,
    get_recommendation_prompt,
    get_product_recommendation_message,
    get_order_summary_prompt,
    get_payment_alternatives_prompt,
    get_payment_success_prompt,
    get_payment_failure_prompt,
)
from .user_management import UserManager
from .order_management import OrderManager
from .payment_processor import PaymentProcessor
from .email_service import EmailService
from .product_database import get_product_by_id

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
initialize_arize_tracing(settings)
user_manager = UserManager()
order_manager = OrderManager()
payment_processor = PaymentProcessor()
email_service = EmailService()

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.openai_api_key,
    temperature=0.7,
)


def initialize_state() -> AgenticState:
    """Initialize a new agentic state for a conversation"""
    return {
        "user_profile": None,
        "conversation_history": [],
        "conversation_context": {
            "occasion": None,
            "category": None,
            "age_group": None,
            "budget_range": None,
            "quantity_needed": None,
            "specific_needs": [],
            "preferred_features": [],
        },
        "current_message": "",
        "agent_steps": [],
        "agent_reasoning": "",
        "next_action": AgentActionType.GATHER_INFO,
        "product_recommendations": [],
        "selected_product": None,
        "confirmation_pending": False,
        "current_order": None,
        "default_shipping_address": None,
        "alternate_shipping_addresses": [],
        "selected_shipping_address": None,
        "default_payment_method": None,
        "alternate_payment_methods": [],
        "selected_payment_method": None,
        "payment_successful": False,
        "payment_error": None,
        "order_completed": False,
        "email_sent": False,
        "assistant_response": "",
        "workflow_complete": False,
        "user_confirmed": False,
    }


def process_user_input(state: AgenticState) -> AgenticState:
    """Process the user's input message"""
    message = state["current_message"]
    
    user_msg: ConversationMessage = {
        "role": "user",
        "content": message,
        "timestamp": datetime.now(),
    }
    state["conversation_history"].append(user_msg)
    
    logger.info(f"User message: {message}")
    return state


def extract_context_from_conversation(state: AgenticState) -> AgenticState:
    """Extract context from conversation using LLM"""
    
    # Build conversation history for analysis
    history_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in state["conversation_history"][-10:]
    ])
    
    context_extraction_prompt = f"""Analyze this conversation and extract the following information:
- Occasion (e.g., birthday, gift, party)
- Category (e.g., toys, costumes, educational)
- Age group (e.g., 5-8, 8-10, 5-12)
- Budget range (e.g., under $50, $50-100, $100+)
- Quantity needed
- Specific needs (list)
- Preferred features (list)

Conversation:
{history_text}

Current extracted context:
- Occasion: {state['conversation_context'].get('occasion')}
- Category: {state['conversation_context'].get('category')}
- Age Group: {state['conversation_context'].get('age_group')}
- Budget Range: {state['conversation_context'].get('budget_range')}
- Quantity: {state['conversation_context'].get('quantity_needed')}
- Specific Needs: {state['conversation_context'].get('specific_needs')}
- Preferred Features: {state['conversation_context'].get('preferred_features')}

Update this context based on the latest messages. Return only the updated values as JSON."""
    
    response = llm.invoke([
        SystemMessage(content="You are an expert at extracting shopping context from conversations. Return only valid JSON."),
        HumanMessage(content=context_extraction_prompt),
    ])
    
    try:
        # Extract JSON from response
        response_text = response.content
        # Find JSON in response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            extracted = json.loads(json_str)
            
            # Update context
            if "occasion" in extracted and extracted["occasion"]:
                state["conversation_context"]["occasion"] = extracted["occasion"]
            if "category" in extracted and extracted["category"]:
                state["conversation_context"]["category"] = extracted["category"]
            if "age_group" in extracted and extracted["age_group"]:
                state["conversation_context"]["age_group"] = extracted["age_group"]
            if "budget_range" in extracted and extracted["budget_range"]:
                state["conversation_context"]["budget_range"] = extracted["budget_range"]
            if "quantity_needed" in extracted and extracted["quantity_needed"]:
                state["conversation_context"]["quantity_needed"] = extracted["quantity_needed"]
            if "specific_needs" in extracted and extracted["specific_needs"]:
                state["conversation_context"]["specific_needs"] = extracted["specific_needs"]
            if "preferred_features" in extracted and extracted["preferred_features"]:
                state["conversation_context"]["preferred_features"] = extracted["preferred_features"]
    except json.JSONDecodeError:
        logger.warning("Failed to parse context extraction response")
    
    return state


def agent_reasoning(state: AgenticState) -> AgenticState:
    """Agent reasoning step to decide what action to take"""
    
    # Build the reasoning prompt for tracing/logging
    reasoning_prompt = get_recommendation_prompt(
        state["conversation_context"],
        state["conversation_history"],
    )
    
    response = llm.invoke([
        SystemMessage(content=get_system_prompt()),
        HumanMessage(content=reasoning_prompt),
    ])
    
    agent_response = response.content
    state["agent_reasoning"] = agent_response
    
    # Determine next action based on STATE, not LLM response text
    # This ensures deterministic, predictable state transitions
    
    # 1. If no product selected yet, check if we should search for products
    if not state["selected_product"]:
        # Check if we have enough context to search
        has_occasion = state["conversation_context"].get("occasion")
        has_category = state["conversation_context"].get("category")
        has_age = state["conversation_context"].get("age_group")
        has_budget = state["conversation_context"].get("budget_range")
        
        # Allow either an occasion OR a category to be sufficient along with age and budget
        if (has_occasion or has_category) and has_age and has_budget:
            # We have enough context to search for products
            state["next_action"] = AgentActionType.RECOMMEND_PRODUCT
            logger.info("Agent: Have enough context, moving to product recommendation")
        else:
            # Still need more information from user
            state["next_action"] = AgentActionType.CONTINUE_CONVERSATION
            logger.info("Agent: Need more context, continuing conversation")
    
    # 2. If product selected but not yet summarized for checkout, show summary
    elif state["selected_product"] and not state["confirmation_pending"]:
        state["next_action"] = AgentActionType.SUMMARIZE_RECOMMENDATION
        logger.info("Agent: Product selected, moving to order summary")
    
    # 3. If order created and waiting for payment confirmation, process payment
    elif state["current_order"] and state["confirmation_pending"]:
        state["next_action"] = AgentActionType.PROCESS_PAYMENT
        logger.info("Agent: Order ready, processing payment")
    
    # 4. Default: continue conversation
    else:
        state["next_action"] = AgentActionType.CONTINUE_CONVERSATION
        logger.info("Agent: Continuing conversation")
    
    return state


def gather_information(state: AgenticState) -> AgenticState:
    """Agent gathers more information if needed"""
    
    history_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in state["conversation_history"][-8:]
    ])
    
    info_gathering_prompt = f"""Based on this conversation, we need to find the right product. 

Current context:
- Occasion: {state['conversation_context'].get('occasion') or 'Unknown'}
- Age Group: {state['conversation_context'].get('age_group') or 'Unknown'}
- Budget: {state['conversation_context'].get('budget_range') or 'Unknown'}
- Needs: {state['conversation_context'].get('specific_needs') or ['Not fully specified']}

Recent conversation:
{history_text}

If we're still missing key information, ask clarifying questions about:
- What's the occasion? (birthday, holiday, gift, etc.)
- What age group? (specific age or age range)
- What's the budget? (rough range is fine)
- Any specific needs or preferences?

Be conversational and helpful. Don't rush - ask one or two clarifying questions at a time."""
    
    response = llm.invoke([
        SystemMessage(content=get_system_prompt()),
        HumanMessage(content=info_gathering_prompt),
    ])
    
    state["assistant_response"] = response.content
    logger.info("Gathering information from user")
    return state


def recommend_product(state: AgenticState) -> AgenticState:
    """Recommend products based on extracted context"""
    
    from .tools import search_products_by_criteria
    from .vector_search import semantic_product_search, initialize_product_embeddings
    from .product_database import get_product_db, initialize_vector_search
    
    # Ensure vector search is initialized
    initialize_vector_search()
    
    # Build parameters for product search
    budget = None
    if state["conversation_context"].get("budget_range"):
        budget_str = state["conversation_context"]["budget_range"]
        if "$50-100" in budget_str:
            budget = 100
        elif "$100+" in budget_str:
            budget = 500
        elif "under $50" in budget_str:
            budget = 50
    
    # Build a semantic query from all available context
    query_parts = []
    if state["conversation_context"].get("occasion"):
        query_parts.append(state["conversation_context"]["occasion"])
    if state["conversation_context"].get("category"):
        query_parts.append(state["conversation_context"]["category"])
    if state["conversation_context"].get("specific_needs"):
        query_parts.extend(state["conversation_context"]["specific_needs"])
    if state["conversation_context"].get("preferred_features"):
        query_parts.extend(state["conversation_context"]["preferred_features"])
    
    # Build semantic query
    semantic_query = " ".join(filter(None, query_parts)) if query_parts else "toys for kids"
    
    logger.info(f"Searching for products with semantic query: {semantic_query}")
    
    # Use semantic search directly for better matching
    products = semantic_product_search(
        query=semantic_query,
        top_k=10,
        budget_max=budget,
        age_group=state["conversation_context"].get("age_group"),
        educational=None,  # Let semantic search determine
        eco_friendly=None,  # Let semantic search determine
    )
    
    state["product_recommendations"] = products
    
    if products:
        # Select the first/best recommendation (highest semantic similarity)
        recommended_product = products[0]
        state["selected_product"] = recommended_product
        state["assistant_response"] = get_product_recommendation_message(recommended_product)
        # Move directly to summarization so we can create the order in the same workflow run
        state["next_action"] = AgentActionType.SUMMARIZE_RECOMMENDATION
    else:
        state["assistant_response"] = "I didn't find products matching your criteria. Could you tell me more about what you're looking for?"
        state["next_action"] = AgentActionType.GATHER_INFO
    
    logger.info(f"Found {len(products)} product recommendations")
    return state


def summarize_recommendation(state: AgenticState) -> AgenticState:
    """Summarize the selected product and prepare for checkout"""
    
    if not state["selected_product"]:
        state["assistant_response"] = "Let me help you find a product first."
        state["next_action"] = AgentActionType.RECOMMEND_PRODUCT
        return state
    
    # If user hasn't been assigned a profile yet, use demo user
    if not state["user_profile"]:
        state["user_profile"] = user_manager.get_user("user_001")
    
    # Get user's addresses and payment methods
    if state["user_profile"]:
        default_addr = user_manager.get_default_shipping_address(state["user_profile"]["user_id"])
        default_pm = user_manager.get_default_payment_method(state["user_profile"]["user_id"])
        state["default_shipping_address"] = default_addr
        state["default_payment_method"] = default_pm
        state["alternate_shipping_addresses"] = user_manager.get_alternate_shipping_addresses(
            state["user_profile"]["user_id"]
        )
        state["alternate_payment_methods"] = user_manager.get_alternate_payment_methods(
            state["user_profile"]["user_id"]
        )
    
    # Create order
    if state["default_shipping_address"] and state["default_payment_method"]:
        order = order_manager.create_order(
            user_id=state["user_profile"]["user_id"],
            product=state["selected_product"],
            quantity=state["conversation_context"].get("quantity_needed", 1),
            shipping_address=state["default_shipping_address"],
            payment_method=state["default_payment_method"],
        )
        state["current_order"] = order
        state["confirmation_pending"] = True
        
        # Build summary message
        summary = get_order_summary_prompt(order, state["user_profile"]["name"])
        
        if state["alternate_shipping_addresses"] or state["alternate_payment_methods"]:
            summary += "\n\n" + get_payment_alternatives_prompt(
                state["user_profile"]["name"],
                state["alternate_shipping_addresses"],
                state["alternate_payment_methods"],
            )
        
        state["assistant_response"] = summary
    
    state["next_action"] = AgentActionType.CONTINUE_CONVERSATION
    logger.info("Order summarized and ready for checkout")
    return state


def process_payment(state: AgenticState) -> AgenticState:
    """Process payment for the order"""
    
    if not state["current_order"]:
        state["assistant_response"] = "No order to process. Let me help you create one."
        state["next_action"] = AgentActionType.RECOMMEND_PRODUCT
        return state
    
    # Update order status
    order_manager.update_order_status(state["current_order"]["id"], OrderStatus.PAYMENT_PROCESSING)
    
    # Process payment
    success, message, transaction_id = payment_processor.process_payment(state["current_order"])
    
    state["payment_successful"] = success
    
    if success:
        state["assistant_response"] = get_payment_success_prompt(transaction_id)
        state["next_action"] = AgentActionType.COMPLETE_ORDER
        order_manager.update_order_status(state["current_order"]["id"], OrderStatus.PAYMENT_COMPLETED)
    else:
        state["payment_error"] = message
        state["assistant_response"] = get_payment_failure_prompt(message)
        state["next_action"] = AgentActionType.CONTINUE_CONVERSATION
    
    logger.info(f"Payment processed - Success: {success}")
    return state


def complete_order(state: AgenticState) -> AgenticState:
    """Complete the order after successful payment"""
    
    if not state["current_order"] or not state["payment_successful"]:
        state["assistant_response"] = "Order completion failed. Please try again."
        state["next_action"] = AgentActionType.CONTINUE_CONVERSATION
        return state
    
    # Update order status to completed
    order_manager.update_order_status(state["current_order"]["id"], OrderStatus.COMPLETED)
    state["order_completed"] = True
    
    # Send confirmation email
    state["next_action"] = AgentActionType.SEND_ORDER_EMAIL
    logger.info(f"Order {state['current_order']['id']} completed successfully")
    
    return state


def send_order_email(state: AgenticState) -> AgenticState:
    """Send order confirmation email"""
    
    if not state["current_order"] or not state["user_profile"]:
        logger.warning("Cannot send email - order or user profile missing")
        state["next_action"] = AgentActionType.CONTINUE_CONVERSATION
        return state
    
    success, email_message = email_service.send_order_confirmation_email(
        state["user_profile"],
        state["current_order"],
    )
    
    state["email_sent"] = success
    
    if success:
        state["assistant_response"] += f"\n\n{email_message}"
    
    state["workflow_complete"] = True
    logger.info("Order confirmation email sent")
    
    return state


def build_agentic_workflow() -> StateGraph:
    """Build the LangGraph workflow for autonomous agentic shopping"""
    
    workflow = StateGraph(AgenticState)
    
    # Add nodes
    workflow.add_node("process_input", process_user_input)
    workflow.add_node("extract_context", extract_context_from_conversation)
    workflow.add_node("agent_reasoning", agent_reasoning)
    workflow.add_node("gather_information", gather_information)
    workflow.add_node("recommend_product", recommend_product)
    workflow.add_node("summarize_recommendation", summarize_recommendation)
    workflow.add_node("process_payment", process_payment)
    workflow.add_node("complete_order", complete_order)
    workflow.add_node("send_order_email", send_order_email)
    
    # Add edges
    workflow.set_entry_point("process_input")
    
    workflow.add_edge("process_input", "extract_context")
    workflow.add_edge("extract_context", "agent_reasoning")
    
    # Conditional routing from agent reasoning
    def route_after_reasoning(state: AgenticState):
        if state["next_action"] == AgentActionType.CONTINUE_CONVERSATION:
            return "gather_information"
        elif state["next_action"] == AgentActionType.RECOMMEND_PRODUCT:
            return "recommend_product"
        elif state["next_action"] == AgentActionType.SUMMARIZE_RECOMMENDATION:
            return "summarize_recommendation"
        elif state["next_action"] == AgentActionType.PROCESS_PAYMENT:
            return "process_payment"
        else:
            return "gather_information"
    
    workflow.add_conditional_edges("agent_reasoning", route_after_reasoning)
    
    workflow.add_edge("gather_information", END)
    workflow.add_edge("recommend_product", "summarize_recommendation")
    workflow.add_edge("summarize_recommendation", END)
    
    # Payment flow
    def route_after_payment(state: AgenticState):
        if state["payment_successful"]:
            return "complete_order"
        else:
            return END
    
    workflow.add_conditional_edges("process_payment", route_after_payment)
    
    workflow.add_edge("complete_order", "send_order_email")
    workflow.add_edge("send_order_email", END)
    
    return workflow


async def process_message(state: AgenticState, user_message: str) -> AgenticState:
    """Process a user message through the workflow"""
    state["current_message"] = user_message
    
    # Build and execute the workflow
    workflow = build_agentic_workflow()
    compiled_workflow = workflow.compile()
    
    # Execute the workflow
    result_state = compiled_workflow.invoke(state)
    
    return result_state
