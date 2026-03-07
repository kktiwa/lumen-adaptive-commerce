# Getting Started with Iteration 3

## Quick Start (5 minutes)

### 1. Prerequisites

Make sure you have:
- Python 3.10+
- Poetry
- OpenAI API key (.env file)

### 2. Install & Run

```bash
# Navigate to project
cd /Users/kunaltiwary/projects/lumen-adaptive-commerce

# Install dependencies (if not already done)
poetry install

# Run iteration 3
poetry run iteration3
```

The application will launch in your browser at `http://localhost:7860`

## Sample Conversation Script

Try this conversation to test the full flow:

### Message 1:
```
I need a gift for my 6-year-old's birthday party. What do you have?
```

**Agent Response:** Will ask about budget and preferences

### Message 2:
```
Under $50, and they like outdoor activities
```

**Agent Response:** Will search and recommend "Outdoor Scavenger Hunt Pack"

### Message 3:
```
That sounds perfect! Let's buy it.
```

**Agent Response:** Will show order summary with:
- Product details
- Default shipping address
- Default payment method
- Total price ($38.40)
- Alternative options

### Message 4:
```
Yes, proceed with payment
```

**Agent Response:** Will process payment and send confirmation
- Order completed ✓
- Payment successful ✓
- Email sent ✓

## Understanding the State

During conversation, the agent maintains this state:

```python
{
    "user_profile": UserProfile,           # Current user (Alice Johnson by default)
    "conversation_history": [              # All messages so far
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        ...
    ],
    "conversation_context": {              # Extracted needs
        "occasion": "birthday party",
        "age_group": "5-8",
        "budget_range": "under $50",
        "specific_needs": ["outdoor"],
        ...
    },
    "selected_product": {                  # The product to buy
        "id": "prod_003",
        "name": "Outdoor Scavenger Hunt Pack",
        "price": 30,
        ...
    },
    "current_order": {                     # Order being processed
        "id": "order_abc123",
        "total_amount": 38.40,
        ...
    },
    "payment_successful": True,            # Payment status
    "order_completed": True,               # Order status
    "email_sent": True,                    # Confirmation sent
}
```

## Workflow Nodes (What Happens Behind the Scenes)

```
User: "I need a gift for my 6-year-old"
                    ↓
         [process_input] ← Parse user message
                    ↓
      [extract_context] ← Extract "age 6" from text
                    ↓
    [agent_reasoning] ← LLM decides: "Need budget info"
                    ↓
   [gather_information] ← Ask for budget
                    ↓
            → Response sent to user

User: "Under $50"
                    ↓
         [process_input]
                    ↓
      [extract_context] ← Extract budget now
                    ↓
    [agent_reasoning] ← LLM decides: "Have enough info!"
                    ↓
    [recommend_product] ← Search for matching products
                    ↓
    → Recommendation sent to user

User: "Let's buy it"
                    ↓
         [process_input]
                    ↓
    [agent_reasoning] ← "User confirmed, show checkout"
                    ↓
  [summarize_recommendation] ← Create order, show summary
                    ↓
            → Order summary sent

User: "Proceed with payment"
                    ↓
    [process_payment] → Payment processing
                    ↓
    [complete_order] → Mark order completed
                    ↓
   [send_order_email] → Send confirmation
                    ↓
      → Success message sent
```

## Checking Results

### View Order in System

After completing a purchase, check the order:

```python
# In Python console
from iteration3.order_manager import OrderManager
om = OrderManager()
orders = om.get_user_orders("user_001")
order = orders[-1]  # Latest order
print(om.get_order_summary(order))
```

**Output:**
```
ORDER SUMMARY
=============
Order ID: order_abc123

Items:
  - Outdoor Scavenger Hunt Pack (Qty: 1) - $30.00 each = $30.00

Subtotal: $30.00
Tax (8%): $2.40
Shipping: $10.00
TOTAL: $42.40

Shipping Address:
Home
123 Main Street
San Francisco, CA 94110
USA

Payment Method:
Credit Card
*** **** **** 4242
```

### View Payment Transactions

```python
from iteration3.payment_processor import PaymentProcessor
pp = PaymentProcessor()
log = pp.get_transaction_log()
for txn in log:
    print(f"{txn['status']}: ${txn['amount']} - {txn['order_id']}")
```

### View Sent Emails

```python
from iteration3.email_service import EmailService
es = EmailService()
emails = es.get_sent_emails()
for email in emails:
    print(f"To: {email['to']}")
    print(f"Subject: {email['subject']}")
    print(f"Body preview: {email['body'][:100]}...")
```

## Testing Different Scenarios

### Scenario 1: Budget-Conscious Shopper

```
User: "I need something for 5-year-old under $25"
→ Will recommend: Superhero Cape ($25) or Party Game Pack ($35 - too expensive)
→ Best match: Superhero Cape
```

### Scenario 2: Educational Focus

```
User: "Looking for educational toys for 8-year-old, budget $50-100"
→ Will recommend: STEM Robot Kit ($45) or Art Box ($55)
→ Multiple options for user to choose
```

### Scenario 3: Eco-Conscious

