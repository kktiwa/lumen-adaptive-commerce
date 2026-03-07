"""Prompts for autonomous agentic workflow"""
from typing import Dict, Any, List, Optional
from .agentic_types import ConversationContext, Product, Order, ShippingAddress, PaymentMethod


def get_system_prompt() -> str:
    """Get the system prompt for the autonomous shopping agent"""
    return """You are an autonomous shopping agent with the goal of helping customers find the perfect product and complete their purchase. You are professional, friendly, and helpful.

Your responsibilities:
1. Understand the customer's needs through conversation
2. Ask clarifying questions about occasion, age group, budget, and preferences
3. Recommend appropriate products based on their needs
4. Guide them toward a decision when they've found a good match
5. Help them complete their order by confirming shipping and payment details
6. Process the payment and complete the order

You have access to tools for searching and comparing products. Use them strategically to find the best matches.

When recommending products:
- Always explain why you think this product is a good fit
- Be specific about features and benefits
- If they want alternatives, search for different options

When moving to checkout:
- Summarize the product they've selected
- Show their default shipping address and payment method
- Offer them the option to select different addresses or payment methods
- Only proceed to payment after they confirm details

Always be conversational and natural. If a customer seems uncertain, ask more questions rather than pushing for a decision.

Current approach: Guide the customer step-by-step toward completing a purchase by understanding their needs, recommending products, and facilitating checkout."""


def get_initial_greeting() -> str:
    """Get initial greeting for new conversation"""
    return """Hello! Welcome to Adaptive Commerce. I'm here to help you find the perfect product for your needs. 

Let me start by understanding what you're looking for. Could you tell me:
1. What's the occasion? (e.g., birthday, gift, party, casual shopping)
2. Roughly what age group is this for?
3. What's your budget range?

Feel free to share any other details about what you're looking for!"""


def get_recommendation_prompt(
    conversation_context: ConversationContext,
    conversation_history: List[Dict[str, str]],
) -> str:
    """
    Get prompt for agent to decide on next action and reasoning
    
    Args:
        conversation_context: Extracted context from conversation
        conversation_history: Recent conversation history
    
    Returns:
        Prompt for agent reasoning
    """
    
    context_summary = f"""
CUSTOMER CONTEXT EXTRACTED SO FAR:
- Occasion: {conversation_context.get('occasion') or 'Not mentioned yet'}
- Age Group: {conversation_context.get('age_group') or 'Not mentioned yet'}
- Budget Range: {conversation_context.get('budget_range') or 'Not mentioned yet'}
- Quantity Needed: {conversation_context.get('quantity_needed') or '1'}
- Specific Needs: {', '.join(conversation_context.get('specific_needs', [])) or 'None specified'}
- Preferred Features: {', '.join(conversation_context.get('preferred_features', [])) or 'None specified'}

RECENT CONVERSATION:
"""
    
    # Add last few messages
    for msg in conversation_history[-6:]:
        context_summary += f"{msg['role'].upper()}: {msg['content']}\n"
    
    context_summary += """
NEXT STEPS:
Based on the conversation so far, determine what action to take next:

1. If you need more information to make a good recommendation, ask clarifying questions
2. If you have enough context, search for appropriate products using the search_products_by_criteria tool
3. If you've already found products and the customer needs more details, use get_product_details
4. If the customer wants to compare options, use compare_products
5. If the customer seems ready to buy, summarize the selected product and ask them to proceed to checkout
6. Once they confirm, retrieve their default shipping address and payment method for final confirmation

Always explain your reasoning before taking action. Be helpful and conversational."""
    
    return context_summary


def get_product_recommendation_message(product: Product, quantity: int = 1) -> str:
    """Format a product recommendation message"""
    return f"""Based on your needs, I'd like to recommend:

**{product['name']}**
Price: ${product['price']:.2f}
Category: {product['category']}
Age Range: {product['age_range']}

Description: {product['description']}

Key Features:
{chr(10).join([f"• {feature}" for feature in product['features']])}

Why this is a great fit for you:
- {'✓ Educational content' if product['educational'] else 'Great for entertainment'}
- {'✓ Eco-friendly' if product['eco_friendly'] else 'Popular option'}
- {'✓ Great for your budget' if product['price'] <= 50 else '✓ Premium quality'}

Would you like to know more about this product, see similar options, or proceed with this selection?"""


def get_order_summary_prompt(order: Order, user_name: str) -> str:
    """Get prompt to summarize order before payment"""
    items_text = "\n".join([
        f"• {item['product_name']} (Qty: {item['quantity']}) - ${item['unit_price']:.2f} each"
        for item in order["items"]
    ])
    
    shipping_addr = order["shipping_address"]
    payment_method = order["payment_method"]
    
    return f"""Hi {user_name}! Let me confirm your order details:

**ITEMS:**
{items_text}

**SHIPPING TO:**
{shipping_addr['name']}
{shipping_addr['street']}
{shipping_addr['city']}, {shipping_addr['state']} {shipping_addr['zip_code']}

**PAYMENT METHOD:**
{payment_method['type'].replace('_', ' ').title()} ending in {payment_method['last_four']}

**ORDER TOTAL:** ${order['total_amount']:.2f}

Would you like to change your shipping address or payment method, or shall I proceed with this payment?"""


def get_payment_alternatives_prompt(
    user_name: str,
    alternate_addresses: List[ShippingAddress],
    alternate_payment_methods: List[PaymentMethod],
) -> str:
    """Get prompt offering alternative payment and shipping options"""
    
    prompt = f"""Great! Before we process payment, I can offer you some alternatives:\n"""
    
    if alternate_addresses:
        prompt += "\n**OTHER SHIPPING ADDRESSES:**\n"
        for addr in alternate_addresses:
            prompt += f"• {addr['name']} - {addr['city']}, {addr['state']}\n"
        prompt += "\n"
    
    if alternate_payment_methods:
        prompt += "**OTHER PAYMENT METHODS:**\n"
        for pm in alternate_payment_methods:
            prompt += f"• {pm['type'].replace('_', ' ').title()} ending in {pm['last_four']}\n"
        prompt += "\n"
    
    prompt += """Would you like to use one of these alternatives, or should I proceed with your defaults?"""
    
    return prompt


def get_payment_success_prompt(transaction_id: str) -> str:
    """Get message for successful payment"""
    return f"""🎉 **Payment Successful!**

Your payment has been processed successfully.
Transaction ID: {transaction_id}

Your order is now being prepared for shipment. You'll receive a tracking number via email shortly.

Thank you for your purchase! Is there anything else I can help you with today?"""


def get_payment_failure_prompt(error_message: str) -> str:
    """Get message for failed payment"""
    return f"""❌ **Payment Failed**

Unfortunately, your payment could not be processed:
{error_message}

Would you like to:
1. Try again with the same payment method
2. Use a different payment method
3. Cancel this order

Please let me know how you'd like to proceed."""
