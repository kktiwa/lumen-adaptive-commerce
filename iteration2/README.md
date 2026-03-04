# Iteration 2: Conversational Shopping Assistant

## Overview

Iteration 2 enhances the adaptive commerce platform with a **multi-turn conversational experience** where:
- User preferences are pre-loaded from a selected profile
- The AI agent guides conversation to understand exact needs
- The system asks clarifying questions until it has enough context
- Products are recommended based on conversation context

## Architecture

### Core Components

#### 1. **conversation_types.py**
Defines TypedDict schemas for:
- `UserPreferences` - Budget, interests, preferences
- `ConversationContext` - Occasion, age group, quantity, specific needs
- `ConversationMessage` - Role, content, timestamp
- `ConversationState` - Full state for LangGraph

#### 2. **user_preferences.py**
Manages user profiles with sample data:
- 3 pre-built profiles with different budgets and interests
- `load_user_preferences()` - Load profile by ID
- `get_available_profiles()` - List available profiles

#### 3. **product_database.py**
Sample product database with 8+ products including:
- Toys, games, educational items, sports equipment
- Metadata: price, age range, occasion, features, eco-friendly, educational
- `search_products()` - Filter by occasion, age, price, preferences
- `get_product_by_id()` - Look up specific product

#### 4. **chat_prompts.py**
LLM prompts for the conversational agent:
- System prompt with user context
- Context extraction prompt
- Product recommendation prompt
- `get_system_prompt()` - Build prompt with user info
- `get_recommendation_prompt()` - Build recommendation prompt

#### 5. **chat_workflow.py**
LangGraph multi-turn workflow with nodes:
- `process_user_message` - Add message to history
- `extract_context` - Extract occasion, age, quantity from message
- `generate_response` - Generate assistant response using LLM
- `get_recommendations` - Search for products when ready
- `create_initial_state()` - Initialize conversation with loaded preferences

#### 6. **chat_app.py**
Main application engine:
- `ConversationalChatEngine` - Manages conversation state and flow
- `send_message()` - Process user input and get response
- `get_conversation_history()` - Retrieve full conversation
- `reset_conversation()` - Start fresh conversation
- `run_chat_session()` - CLI interface for testing

#### 7. **chat_ui.py**
Gradio web interface:
- Profile selection dropdown
- Chat interface with history
- Product recommendations display
- Reset conversation button

## Key Features

### ✅ Conversational Flow
- Multi-turn conversation with context preservation
- Asks clarifying questions only when needed
- Remembers previous messages for better context

### ✅ Pre-loaded Preferences
- Users start with a selected profile
- Budget, interests, and preferences already set
- Agent uses this context to make better recommendations

### ✅ Smart Context Extraction
- Automatically extracts: occasion, age group, quantity needed
- Understands keywords like "birthday party", "5 year old", etc.
- Builds up understanding across multiple messages

### ✅ Agent-Guided Narrowing
- Agent asks follow-up questions if needed
- Requires clear context before recommending
- Uses [READY_TO_RECOMMEND] marker for completion

### ✅ Product Matching
- Filters products by budget, age range, occasion
- Respects user preferences (eco-friendly, educational, etc.)
- Returns relevant products with details

## Usage

### Web Interface (Gradio)
```bash
# Run from project root
python run_iteration2.py
```

Then:
1. Select a user profile (profile1, profile2, or profile3)
2. Click "Load Profile"
3. Start typing your question
4. Conversation will narrow down to specific product recommendations

### Example Conversation
**User**: "I want to buy products for hosting a birthday party for my 5 year old"

**Agent**: "Great! A birthday party for a 5-year-old is fun! To help me find the best products, I have a quick question - are you looking for decorations, games, toys, or a mix of things?"

**User**: "Mix of games and toys"

**Agent**: "Perfect! One more thing - roughly how many kids will be at the party?"

**User**: "About 6 kids"

**Agent**: "Got it! Based on your budget of $50-100... [READY_TO_RECOMMEND]"

*System recommends 3-5 products*

### CLI Interface (For Testing)
```bash
from iteration2.chat_app import run_chat_session
run_chat_session("profile1")
```

## Data Models

### User Profile Structure
```python
{
    "budget": "$50-100",  # "$0-50", "$50-100", "$100-200", "$200+"
    "interests": ["sports", "outdoor activities", "tech"],
    "preferences": {
        "eco_friendly": bool,
        "premium": bool,
        "educational": bool
    }
}
```

### Product Structure
```python
{
    "id": "prod_001",
    "name": "Product Name",
    "category": "toys",
    "price": 25,
    "age_range": "5-8",
    "occasion": ["birthday party", "outdoor play"],
    "features": ["feature1", "feature2"],
    "educational": bool,
    "eco_friendly": bool
}
```

## Future Enhancements

1. **Better Context Extraction**
   - Use LLM for semantic extraction instead of keyword matching
   - Handle more complex scenarios

2. **Persistent Conversations**
   - Save conversations to database
   - Allow resuming conversations

3. **Richer Product Database**
   - Real product catalog with images
   - Dynamic product loading from API

4. **User Feedback**
   - Rate recommendations (thumbs up/down)
   - Learn from interactions

5. **Multi-language Support**
   - Support for Spanish, French, etc.

6. **Advanced Filtering**
   - Brand preferences
   - Specific allergen information
   - Shipping preferences

## Integration with Arize

The chat workflow uses the same Arize instrumentation as iteration1. All LLM calls and agent decisions are automatically traced for monitoring.

## Testing

To test the conversation flow:
```bash
from iteration2.chat_app import ConversationalChatEngine

engine = ConversationalChatEngine("profile1")

# Simulate conversation
response1 = engine.send_message("I want to buy products for hosting a birthday party for my 5 year old")
print(response1["response"])

response2 = engine.send_message("Mix of games and toys")
print(response2["response"])
```
