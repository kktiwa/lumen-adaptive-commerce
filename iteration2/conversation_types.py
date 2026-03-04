from typing import TypedDict, List, Optional
from datetime import datetime

class UserPreferences(TypedDict):
    """User preferences that persist across conversations"""
    budget: str  # e.g., "$0-50", "$50-100", "$100-200", "$200+"
    interests: List[str]  # e.g., ["sports", "arts", "outdoor activities"]
    preferences: dict  # Any additional preferences

class ConversationContext(TypedDict):
    """Context for understanding the current request"""
    occasion: Optional[str]  # e.g., "birthday party", "camping trip"
    age_group: Optional[str]  # e.g., "5-7 years old", "8-10 years old"
    quantity_needed: Optional[int]  # number of items/people
    specific_needs: List[str]  # e.g., ["outdoor", "educational", "under $20"]
    clarifications_needed: List[str]  # Questions we still need to ask

class ConversationMessage(TypedDict):
    """Individual message in the conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime

class ConversationState(TypedDict):
    """Complete conversation state in LangGraph"""
    user_preferences: UserPreferences
    conversation_history: List[ConversationMessage]
    conversation_context: ConversationContext
    current_message: str
    assistant_response: str
    product_recommendations: List[dict]
    conversation_complete: bool
