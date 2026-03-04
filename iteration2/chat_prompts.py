"""Prompts for the conversational agent"""
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

# System prompt for the conversational agent
SYSTEM_PROMPT = """You are a helpful shopping assistant for a children's product store.

Your goal is to help customers find the perfect products by understanding their needs through conversation.

IMPORTANT INSTRUCTIONS:
1. You have access to the customer's existing preferences (budget, interests)
2. Be conversational and friendly - this is a chat, not a questionnaire
3. Ask ONE clarifying question at a time if you need more information
4. CRITICAL: Never ask for information you already know - check the "ALREADY EXTRACTED" section below
5. Once you have enough context to understand the customer's needs, end your response with [READY_TO_RECOMMEND]

USER PROFILE:
- Budget: {budget}
- Interests: {interests}
- Preferences: {preferences}

ALREADY EXTRACTED FROM CONVERSATION:
- Occasion: {occasion}
- Age Group: {age_group}
- Quantity Needed: {quantity_needed}
- Specific Needs: {specific_needs}
- Still Need Info About: {clarifications_needed}

RECENT CONVERSATION:
{history}

When you understand enough about what the customer needs, end your response with:
[READY_TO_RECOMMEND]"""

# Prompt template for context extraction
CONTEXT_EXTRACTION_PROMPT = """Extract the following information from the conversation:

Conversation:
{conversation}

Extract:
1. Occasion (e.g., birthday party, camping trip, rainy day activity)
2. Age Group (e.g., "5-7 years old")
3. Quantity Needed (number of items or people)
4. Specific Needs (list of requirements, constraints)
5. What other clarifications are needed?

Return as JSON."""

# Prompt template for product recommendations
RECOMMENDATION_PROMPT = """Based on the customer's needs, recommend the best products.

Customer Profile:
- Budget: {budget}
- Interests: {interests}
- Preferences: {preferences}

Customer's Specific Needs:
{context}

Available Products:
{products}

Provide 3-5 product recommendations with brief explanations about why each product is suitable.
Include price and key features."""

def get_system_prompt(
    budget: str, 
    interests: list, 
    preferences: dict, 
    occasion: str = None,
    age_group: str = None,
    quantity_needed: int = None,
    specific_needs: list = None,
    clarifications_needed: list = None,
    history: str = ""
) -> str:
    """Generate the system prompt with user context and extracted conversation data"""
    interests_str = ", ".join(interests) if interests else "not specified"
    prefs_str = str(preferences) if preferences else "default"
    occasion_str = occasion or "not yet discussed"
    age_group_str = age_group or "not yet specified"
    quantity_str = str(quantity_needed) if quantity_needed else "not specified"
    needs_str = ", ".join(specific_needs) if specific_needs else "none specified yet"
    clarifications_str = ", ".join(clarifications_needed) if clarifications_needed else "none identified yet"
    
    return SYSTEM_PROMPT.format(
        budget=budget,
        interests=interests_str,
        preferences=prefs_str,
        occasion=occasion_str,
        age_group=age_group_str,
        quantity_needed=quantity_str,
        specific_needs=needs_str,
        clarifications_needed=clarifications_str,
        history=history or "No previous messages"
    )

def get_recommendation_prompt(
    budget: str,
    interests: list,
    preferences: dict,
    context: str,
    products: str
) -> str:
    """Generate the recommendation prompt"""
    interests_str = ", ".join(interests) if interests else "not specified"
    prefs_str = str(preferences) if preferences else "default"
    
    return RECOMMENDATION_PROMPT.format(
        budget=budget,
        interests=interests_str,
        preferences=prefs_str,
        context=context,
        products=products
    )
