# Iteration 3: Autonomous Agentic E-Commerce Application

## Overview

Iteration 3 implements a fully autonomous agentic application that guides customers through an end-to-end shopping experience using an AI agent powered by LLMs and LangGraph. The agent converses naturally with customers, understands their needs, recommends products, handles checkout, processes payments, and sends order confirmations.

## Architecture

### Core Components

```
iteration3/
├── agentic_types.py              # Type definitions for agentic state & entities
├── user_management.py            # User profiles, addresses, payment methods
├── order_management.py           # Order creation and tracking
├── payment_processor.py          # Payment processing (mock)
├── email_service.py              # Order confirmation emails
├── product_database.py           # Product catalog
├── tools.py                      # Agent tools/actions
├── agentic_prompts.py           # System prompts & message formatting
├── agentic_workflow.py          # LangGraph workflow (core logic)
├── agentic_ui.py                # Gradio UI
└── app.py                       # Entry point
```

### Workflow Flow

The autonomous agent operates in a state machine with the following path:

```
1. Process User Input
   └─> Extract Context from Conversation
       └─> Agent Reasoning (decide next action)
           ├─> Gather Information (if needs clarification)
           │   └─> Continue conversation
           ├─> Recommend Product (if have enough context)
           │   └─> Display recommendation
           ├─> Summarize Recommendation (if product selected)
           │   ├─> Create order
           │   └─> Display order with alternatives
           └─> Process Payment (if user confirmed)
               ├─> SUCCESS → Complete Order → Send Email
               └─> FAILED → Show error, ask retry
```

### Key Design Patterns

#### 1. **State Management with LangGraph**
- Centralized `AgenticState` TypedDict manages all conversation and order data
- Each workflow node is a pure function that transforms state
- Stateless design enables easy debugging and testing

#### 2. **Service Layer Architecture**
- **UserManager**: Handles user profiles, shipping addresses, payment methods
- **OrderManager**: Creates and tracks orders with pricing calculations
- **PaymentProcessor**: Processes payments with transaction logging
- **EmailService**: Sends confirmations and shipping notifications

#### 3. **LLM-driven Agent Reasoning**
- Multi-step reasoning process with conversation context extraction
- Agent decides which action to take based on conversation progress
- Natural language prompts guide the LLM's decision-making

#### 4. **Tool-based Product Discovery**
- LangChain tools for searching, comparing, and retrieving products
- Agent can invoke tools during reasoning (though not in this simplified version)
- Extensible for semantic search with embeddings

## Type System

### Core Types

```python
AgenticState(TypedDict):
    # Conversation & User
    user_profile: Optional[UserProfile]
    conversation_history: List[ConversationMessage]
    conversation_context: ConversationContext
    
    # Agent State
    agent_steps: List[AgentStep]
    next_action: AgentActionType
    
    # Order Processing
    selected_product: Optional[Product]
    current_order: Optional[Order]
    payment_successful: bool
    order_completed: bool
    email_sent: bool
```

## Features

### 1. **Natural Conversation Flow**
- Agent asks clarifying questions about occasion, age group, budget, needs
- Extracts context incrementally from multi-turn conversations
- Personalized recommendations based on extracted context

### 2. **Product Recommendation**
- Searches product database by multiple criteria
- Supports filtering by price, age range, occasion, educational value, eco-friendliness
- Explains why each product is a good match

### 3. **Intelligent Checkout**
- Shows default shipping address and payment method
- Offers alternatives if multiple are saved
- Requires explicit user confirmation before payment

### 4. **Payment Processing**
- Mock payment processor with realistic success/failure simulation
- Transaction logging for auditing
- Error handling and user-friendly error messages
- Refund support (for future implementation)

### 5. **Order Management**
- Automatic order creation with calculated totals (subtotal + tax + shipping)
- Order status tracking (pending → processing → completed)
- Order summaries with all details

### 6. **Email Notifications**
- Automated order confirmation emails
- Shipping notifications (can be sent after shipment)
- Mock email service with logging

## Best Practices Implemented

### 1. **Separation of Concerns**
- Each module has single responsibility
- Clear interfaces between components
- Easy to test and extend

### 2. **Type Safety**
- Full TypedDict usage for all data structures
- Type hints on all functions
- Prevents runtime errors from data mismatches

### 3. **Error Handling**
- Graceful error handling in all services
- User-friendly error messages
- Logging for debugging

### 4. **Stateless Functions**
- All workflow nodes are pure functions
- State transformations are explicit
- Enables easy debugging and testing

### 5. **User Experience**
- Conversational and natural language
- Clear order summaries
- Multiple confirmation steps before payment
- Helpful alternatives when available

### 6. **Extensibility**
- Easy to add new products
- Simple to add new payment methods
- Can enhance with real payment processing
- Semantic search can be added via embeddings

### 7. **Observability**
- Comprehensive logging at each step
- Arize tracing integration (from common.config)
- Transaction and email logs
- Agent reasoning logs

## Running the Application

### Prerequisites
```bash
# Install poetry if not already installed
pip install poetry

# Install dependencies
cd /Users/kunaltiwary/projects/lumen-adaptive-commerce
poetry install
```

### Running Iteration 3

```bash
# Option 1: Using poetry script
poetry run iteration3

# Option 2: Direct Python
python -m iteration3.app
```

