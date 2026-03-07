# Test Script: Verify Workflow State Transitions

This file documents the expected state transitions after the fix.

## Test Case 1: Complete Purchase Flow

### Scenario
User provides full context in first message and completes purchase.

### Messages & Expected Transitions

```
Message 1: "I need a birthday gift for my 6-year-old, under $50"
├─ extract_context()
│  ├─ occasion: "birthday"
│  ├─ age_group: "5-8"
│  └─ budget_range: "under $50"
├─ agent_reasoning()
│  ├─ Check: selected_product? NO
│  ├─ Check: has_occasion AND has_age AND has_budget? YES ✓
│  └─ next_action = RECOMMEND_PRODUCT ✓
├─ route_after_reasoning() → "recommend_product"
├─ recommend_product()
│  ├─ search_products_by_criteria(occasion, age_group, budget_max)
│  ├─ selected_product = best_match
│  ├─ assistant_response = recommendation message
│  └─ next_action = CONTINUE_CONVERSATION (ignored, goes to END)
└─ Response: Product recommendation shown to user

────────────────────────────────────────────────────────────────────

Message 2: "That sounds perfect!"
├─ extract_context()
│  └─ (no new context needed)
├─ agent_reasoning()
│  ├─ Check: selected_product? YES
│  ├─ Check: confirmation_pending? NO (False)
│  └─ next_action = SUMMARIZE_RECOMMENDATION ✓
├─ route_after_reasoning() → "summarize_recommendation"
├─ summarize_recommendation()
│  ├─ user_profile = user_001 (Alice)
│  ├─ current_order = create_order(product, user, address, payment)
│  ├─ confirmation_pending = True ✓
│  ├─ assistant_response = order summary + price breakdown
│  └─ next_action = CONTINUE_CONVERSATION (not used, goes to END)
└─ Response: Order summary shown (shipping, payment, total)

────────────────────────────────────────────────────────────────────

Message 3: "Yes, process the payment"
├─ extract_context()
│  └─ (no new context needed)
├─ agent_reasoning()
│  ├─ Check: selected_product? YES
│  ├─ Check: confirmation_pending? YES (True) - first condition FALSE
│  ├─ Check: current_order AND confirmation_pending? YES ✓
│  └─ next_action = PROCESS_PAYMENT ✓
├─ route_after_reasoning() → "process_payment"
├─ process_payment()
│  ├─ Check: current_order exists? YES ✓
│  ├─ payment_processor.process_payment(order)
│  ├─ payment_successful = True (95% probability)
│  ├─ assistant_response = payment success message
│  └─ order_status = PAYMENT_COMPLETED
├─ route_after_payment()
│  ├─ Check: payment_successful? YES ✓
│  └─ Route to: "complete_order"
├─ complete_order()
│  ├─ order_status = COMPLETED
│  ├─ order_completed = True
│  └─ next_action = SEND_ORDER_EMAIL (routing ignores, uses edge)
├─ send_order_email()
│  ├─ email_service.send_order_confirmation_email()
│  ├─ email_sent = True
│  └─ assistant_response += confirmation details
└─ Response: Success! Order complete, confirmation sent
   └─ Workflow reaches END
```

## Test Case 2: Multi-Step Information Gathering

### Scenario
User provides information gradually, then completes purchase.

