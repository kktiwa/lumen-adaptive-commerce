"""Type definitions for autonomous agentic workflow"""
from typing import TypedDict, List, Optional, Any, Dict
from datetime import datetime
from enum import Enum


class AgentActionType(str, Enum):
    """Types of actions the agent can take"""
    GATHER_INFO = "gather_info"
    RECOMMEND_PRODUCT = "recommend_product"
    SUMMARIZE_RECOMMENDATION = "summarize_recommendation"
    GET_SHIPPING_ADDRESS = "get_shipping_address"
    OFFER_SHIPPING_ALTERNATIVES = "offer_shipping_alternatives"
    GET_PAYMENT_METHOD = "get_payment_method"
    OFFER_PAYMENT_ALTERNATIVES = "offer_payment_alternatives"
    PROCESS_PAYMENT = "process_payment"
    COMPLETE_ORDER = "complete_order"
    SEND_ORDER_EMAIL = "send_order_email"
    CONTINUE_CONVERSATION = "continue_conversation"


class OrderStatus(str, Enum):
    """Order status tracking"""
    PENDING = "pending"
    PAYMENT_PROCESSING = "payment_processing"
    PAYMENT_COMPLETED = "payment_completed"
    COMPLETED = "completed"
    FAILED = "failed"


class ShippingAddress(TypedDict):
    """Shipping address information"""
    id: str
    name: str
    street: str
    city: str
    state: str
    zip_code: str
    country: str
    is_default: bool


class PaymentMethod(TypedDict):
    """Payment method information"""
    id: str
    type: str  # "credit_card", "debit_card", "paypal", etc.
    last_four: str
    cardholder_name: Optional[str]
    expiry_date: Optional[str]
    is_default: bool


class Product(TypedDict):
    """Product information"""
    id: str
    name: str
    category: str
    price: float
    age_range: Optional[str]
    occasion: List[str]
    features: List[str]
    description: str
    educational: bool
    eco_friendly: bool


class OrderItem(TypedDict):
    """Item in an order"""
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float


class Order(TypedDict):
    """Order information"""
    id: str
    user_id: str
    items: List[OrderItem]
    total_amount: float
    status: OrderStatus
    shipping_address: ShippingAddress
    payment_method: PaymentMethod
    created_at: datetime
    completed_at: Optional[datetime]


class UserProfile(TypedDict):
    """User profile with preferences"""
    user_id: str
    name: str
    email: str
    shipping_addresses: List[ShippingAddress]
    payment_methods: List[PaymentMethod]
    preferences: Dict[str, Any]


class AgentStep(TypedDict):
    """A single step in the agent's reasoning"""
    action: AgentActionType
    reasoning: str
    parameters: Dict[str, Any]
    timestamp: datetime


class ConversationMessage(TypedDict):
    """Message in conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime


class ConversationContext(TypedDict):
    """Context extracted from conversation"""
    occasion: Optional[str]
    age_group: Optional[str]
    budget_range: Optional[str]
    quantity_needed: Optional[int]
    specific_needs: List[str]
    preferred_features: List[str]


class AgenticState(TypedDict):
    """Complete state for the autonomous agentic workflow - LangGraph state"""
    # User and conversation info
    user_profile: Optional[UserProfile]
    conversation_history: List[ConversationMessage]
    conversation_context: ConversationContext
    current_message: str
    
    # Agent reasoning and actions
    agent_steps: List[AgentStep]
    agent_reasoning: str
    next_action: AgentActionType
    
    # Product recommendation tracking
    product_recommendations: List[Product]
    selected_product: Optional[Product]
    confirmation_pending: bool
    
    # Order information
    current_order: Optional[Order]
    
    # Shipping and payment
    default_shipping_address: Optional[ShippingAddress]
    alternate_shipping_addresses: List[ShippingAddress]
    selected_shipping_address: Optional[ShippingAddress]
    
    default_payment_method: Optional[PaymentMethod]
    alternate_payment_methods: List[PaymentMethod]
    selected_payment_method: Optional[PaymentMethod]
    
    # Order completion tracking
    payment_successful: bool
    payment_error: Optional[str]
    order_completed: bool
    email_sent: bool
    
    # Agent response
    assistant_response: str
    
    # Flow control
    workflow_complete: bool
    user_confirmed: bool
