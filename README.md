# Lumen Adaptive Commerce

An AI-powered personalization and agentic commerce platform that dynamically adapts product discovery, content generation, and the end-to-end shopping journey.

- **Iteration 1:** Adaptive product search results
- **Iteration 2:** Contextual conversational commerce agent
- **Iteration 3:** Autonomous multi-agent shopping flow

Built with:

- LangChain
- LangGraph
- Gradio
- Python 3.10+
- ChromaDB (Vector Search)
- OpenAI Embeddings

## Getting Started

### Install dependencies

```bash
poetry install
```

### Running Iterations

#### Iteration 1: Adaptive Product Search

Run the adaptive product search interface:

```bash
poetry run python -m iteration1.app
```

This launches a Gradio UI where you can input user preferences and product details to generate adaptive product descriptions.

---

## Iteration 2: Conversational Shopping Assistant

### Overview

Iteration 2 enhances the adaptive commerce platform with a **multi-turn conversational experience** where:
- User preferences are pre-loaded from a selected profile
- The AI agent guides conversation to understand exact needs
- The system asks clarifying questions until it has enough context
- Products are recommended based on conversation context and vector similarity search

### Architecture

#### Core Components

**1. conversation_types.py**
- TypedDict schemas for user profiles, conversation context, and state management
- Supports multi-turn conversation tracking with LangGraph

**2. user_preferences.py**
- Manages 3 pre-built user profiles with different budgets and interests
- `load_user_preferences()` - Load profile by ID
- `get_available_profiles()` - List available profiles

**3. product_database.py**
- Vector-enhanced product database using LangChain Chroma
- 8+ sample products with embeddings for semantic search
- Products include: toys, games, educational items, sports equipment
- Native `similarity_search()` with metadata filtering for:
  - Price bounds
  - Age ranges
  - Educational/eco-friendly preferences
- Optimized document indexing for embedding efficiency

**4. chat_prompts.py**
- Dynamic system prompts with context awareness
- Prevents repeated questions by tracking extracted context
- Context extraction prompt for semantic understanding
- Product recommendation prompt for personalized suggestions

**5. chat_workflow.py**
- LangGraph multi-turn workflow with 4 nodes:
  - `process_user_message` - Track conversation history
  - `extract_context` - Accumulate occasion, age, quantity, specific needs
  - `generate_response` - LLM-powered conversational replies
  - `get_recommendations` - Vector similarity search for products

**6. chat_app.py**
- Main application engine: `ConversationalChatEngine`
- `send_message()` - Process user input and return response
- `get_conversation_history()` - Full conversation retrieval
- `reset_conversation()` - Start new conversation
- `run_chat_session()` - CLI testing interface

**7. chat_ui.py**
- Gradio web interface with profile selection
- Real-time chat experience with conversation history
- Dynamic product recommendations display
- Reset conversation capability

### Key Features

✅ **Conversational Flow**
- Multi-turn dialogue with context preservation
- Avoids repeating previously asked questions
- Accumulates information across turns

✅ **Pre-loaded Preferences**
- Users start with pre-selected profile
- Budget, interests, and preferences already set
- Agent uses context for better recommendations

✅ **Smart Context Extraction**
- Automatically extracts: occasion, age group, quantity needed
- Accumulates context instead of replacing it
- Validates sufficient context before recommending

✅ **Vector-Powered Search**
- Native ChromaDB similarity search with metadata filtering
- Embeddings optimized for product semantics
- Top 4 most relevant results for optimal relevance

✅ **Validation & Safety**
- Requires occasion, age group, and specific needs before recommending
- Type-safe context handling
- Prevents premature product displays

### Usage

#### Web Interface (Gradio)
```bash
poetry run python -m iteration2.chat_ui
```

Then:
1. Select a user profile (profile1, profile2, or profile3)
2. Click "Load Profile"
3. Start typing your question
4. Conversation narrows down to specific product recommendations

