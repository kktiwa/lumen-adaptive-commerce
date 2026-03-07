"""Order management system for creating and tracking orders"""
from typing import List, Optional
from .agentic_types import (
    Order,
    OrderItem,
    OrderStatus,
    Product,
    ShippingAddress,
    PaymentMethod,
)
import uuid
from datetime import datetime


class OrderManager:
    """Manages order creation and tracking"""
    
    def __init__(self):
        """Initialize order manager"""
        self._orders: dict[str, Order] = {}
        self._TAX_RATE = 0.08  # 8% tax rate
        self._SHIPPING_COST = 10.0  # Flat shipping cost
    
    def create_order(
        self,
        user_id: str,
        product: Product,
        quantity: int,
        shipping_address: ShippingAddress,
        payment_method: PaymentMethod,
    ) -> Order:
        """Create a new order"""
        order_id = f"order_{uuid.uuid4().hex[:8]}"
        
        # Calculate order total
        subtotal = product["price"] * quantity
        tax = subtotal * self._TAX_RATE
        total = subtotal + tax + self._SHIPPING_COST
        
        order: Order = {
            "id": order_id,
            "user_id": user_id,
            "items": [
                {
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "quantity": quantity,
                    "unit_price": product["price"],
                    "subtotal": subtotal,
                }
            ],
            "total_amount": total,
            "status": OrderStatus.PENDING,
            "shipping_address": shipping_address,
            "payment_method": payment_method,
            "created_at": datetime.now(),
            "completed_at": None,
        }
        
        self._orders[order_id] = order
        return order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self._orders.get(order_id)
    
    def get_user_orders(self, user_id: str) -> List[Order]:
        """Get all orders for a user"""
        return [order for order in self._orders.values() if order["user_id"] == user_id]
    
    def update_order_status(self, order_id: str, status: OrderStatus) -> Optional[Order]:
        """Update order status"""
        order = self._orders.get(order_id)
        if not order:
            return None
        
        order["status"] = status
        
        # Set completion time if order is completed
        if status == OrderStatus.COMPLETED:
            order["completed_at"] = datetime.now()
        
        return order
    
    def get_order_summary(self, order: Order) -> str:
        """Get a human-readable summary of the order"""
        items_text = "\n".join([
            f"  - {item['product_name']} (Qty: {item['quantity']}) - ${item['unit_price']:.2f} each = ${item['subtotal']:.2f}"
            for item in order["items"]
        ])
        
        subtotal = sum(item["subtotal"] for item in order["items"])
        tax = subtotal * self._TAX_RATE
        
        summary = f"""
ORDER SUMMARY
=============
Order ID: {order['id']}

Items:
{items_text}

Subtotal: ${subtotal:.2f}
Tax (8%): ${tax:.2f}
Shipping: ${self._SHIPPING_COST:.2f}
TOTAL: ${order['total_amount']:.2f}

Shipping Address:
{order['shipping_address']['name']}
{order['shipping_address']['street']}
{order['shipping_address']['city']}, {order['shipping_address']['state']} {order['shipping_address']['zip_code']}
{order['shipping_address']['country']}

Payment Method:
{order['payment_method']['type'].replace('_', ' ').title()}
*** **** **** {order['payment_method']['last_four']}
"""
        return summary