```
Message 1: "I need a birthday gift"
├─ extract_context()
│  ├─ occasion: "birthday"
│  ├─ age_group: None
│  └─ budget_range: None
├─ agent_reasoning()
│  ├─ Check: selected_product? NO
│  ├─ Check: has_occasion AND has_age AND has_budget? NO ✗
│  └─ next_action = CONTINUE_CONVERSATION ✓
├─ route_after_reasoning() → "gather_information"
├─ gather_information()
│  ├─ LLM generates question about age/budget
│  └─ assistant_response = "What age is the child? What's your budget?"
└─ Response: Question asked

────────────────────────────────────────────────────────────────────

Message 2: "For a 6-year-old"
├─ extract_context()
│  ├─ occasion: "birthday" (preserved)
│  ├─ age_group: "5-8" (new)
│  └─ budget_range: None (still missing)
├─ agent_reasoning()
│  ├─ Check: selected_product? NO
│  ├─ Check: has_occasion AND has_age AND has_budget? NO ✗ (missing budget)
│  └─ next_action = CONTINUE_CONVERSATION ✓
├─ route_after_reasoning() → "gather_information"
├─ gather_information()
│  ├─ LLM generates question about budget
│  └─ assistant_response = "What's your budget?"
└─ Response: Follow-up question

────────────────────────────────────────────────────────────────────

Message 3: "Under $50"
├─ extract_context()
│  ├─ occasion: "birthday" (preserved)
│  ├─ age_group: "5-8" (preserved)
│  └─ budget_range: "under $50" (new) ✓
├─ agent_reasoning()
│  ├─ Check: selected_product? NO
│  ├─ Check: has_occasion AND has_age AND has_budget? YES ✓✓✓
│  └─ next_action = RECOMMEND_PRODUCT ✓
├─ route_after_reasoning() → "recommend_product"
├─ recommend_product()
│  └─ [recommendation flow same as Test Case 1]
└─ Response: Product recommendation

[Then same as Messages 2-3 of Test Case 1...]
```

## Test Case 3: Payment Failure & Retry

### Scenario
User confirms payment, but it fails (5% probability), then retries.

```
Message 3: "Yes, process the payment" (same as test 1)
├─ ... same up to process_payment ...
├─ process_payment()
│  ├─ payment_processor.process_payment(order)
│  ├─ payment_successful = False (5% probability) ✗
│  ├─ payment_error = "Payment declined by bank"
│  ├─ assistant_response = error message
│  └─ order_status = PAYMENT_PROCESSING (unchanged)
├─ route_after_payment()
│  ├─ Check: payment_successful? NO
│  └─ Route to: END ✓
└─ Response: Error message shown

────────────────────────────────────────────────────────────────────

Message 4: "Try with different payment method"
├─ extract_context()
│  └─ (no new context)
├─ agent_reasoning()
│  ├─ Check: selected_product? YES
│  ├─ Check: confirmation_pending? YES - first condition FALSE
│  ├─ Check: current_order AND confirmation_pending? YES ✓
│  └─ next_action = PROCESS_PAYMENT ✓ (retries payment)
├─ process_payment()
│  ├─ payment_processor.process_payment(order) [retry]
│  ├─ payment_successful = True ✓ (or False again)
│  └─ [Continue with success flow...]
```

## Key State Transitions

| Current State | Condition | Next Action | Route |
|---|---|---|---|
| No product | Enough context | RECOMMEND_PRODUCT | → recommend_product |
| No product | Missing context | CONTINUE_CONVERSATION | → gather_information |
| Product selected | Not confirmed | SUMMARIZE_RECOMMENDATION | → summarize_recommendation |
| Order created | Confirmed | PROCESS_PAYMENT | → process_payment |
| Any | Default | CONTINUE_CONVERSATION | → gather_information |

## Verification Checklist

After running the application with these test cases:

- [ ] Message 1 with full context → immediately shows recommendation (no looping)
- [ ] Recommendation → clicking "buy" shows order summary
- [ ] Order summary → clicking "confirm" processes payment
- [ ] Payment success → shows confirmation and order complete
- [ ] Payment failure → shows error, can retry with same/different payment
- [ ] Multi-step gathering → properly accumulates context
- [ ] No "No order to process" errors (the original bug)
- [ ] Workflow never gets stuck in a loop
- [ ] State transitions are deterministic and predictable

## State Verification Script

After each user message, verify:

```python
# After message 1
assert state["conversation_context"]["occasion"] is not None
assert state["conversation_context"]["age_group"] is not None
assert state["conversation_context"]["budget_range"] is not None
assert state["selected_product"] is not None
assert state["confirmation_pending"] == False
assert state["current_order"] is None

# After message 2
assert state["confirmation_pending"] == True
assert state["current_order"] is not None
assert state["current_order"]["total_amount"] == 38.40

# After message 3
assert state["payment_successful"] == True
assert state["order_completed"] == True
assert state["email_sent"] == True
```

## Performance Expectations

- Message 1: ~2-3 seconds (LLM extract context + reasoning + product search)
- Message 2: ~2-3 seconds (LLM extract + reasoning + order creation)
- Message 3: ~1-2 seconds (LLM extract + reasoning + payment processing)

Total conversation: ~5-8 seconds from start to completed order.