#### Example Conversation
```
User: "I want to buy products for hosting a birthday party for my 5 year old"

Agent: "Great! A birthday party for a 5-year-old is fun! To help me find the best 
products, I have a quick question - are you looking for decorations, games, toys, 
or a mix of things?"

User: "Mix of games and toys"

Agent: "Perfect! One more thing - roughly how many kids will be at the party?"

User: "About 6 kids"

Agent: "Got it! Based on your budget and preferences, here are my top recommendations..."

[System displays 3-5 relevant products]
```

#### CLI Testing
```python
from iteration2.chat_app import ConversationalChatEngine

engine = ConversationalChatEngine("profile1")

# Simulate conversation
response1 = engine.send_message("Products for birthday party for my 5 year old")
print(response1["response"])

response2 = engine.send_message("Mix of games and toys")
print(response2["response"])
```

### Data Models

**User Profile Structure**
```python
{
    "budget": "$50-100",  # Options: "$0-50", "$50-100", "$100-200", "$200+"
    "interests": ["sports", "outdoor activities", "tech"],
    "preferences": {
        "eco_friendly": bool,
        "premium": bool,
        "educational": bool
    }
}
```

**Product Structure**
```python
{
    "id": "prod_001",
    "name": "Product Name",
    "category": "toys",
    "price": 25,
    "age_range": "5-8",
    "occasion": ["birthday party", "outdoor play"],
    "features": ["feature1", "feature2"],
    "description": "Product description",
    "educational": bool,
    "eco_friendly": bool
}
```

### Future Enhancements

1. **Persistent Storage**
   - Save conversations to database
   - Resume interrupted conversations

2. **Real Product Catalog**
   - Integration with actual product data
   - Dynamic product loading from APIs
   - Real product images and reviews

3. **User Feedback Loop**
   - Rate recommendations (thumbs up/down)
   - Learn from per-user interactions
   - Improve recommendations over time

4. **Multi-language Support**
   - Support for Spanish, French, and other languages

5. **Advanced Filtering**
   - Brand preferences
   - Allergen information
   - Shipping preferences and constraints

6. **Conversation Analytics**
   - Track common questions and product interests
   - Identify gaps in product catalog
   - Monitor conversation quality metrics

### Integration with Arize

All LLM calls and agent decisions are automatically traced through Arize for:
- Performance monitoring
- Cost tracking
- Quality assessment
- Debugging

---

## Iteration 3: Autonomous Agentic E-Commerce Application

### Overview

Iteration 3 implements a fully autonomous agentic application that guides customers through an end-to-end shopping experience using an AI agent powered by LLMs and LangGraph. The agent converses naturally with customers, understands their needs, recommends products, handles checkout, processes payments, and sends order confirmations.

### Architecture

#### Core Components

```
iteration3/
├── agentic_types.py              # Type definitions for agentic state & entities
├── user_management.py            # User profiles, addresses, payment methods
├── order_management.py           # Order creation and tracking
├── payment_processor.py          # Payment processing (mock)
├── email_service.py              # Order confirmation emails
├── product_database.py           # Product catalog with vector search
├── vector_search.py              # ChromaDB semantic search (NEW)
├── tools.py                      # Agent tools/actions
├── agentic_prompts.py           # System prompts & message formatting
├── agentic_workflow.py          # LangGraph workflow (core logic)
├── agentic_ui.py                # Gradio UI
└── app.py                       # Entry point
```

#### Workflow Flow

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

#### Key Design Patterns

**1. State Management with LangGraph**
- Centralized `AgenticState` TypedDict manages all conversation and order data
- Each workflow node is a pure function that transforms state
- Stateless design enables easy debugging and testing

**2. Service Layer Architecture**
- **UserManager**: Handles user profiles, shipping addresses, payment methods
- **OrderManager**: Creates and tracks orders with pricing calculations
- **PaymentProcessor**: Processes payments with transaction logging
- **EmailService**: Sends confirmations and shipping notifications
- **VectorSearch**: ChromaDB-powered semantic product search with embeddings

**3. LLM-driven Agent Reasoning**
- Multi-step reasoning process with conversation context extraction
- Agent decides which action to take based on conversation progress
- Natural language prompts guide the LLM's decision-making

**4. Semantic Product Discovery**
- ChromaDB with OpenAI embeddings for intelligent product matching
- Natural language queries instead of rigid field matching
- Relevance ranking by semantic similarity
- Fast filtering by budget, age group, educational, eco-friendly, etc.

