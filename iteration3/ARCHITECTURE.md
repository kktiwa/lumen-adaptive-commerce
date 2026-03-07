# Iteration 3 Architecture & Design Document

## Executive Summary

Iteration 3 implements a production-ready autonomous agentic e-commerce system using modern LLM and agentic patterns. It demonstrates how to build intelligent, stateful multi-turn conversations that guide users through complex business logic (product recommendation → checkout → payment → fulfillment).

## Design Philosophy

### Core Principles

1. **State as First-Class Citizen**
   - All conversation and business state centralized in `AgenticState`
   - No hidden state in LLM context
   - Enables reproducibility, testing, and debugging

2. **Composable Service Layer**
   - Each service handles one domain: Users, Orders, Payments, Email
   - Services are dependency-free and mockable
   - Easy to swap implementations (e.g., real payment processor)

3. **LLM as Decision Engine, Not Executor**
   - LLM handles reasoning and natural language understanding
   - Business logic executed by deterministic services
   - Keeps costs and latency low

4. **Linear Workflow with Branching**
   - Clear entry/exit points for each workflow step
   - Branching logic minimal and explicit
   - Easy to understand control flow

## Component Deep Dive

### 1. Type System (`agentic_types.py`)

**Why TypedDict over Dataclasses?**
- Required by LangGraph for state serialization
- More flexible for optional fields
- Standard in LangChain ecosystem

**Key Type Hierarchy:**
```
AgenticState (master state container)
├── ConversationState
│   ├── conversation_history
│   └── conversation_context
├── UserState
│   ├── user_profile
│   ├── default_shipping_address
│   └── alternate_shipping_addresses
├── OrderState
│   └── current_order
└── PaymentState
    ├── payment_successful
    └── payment_error
```

**Design Decisions:**
- `AgentActionType` enum prevents action type mismatches
- `OrderStatus` enum ensures valid order transitions
- Optional fields allow partial state during workflow
- Timestamp on each ConversationMessage for audit trail

### 2. Service Layer

#### UserManager
**Responsibilities:**
- Load/create user profiles
- Manage shipping addresses and payment methods
- Query default vs. alternate options

**Key Decisions:**
- In-memory storage (easily replaced with database)
- Sample data provided for demo
- Default selection logic (first is default if none marked)

#### OrderManager
**Responsibilities:**
- Create orders from products and user info
- Calculate pricing (subtotal + tax + shipping)
- Track order status transitions
- Generate order summaries

**Key Decisions:**
- Immutable order creation (no editing after creation)
- Tax and shipping hardcoded for demo
- Status transitions guard against invalid states
- Summary generation for user communication

#### PaymentProcessor
**Responsibilities:**
- Process payments (mock for demo)
- Track transactions for auditing
- Support refunds

**Key Decisions:**
- Mock implementation with configurable success rate
- Transaction logging for every attempt
- Returns success + message + transaction_id tuple
- Extensible for real payment gateway

#### EmailService
**Responsibilities:**
- Send order confirmations
- Send shipping notifications
- Log all sent emails

**Key Decisions:**
- Mock implementation (just logs)
- Rich email templates with order details
- Separate methods for different email types

### 3. Agent Prompts (`agentic_prompts.py`)

**Prompt Engineering Strategy:**

1. **System Prompt**
   - Sets agent persona and responsibilities
   - Lists the 10 key responsibilities
   - Defines decision-making criteria

2. **Action-Specific Prompts**
   - Provide context for each decision point
   - Include current state (extracted context, order details)
   - Ask for specific next action with reasoning

3. **Message Templates**
   - Product recommendations with formatted details
   - Order summaries with calculated totals
   - Error messages with clarity

**Why This Approach:**
- System prompt sets initial behavior
- Action prompts add decision context
- Templates ensure consistency
- Easy to A/B test different prompts

### 4. Workflow Orchestration (`agentic_workflow.py`)

**State Machine Architecture:**

```
[ENTRY] process_input
↓
extract_context_from_conversation
↓
agent_reasoning
├─→ gather_information → [END]
├─→ recommend_product → [END]
├─→ summarize_recommendation → [END]
├─→ process_payment → [CONDITIONAL]
    ├─→ complete_order → send_order_email → [END]
    └─→ [END]
```

**Design Rationale:**

1. **Node as Pure Functions**
   ```python
   # Input: state
   # Output: modified state
   # No side effects (except logging)
   ```

2. **Conditional Routing**
   ```python
   def route_after_reasoning(state):
       if state["next_action"] == CONTINUE:
           return "gather_information"
       elif state["next_action"] == RECOMMEND:
           return "recommend_product"
       ...
   ```

3. **Action Propagation**
   - Each agent node updates `next_action`
   - Routing uses this to determine next node
   - Clear decision trail

### 5. Context Extraction

**Process:**
1. Get last 10 messages from conversation
2. Send to LLM with extraction template
3. Parse response as JSON
4. Merge with existing context
5. Update state

**Why This Works:**
- Incremental extraction keeps cost low
- Recent messages capture latest information
- JSON parsing is reliable
- Merging preserves long-term context

### 6. Payment Flow (Critical for Completeness)

