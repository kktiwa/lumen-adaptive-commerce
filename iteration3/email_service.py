"""Email service for order notifications"""
from typing import Optional, Tuple
from .agentic_types import Order, UserProfile
from datetime import datetime


class EmailService:
    """Handles email notifications - mock implementation"""
    
    def __init__(self):
        """Initialize email service"""
        self._sent_emails: list[dict] = []
    
    def send_order_confirmation_email(
        self,
        user_profile: UserProfile,
        order: Order,
    ) -> Tuple[bool, str]:
        """Send order confirmation email to customer"""
        email_address = user_profile["email"]
        
        # Prepare email content
        items_text = "\n".join([
            f"  - {item['product_name']} (Qty: {item['quantity']}) - ${item['subtotal']:.2f}"
            for item in order["items"]
        ])
        
        shipping_addr = order["shipping_address"]
        payment_method = order["payment_method"]
        
        email_body = f"""
Dear {user_profile['name']},

Thank you for your order! Here are your order details:

Order ID: {order['id']}
Order Date: {order['created_at'].strftime('%Y-%m-%d %H:%M:%S')}

ITEMS ORDERED:
{items_text}

ORDER TOTAL: ${order['total_amount']:.2f}

SHIPPING ADDRESS:
{shipping_addr['name']}
{shipping_addr['street']}
{shipping_addr['city']}, {shipping_addr['state']} {shipping_addr['zip_code']}
{shipping_addr['country']}

PAYMENT METHOD:
{payment_method['type'].replace('_', ' ').title()}
ending in {payment_method['last_four']}

Your order is being processed and will be shipped soon. You'll receive a tracking number via email once it ships.

If you have any questions, please don't hesitate to contact our customer service team.

Thank you for shopping with us!

Best regards,
Adaptive Commerce Team
"""
        
        email_record = {
            "to": email_address,
            "subject": f"Order Confirmation - {order['id']}",
            "body": email_body,
            "sent_at": datetime.now(),
            "status": "sent",
        }
        
        self._sent_emails.append(email_record)
        
        return True, f"Order confirmation email sent to {email_address}"
    
    def send_shipping_notification_email(
        self,
        user_profile: UserProfile,
        order: Order,
        tracking_number: str,
    ) -> Tuple[bool, str]:
        """Send shipping notification email with tracking info"""
        email_address = user_profile["email"]
        
        email_body = f"""
Dear {user_profile['name']},

Your order has shipped! Here's your tracking information:

Order ID: {order['id']}
Tracking Number: {tracking_number}
Expected Delivery: In 3-5 business days

You can track your order at: https://tracking.example.com/{tracking_number}

Thank you for your patience!

Best regards,
Adaptive Commerce Team
"""
        
        email_record = {
            "to": email_address,
            "subject": f"Your order {order['id']} has shipped!",
            "body": email_body,
            "sent_at": datetime.now(),
            "status": "sent",
        }
        
        self._sent_emails.append(email_record)
        
        return True, f"Shipping notification email sent to {email_address}"
    
    def get_sent_emails(self) -> list[dict]:
        """Get log of all sent emails"""
        return self._sent_emails.copy()