The UI will launch in your browser at the Gradio URL (typically `http://localhost:7860`).

## Sample Conversations

### Example 1: Complete Purchase Flow
```
User: I need a birthday gift for my 6-year-old
Agent: Great! Let me ask a few questions to find the perfect gift:
       - What's your budget range? ($25, $50, $100+)
       - What interests your child? (sports, arts, educational, outdoor)

User: Under $50, and they love outdoor activities
Agent: [Searches products for age 5-8, outdoor, under $50]
       I'd like to recommend the "Outdoor Scavenger Hunt Pack"
       Price: $30 | Great for groups | Educational | Eco-friendly

User: That sounds perfect! Let's proceed
Agent: [Creates order, shows default address and payment]
       I'll ship to: 123 Main Street, San Francisco, CA
       Payment: Credit card ending in 4242
       Total: $38.40 (includes tax and shipping)
       Should I proceed with payment?

User: Yes, go ahead
Agent: [Processes payment]
       ✓ Payment successful!
       Order confirmation email sent to alice@example.com
```

## Data Structures

### UserProfile
```python
{
    "user_id": "user_001",
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "shipping_addresses": [ShippingAddress],
    "payment_methods": [PaymentMethod],
    "preferences": {
        "notification_email": True,
        "marketing_emails": False,
        "preferred_gift_types": ["educational", "outdoor"]
    }
}
```

### Order
```python
{
    "id": "order_abc123",
    "user_id": "user_001",
    "items": [{
        "product_id": "prod_003",
        "product_name": "Outdoor Scavenger Hunt Pack",
        "quantity": 1,
        "unit_price": 30.00,
        "subtotal": 30.00
    }],
    "total_amount": 38.40,  # subtotal + tax (8%) + shipping ($10)
    "status": "completed",
    "shipping_address": ShippingAddress,
    "payment_method": PaymentMethod,
    "created_at": datetime,
    "completed_at": datetime
}
```

## Testing & Mock Data

### Sample Users
- **user_001**: Alice Johnson (user_001)
  - 2 shipping addresses (Home, Office)
  - 2 payment methods (Visa, Debit)
  - Prefers educational, outdoor gifts

- **user_002**: Bob Smith (user_002)
  - 1 shipping address (Home)
  - 1 payment method (Visa)
  - Prefers sports, educational gifts

### Sample Products
8 products across multiple categories:
- Price range: $25-$180
- Age ranges: 3-8, 5-10, 5-12
- Features: Educational, eco-friendly, group activities, etc.

## Extension Points

### 1. **Real Payment Processing**
Replace `PaymentProcessor` mock with real Stripe/PayPal integration:
```python
def process_payment(self, order: Order) -> Tuple[bool, str, Optional[str]]:
    # Use stripe.py or similar
    response = stripe.PaymentIntent.create(
        amount=int(order["total_amount"] * 100),
        currency="usd",
        ...
    )
```

### 2. **Semantic Search**
Add embedding-based product search:
```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

vectorstore = Chroma(
    collection_name="products",
    embedding_function=OpenAIEmbeddings()
)
```

### 3. **Multi-turn Tool Use**
Enable agent to use tools within reasoning loop:
```python
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(llm, AGENT_TOOLS)
```

### 4. **Inventory Management**
Add stock tracking to prevent overselling:
```python
@dataclass
class Product:
    id: str
    name: str
    price: float
    stock_quantity: int
```

### 5. **User Authentication**
Add proper authentication flow:
```python
@tool
def authenticate_user(email: str, password: str) -> Optional[UserProfile]:
    # Hash and verify password
    user = user_db.get_by_email(email)
    if verify_password(password, user.password_hash):
        return user
```

### 6. **Recommendation Engine**
Add ML-based recommendations:
```python
from sklearn.metrics.pairwise import cosine_similarity

recommendations = recommend_products(
    user_profile=user_profile,
    similar_to_product=viewed_product,
    top_k=5
)
```

## Logging & Monitoring

All operations are logged via Python logging:
```
[INFO] User message: I need a gift for my 6-year-old
[INFO] Agent reasoning - Next action: recommend_product
[INFO] Found 3 product recommendations
[INFO] Payment processed - Success: True
[INFO] Order 12345 completed successfully
[INFO] Order confirmation email sent
```

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Troubleshooting

### Agent not recommending products
- Check if occasion and age_group are extracted
- Verify product database has matches
- Check LLM response formatting

### Payment always fails
- Increase `_success_rate` in PaymentProcessor
- Check payment method is valid
- Verify order total is calculated correctly

### Email not sending
- Verify user email is in profile
- Check email_service logs
- Mock service just logs emails (check console)

## Future Enhancements

1. **Advanced NLP**: Use intent classification for better action routing
2. **Multi-product orders**: Support adding multiple items to cart
3. **Inventory awareness**: Prevent recommending out-of-stock items
4. **A/B testing**: Test different recommendation strategies
5. **Feedback loop**: Learn from user preferences over time
6. **Multi-language**: Support conversations in multiple languages
7. **Voice interface**: Add speech-to-text and text-to-speech
8. **Analytics**: Track conversion rates, average order value, etc.

## License

This project is part of the Lumen Adaptive Commerce platform.
