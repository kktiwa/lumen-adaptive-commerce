"""Payment processing system with mock implementation"""
from typing import Tuple, Optional
from .agentic_types import Order, PaymentMethod
import random


class PaymentProcessor:
    """Handles payment processing - mock implementation"""
    
    def __init__(self):
        """Initialize payment processor"""
        self._transaction_log: list[dict] = []
        self._success_rate = 0.95  # 95% success rate for demo
    
    def process_payment(self, order: Order) -> Tuple[bool, str, Optional[str]]:
        """
        Process payment for an order.
        
        Returns:
            Tuple of (success, message, transaction_id)
        """
        # Validate payment method
        if not order["payment_method"]:
            return False, "No payment method selected", None
        
        payment_method = order["payment_method"]
        
        # Simulate payment processing with high success rate
        if random.random() < self._success_rate:
            transaction_id = f"txn_{random.randint(100000, 999999)}"
            
            log_entry = {
                "transaction_id": transaction_id,
                "order_id": order["id"],
                "user_id": order["user_id"],
                "amount": order["total_amount"],
                "payment_method_id": payment_method["id"],
                "status": "success",
                "timestamp": order["created_at"],
            }
            self._transaction_log.append(log_entry)
            
            message = (
                f"Payment of ${order['total_amount']:.2f} processed successfully "
                f"using {payment_method['type'].replace('_', ' ').title()} ending in {payment_method['last_four']}. "
                f"Transaction ID: {transaction_id}"
            )
            return True, message, transaction_id
        else:
            # Simulate occasional payment failures
            reasons = [
                "Insufficient funds",
                "Payment declined by bank",
                "Invalid card number",
                "Card expired",
            ]
            error_reason = random.choice(reasons)
            
            log_entry = {
                "transaction_id": f"txn_{random.randint(100000, 999999)}",
                "order_id": order["id"],
                "user_id": order["user_id"],
                "amount": order["total_amount"],
                "payment_method_id": payment_method["id"],
                "status": "failed",
                "error_reason": error_reason,
                "timestamp": order["created_at"],
            }
            self._transaction_log.append(log_entry)
            
            return False, f"Payment failed: {error_reason}", None
    
    def refund_payment(self, transaction_id: str) -> Tuple[bool, str]:
        """Refund a previously processed payment"""
        # Find transaction
        transaction = None
        for txn in self._transaction_log:
            if txn["transaction_id"] == transaction_id:
                transaction = txn
                break
        
        if not transaction:
            return False, f"Transaction {transaction_id} not found"
        
        if transaction["status"] != "success":
            return False, f"Cannot refund transaction with status: {transaction['status']}"
        
        # Mark as refunded
        transaction["status"] = "refunded"
        refund_id = f"refund_{random.randint(100000, 999999)}"
        
        return True, f"Refund of ${transaction['amount']:.2f} processed. Refund ID: {refund_id}"
    
    def get_transaction_log(self) -> list[dict]:
        """Get transaction log for debugging/auditing"""
        return self._transaction_log.copy()