**Three Outcomes:**

1. **Success → Complete Order → Email**
   ```
   process_payment (success)
   → complete_order (mark completed)
   → send_order_email (confirmation)
   ```

2. **Failure → Show Error → Continue**
   ```
   process_payment (failed)
   → [END] (let user retry with different method)
   ```

3. **User Cancels → No Payment**
   ```
   summarize_recommendation (user says "cancel")
   → [END]
   ```

## Data Flow Example: End-to-End Purchase

```
User: "I need a gift for my 6-year-old's birthday, budget under $50"

1. PROCESS_INPUT
   conversation_history = [{"role": "user", "content": "..."}]

2. EXTRACT_CONTEXT
   conversation_context = {
       "age_group": "5-8",
       "occasion": "birthday",
       "budget_range": "under $50",
       ...
   }

3. AGENT_REASONING (LLM decides)
   "We have occasion, age group, and budget. Search for products."
   next_action = RECOMMEND_PRODUCT

4. RECOMMEND_PRODUCT
   search_products(age_group="5-8", budget_max=50)
   → found ["Outdoor Scavenger Hunt Pack"]
   selected_product = prod_003
   next_action = CONTINUE_CONVERSATION

5. [Response 1 sent to user]

User: "That sounds perfect, let's buy it"

6. PROCESS_INPUT
   conversation_history += [user message]

7. EXTRACT_CONTEXT
   user_confirmed = True (inferred from "buy it")

8. AGENT_REASONING (LLM decides)
   "User confirmed, product selected. Proceed to checkout."
   next_action = SUMMARIZE_RECOMMENDATION

9. SUMMARIZE_RECOMMENDATION
   current_order = OrderManager.create_order(
       product=prod_003,
       shipping_address=alice_home,
       payment_method=alice_visa
   )
   → order total = $38.40

10. [Order summary sent to user]

User: "Yes, proceed with payment"

11. PROCESS_INPUT
12. EXTRACT_CONTEXT
13. AGENT_REASONING → next_action = PROCESS_PAYMENT

14. PROCESS_PAYMENT
    success, message, txn_id = PaymentProcessor.process_payment(order)
    → success = True
    payment_successful = True
    next_action = COMPLETE_ORDER

15. COMPLETE_ORDER
    OrderManager.update_order_status("completed")
    order_completed = True
    next_action = SEND_ORDER_EMAIL

16. SEND_ORDER_EMAIL
    EmailService.send_order_confirmation_email(user, order)
    email_sent = True
    next_action = END

17. [Success message + email confirmation sent to user]
```

## Design Patterns Used

### 1. **Command Pattern** (Agent Actions)
- Each action is a command with parameters
- Actions queued in agent_steps for audit trail

### 2. **Service Locator Pattern** (Services)
- Global instances: user_manager, order_manager, etc.
- Easy to mock for testing
- Alternative: Dependency injection

### 3. **State Machine Pattern** (Workflow)
- Explicit states and transitions
- Clear entry/exit conditions
- Prevents invalid state combinations

### 4. **Strategy Pattern** (LLM Agent)
- Different LLM prompts for different contexts
- Agent strategy switches based on conversation state

### 5. **Decorator Pattern** (Gradio UI)
- UI wraps workflow and manages state
- Handles async/sync conversion
- Manages UI state updates

## Error Handling Strategy

### Levels of Error Handling:

1. **Service Level** (within each service)
   ```python
   user = user_manager.get_user(user_id)
   if not user:
       return None, "User not found"
   ```

2. **Workflow Level** (in workflow nodes)
   ```python
   if not state["selected_product"]:
       state["assistant_response"] = "No product selected yet"
       return state
   ```

3. **LLM Level** (in agent reasoning)
   ```python
   # LLM generates error messages naturally
   # "You need to select a payment method first"
   ```

4. **UI Level** (in Gradio)
   ```python
   try:
       result = workflow.invoke(state)
   except Exception as e:
       return "I encountered an error. Please try again."
   ```

## Performance Considerations

### Optimization Strategies:

1. **Context Windowing**
   - Only use last 10 messages for extraction
   - Prevents token bloat

2. **Caching**
   - User profiles cached in memory
   - Product catalog preloaded
   - No repeated database queries

3. **Single LLM Call per Node**
   - MAX 2 LLM calls per message (context extraction + reasoning)
   - Reduces latency and cost
   - Most nodes are deterministic (no LLM needed)

4. **Parallel Optional Queries**
   - Could load user addresses + payment methods in parallel
   - Currently sequential (not a bottleneck)

### Scalability Notes:

- **Users**: 1000s easily (in-memory demo, swap with DB)
- **Messages**: Windowing prevents history size explosion
- **Products**: 100s to 1000s (depends on search efficiency)
- **LLM Calls**: ~2 per user message → manageable scale
- **Database**: Not yet integrated (design ready for it)

## Testing Strategy

### Unit Tests (Test Individual Services)

```python
def test_order_creation():
    order = order_manager.create_order(
        user_id="user_001",
        product=product_001,
        quantity=1,
        address=address_001,
        payment=payment_001
    )
    assert order["total_amount"] == 38.40  # $30 + tax + shipping
```

