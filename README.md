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

## Testing

Run tests for the conversational agent:

```bash
pytest iteration2/
```