### Key Features

✅ **Natural Conversation Flow**
- Agent asks clarifying questions about occasion, age group, budget, needs
- Extracts context incrementally from multi-turn conversations
- Personalized recommendations based on extracted context
- Stops asking follow-ups once user provides category, age, and budget

✅ **Semantic Product Recommendation**
- Intelligent semantic search using OpenAI embeddings
- Products ranked by relevance, not just field matches
- Supports filtering by price, age range, occasion, educational value, eco-friendliness
- Explains why each product is a good match

✅ **Intelligent Checkout**
- Shows default shipping address and payment method
- Offers alternatives if multiple are saved
- Requires explicit user confirmation before payment

✅ **Payment Processing**
- Mock payment processor with realistic success/failure simulation
- Transaction logging for auditing
- Error handling and user-friendly error messages
- Refund support (for future implementation)

✅ **Order Management**
- Automatic order creation with calculated totals (subtotal + tax + shipping)
- Order status tracking (pending → processing → completed)
- Order summaries with all details

✅ **Email Notifications**
- Automated order confirmation emails
- Shipping notifications (can be sent after shipment)
- Mock email service with logging

### Best Practices Implemented

✅ **Separation of Concerns** - Each module has single responsibility
✅ **Type Safety** - Full TypedDict usage for all data structures
✅ **Error Handling** - Graceful error handling with user-friendly messages
✅ **Stateless Functions** - Pure functions enable easy debugging and testing
✅ **Extensibility** - Easy to add new products, payment methods, or enhancementss
✅ **Observability** - Comprehensive logging and Arize tracing integration

### Running Iteration 3

```bash
# Using poetry script
poetry run iteration3

# Or direct Python
python -m iteration3.app
```

The UI will launch in your browser at the Gradio URL (typically `http://localhost:7860`).

### Type System

**Core AgenticState**
```python
AgenticState(TypedDict):
    user_profile: Optional[UserProfile]
    conversation_history: List[ConversationMessage]
    conversation_context: ConversationContext
    agent_steps: List[AgentStep]
    next_action: AgentActionType
    selected_product: Optional[Product]
    current_order: Optional[Order]
    payment_successful: bool
    order_completed: bool
    email_sent: bool
```

### Sample Conversation

```
User: I need a birthday gift for my 6-year-old, budget under $50, for outdoor activities

Agent: Perfect! I found some great outdoor toys for that age and budget.
       I'd like to recommend the "Outdoor Scavenger Hunt Pack"
       Price: $30 | Great for groups | Educational | Eco-friendly
       
       Would this work for you?

User: Yes, let's get it!

Agent: Great! I'll create your order:
       Product: Outdoor Scavenger Hunt Pack ($30)
       Shipping to: 123 Main Street, San Francisco, CA
       Payment: Visa ending in 4242
       Total: $38.40 (includes $2.40 tax + $6 shipping)
       
       Should I proceed?

User: Yes, please

Agent: ✓ Payment successful! Order confirmation sent to alice@example.com
```

### Data Structures

**UserProfile**
```python
{
    "user_id": "user_001",
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "shipping_addresses": [ShippingAddress],
    "payment_methods": [PaymentMethod],
}
```

**Order**
```python
{
    "id": "order_abc123",
    "user_id": "user_001",
    "items": [{
        "product_id": "prod_003",
        "product_name": "Outdoor Scavenger Hunt Pack",
        "quantity": 1,
        "unit_price": 30.00,
    }],
    "total_amount": 38.40,  # subtotal + tax + shipping
    "status": "completed",
}
```

### Extension Points

1. **Real Payment Processing** - Replace mock with Stripe/PayPal
2. **Inventory Management** - Add stock tracking to prevent overselling
3. **User Authentication** - Add proper auth flow with password hashing
4. **ML-based Recommendations** - Enhance with collaborative filtering
5. **Multi-turn Tool Use** - Enable agent to invoke tools within reasoning loop

---

## Testing

Run tests for the conversational agent:

```bash
pytest iteration2/
```

Test vector search functionality:

```bash
poetry run python iteration3/test_vector_search.py
```