```
User: "Need eco-friendly gift"
→ Will ask for age/budget to narrow down
→ Will recommend: Bamboo Toy Set ($40) or Scavenger Hunt Pack ($30)
→ Both eco-friendly options
```

### Scenario 4: Group Activity

```
User: "Need something for party with 20 kids"
→ Will search for group activities
→ Will recommend: Party Game Pack ($35) or Scavenger Hunt ($30)
```

## Troubleshooting

### Problem: Agent keeps asking questions

**Cause:** Not enough context extracted
**Solution:** Be more specific in your message
```
Instead of: "I need a gift"
Try: "I need a birthday gift for my 6-year-old under $50"
```

### Problem: Wrong product recommended

**Cause:** Age group or budget range not understood correctly
**Solution:** Rephrase with clear numbers
```
Instead of: "young child"
Try: "5-year-old" or "between 3-5 years"
```

### Problem: Payment processing seems stuck

**Cause:** LLM response formatting issue
**Solution:** Check the logs in the terminal for error messages

### Problem: Email not shown

**Cause:** Mock email service (by design for testing)
**Solution:** Check the email_service logs - emails are logged to console

## Customization Examples

### Change Success Rate of Payments

```python
# In agentic_workflow.py
payment_processor._success_rate = 0.90  # 90% success rate
```

### Add a New User

```python
from iteration3.user_management import UserManager

um = UserManager()
new_user = um.create_user(
    name="Carol Smith",
    email="carol@example.com"
)
um.add_shipping_address(
    user_id=new_user["user_id"],
    name="Home",
    street="789 Maple St",
    city="Austin",
    state="TX",
    zip_code="78701",
    is_default=True
)
um.add_payment_method(
    user_id=new_user["user_id"],
    payment_type="credit_card",
    last_four="9999",
    cardholder_name="Carol Smith",
    expiry_date="12/25",
    is_default=True
)
```

### Add a New Product

```python
# In iteration3/product_database.py
PRODUCT_DATABASE.append({
    "id": "prod_009",
    "name": "Premium Coding Robot",
    "category": "educational tech",
    "price": 150,
    "age_range": "8-12",
    "occasion": ["birthday", "stem learning"],
    "features": ["programmable", "interactive", "advanced logic"],
    "description": "Advanced coding robot for young programmers.",
    "educational": True,
    "eco_friendly": False,
})
```

### Change Tax Rate or Shipping Cost

```python
# In iteration3/order_management.py, OrderManager.__init__()
self._TAX_RATE = 0.10  # Change to 10% tax
self._SHIPPING_COST = 15.0  # Change to $15 flat rate
```

### Modify Agent Prompts

```python
# In iteration3/agentic_prompts.py
def get_system_prompt() -> str:
    return """Your custom system prompt here..."""
```

## Next Steps

1. **Understand the Architecture**
   - Read [ARCHITECTURE.md](ARCHITECTURE.md) for design patterns
   - Review [README.md](README.md) for complete documentation

2. **Explore the Code**
   - `agentic_workflow.py` - Main state machine
   - `agentic_types.py` - Type definitions
   - `user_management.py` - User data handling
   - `order_management.py` - Order processing

3. **Extend the System**
   - Add new products to test recommendations
   - Implement real payment processing
   - Add inventory management
   - Integrate with real email service

4. **Deploy to Production**
   - Replace mock services with real implementations
   - Add authentication and authorization
   - Set up database (PostgreSQL recommended)
   - Configure logging and monitoring
   - Add rate limiting and security

## Key Files Reference

| File | Purpose |
|------|---------|
| `app.py` | Entry point |
| `agentic_ui.py` | Gradio UI wrapper |
| `agentic_workflow.py` | LangGraph workflow (CORE) |
| `agentic_types.py` | Type definitions |
| `agentic_prompts.py` | LLM prompts |
| `user_management.py` | User profiles |
| `order_management.py` | Order processing |
| `payment_processor.py` | Payment handling |
| `email_service.py` | Email notifications |
| `product_database.py` | Product catalog |
| `tools.py` | Agent tools |

## API Reference Quick Start

### Starting a Conversation

```python
from iteration3.agentic_workflow import initialize_state

state = initialize_state()
# state["user_profile"] = your_user  # Optional
# state["current_message"] = "user message"
```

### Processing a Message

```python
from iteration3.agentic_workflow import build_agentic_workflow

workflow = build_agentic_workflow().compile()
result_state = workflow.invoke(state)
print(result_state["assistant_response"])
```

### Accessing Results

```python
# Check if purchase completed
if result_state["order_completed"]:
    print("✓ Order complete!")
    print(f"Order ID: {result_state['current_order']['id']}")
    
# Check payment status
if result_state["payment_successful"]:
    print("✓ Payment processed successfully")
else:
    print(f"✗ Payment failed: {result_state['payment_error']}")
```

## Support & Questions

For issues or questions:
1. Check the [ARCHITECTURE.md](ARCHITECTURE.md) for design details
2. Review the docstrings in source files
3. Check the logs in your terminal
4. Refer to [README.md](README.md) for extension points

## Performance Tips

- First message takes longer (LLM cold start)
- Subsequent messages are faster (context in memory)
- Use recent conversations as examples for better results
- Keep user messages clear and specific

Enjoy building with Iteration 3! 🚀