### Integration Tests (Test Workflow)

```python
def test_purchase_flow():
    state = initialize_state()
    state["current_message"] = "I need a gift for 6-year-old, under $50"
    
    # Process through workflow
    result = workflow.invoke(state)
    
    assert len(result["product_recommendations"]) > 0
    assert result["next_action"] == CONTINUE_CONVERSATION
```

### E2E Tests (Test Full Flow)

```python
def test_complete_purchase():
    # Simulate full conversation
    messages = [
        "I need a gift for my 6-year-old",
        "Yes, that product looks great",
        "Proceed with payment"
    ]
    
    for msg in messages:
        result = process_message(msg)
    
    assert result["order_completed"] == True
    assert result["email_sent"] == True
```

## Security Considerations

### Current Implementation (for demo):

1. **No Authentication**
   - Hardcoded user session
   - OK for demo, needs implementation for production

2. **No Encryption**
   - Payment info in plaintext in memory
   - Must use tokenization + PCI compliance

3. **No Rate Limiting**
   - Could add per-user request limits

4. **Mock Payment Processing**
   - Never accept real card data in this implementation
   - Use proper payment gateway with PCI compliance

### Production Checklist:

- [ ] User authentication (OAuth2/JWT)
- [ ] Encryption at rest + in transit (TLS)
- [ ] Rate limiting (API gateway)
- [ ] Input validation (all user inputs)
- [ ] SQL injection prevention (if using DB)
- [ ] CSRF protection (if web-based)
- [ ] PCI compliance for payments
- [ ] Data retention policies
- [ ] Audit logging
- [ ] Secrets management (API keys, DB credentials)

## Monitoring & Observability

### Logging Levels:

```python
logger.debug("Detailed workflow state")  # Dev only
logger.info("User action completed")      # Production
logger.warning("Fallback strategy used")  # Monitor
logger.error("Service failed")            # Alert
```

### Key Metrics to Track:

1. **Conversion**: % of conversations → completed orders
2. **Latency**: Time from user message → agent response
3. **LLM Calls**: Cost per conversation
4. **Error Rate**: % of failed payments, invalid contexts
5. **User Satisfaction**: (future) Would need feedback mechanism

### Integration Points:

- **Arize Tracing** (already integrated in common.config)
- **Application Metrics** (can add via statsd/prometheus)
- **Payment Metrics** (transaction log)
- **Email Metrics** (sent_emails log)

## Deployment Architecture

### Local Development:
```
poetry run iteration3
→ Launches Gradio UI
→ Single-process
→ No scaling needed
```

### Production Deployment:

```
                    ┌─────────────────┐
                    │   Gradio UI     │
                    │  (load balanced)│
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │ Worker  │         │ Worker  │         │ Worker  │
    │ (async) │         │ (async) │         │ (async) │
    └────┬────┘         └────┬────┘         └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │  API Gateway    │
                    │  (rate limit,   │
                    │   cache)        │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
    ┌─────────────┐  ┌──────────────┐   ┌────────────┐
    │   LLM API   │  │  Database    │   │  Payment   │
    │  (OpenAI)   │  │  (PostgreSQL)│   │  Gateway   │
    └─────────────┘  └──────────────┘   └────────────┘
```

## Future Enhancements

### Level 1: Core Features
- [ ] Multi-item carts
- [ ] Product reviews/ratings
- [ ] User account login
- [ ] Order history

### Level 2: Intelligence
- [ ] Semantic product search (embeddings)
- [ ] Personalized recommendations (ML)
- [ ] Intent classification (better action routing)
- [ ] Sentiment analysis (detect user frustration)

### Level 3: Enterprise
- [ ] Real payment processing (Stripe)
- [ ] Inventory management
- [ ] Warehouse integration
- [ ] Multi-currency support
- [ ] A/B testing framework

### Level 4: Advanced
- [ ] Multi-language support
- [ ] Voice/speech interface
- [ ] Mobile app integration
- [ ] Predictive analytics
- [ ] Fraud detection

## Comparison: Iteration 2 → Iteration 3

| Aspect | Iteration 2 | Iteration 3 |
|--------|-------------|------------|
| User Role | Conversational | Autonomous Agent |
| Scope | Product Recommendation | End-to-end Purchase |
| Payment | Not implemented | Implemented (mock) |
| Order Management | Not implemented | Full order lifecycle |
| State Management | Simple context | Comprehensive AgenticState |
| Workflow | Single agent | Multi-step workflow |
| User Confirmation | Not required | Multiple confirmations |
| Error Recovery | Limited | Comprehensive |

## Conclusion

Iteration 3 demonstrates production-ready patterns for autonomous agentic applications:

1. **State as Source of Truth** → Reproducible, debuggable
2. **Composable Services** → Maintainable, testable
3. **LLM for Reasoning** → Natural, flexible decision-making
4. **Explicit Workflow** → Clear control flow, easy debugging
5. **Type Safety** → Catch errors early

These patterns are applicable beyond e-commerce to any domain requiring multi-turn, stateful AI interactions with complex business logic.
