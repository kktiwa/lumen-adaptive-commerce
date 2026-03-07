"""User management system for handling profiles, addresses, and payment methods"""
from typing import List, Optional, Dict, Any
from .agentic_types import UserProfile, ShippingAddress, PaymentMethod
import uuid
from datetime import datetime


class UserManager:
    """Manages user profiles and related information"""
    
    def __init__(self):
        """Initialize user manager with sample data"""
        self._users: Dict[str, UserProfile] = {}
        self._initialize_sample_users()
    
    def _initialize_sample_users(self) -> None:
        """Initialize with sample user data"""
        # Sample user 1
        user1_id = "user_001"
        self._users[user1_id] = {
            "user_id": user1_id,
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "shipping_addresses": [
                {
                    "id": "addr_001",
                    "name": "Home",
                    "street": "123 Main Street",
                    "city": "San Francisco",
                    "state": "CA",
                    "zip_code": "94110",
                    "country": "USA",
                    "is_default": True,
                },
                {
                    "id": "addr_002",
                    "name": "Office",
                    "street": "456 Tech Boulevard",
                    "city": "Mountain View",
                    "state": "CA",
                    "zip_code": "94040",
                    "country": "USA",
                    "is_default": False,
                },
            ],
            "payment_methods": [
                {
                    "id": "pm_001",
                    "type": "credit_card",
                    "last_four": "4242",
                    "cardholder_name": "Alice Johnson",
                    "expiry_date": "12/25",
                    "is_default": True,
                },
                {
                    "id": "pm_002",
                    "type": "debit_card",
                    "last_four": "5678",
                    "cardholder_name": "Alice Johnson",
                    "expiry_date": "06/26",
                    "is_default": False,
                },
            ],
            "preferences": {
                "notification_email": True,
                "marketing_emails": False,
                "preferred_gift_types": ["educational", "outdoor"],
            },
        }
        
        # Sample user 2
        user2_id = "user_002"
        self._users[user2_id] = {
            "user_id": user2_id,
            "name": "Bob Smith",
            "email": "bob@example.com",
            "shipping_addresses": [
                {
                    "id": "addr_003",
                    "name": "Home",
                    "street": "789 Oak Lane",
                    "city": "Seattle",
                    "state": "WA",
                    "zip_code": "98101",
                    "country": "USA",
                    "is_default": True,
                },
            ],
            "payment_methods": [
                {
                    "id": "pm_003",
                    "type": "credit_card",
                    "last_four": "3333",
                    "cardholder_name": "Bob Smith",
                    "expiry_date": "09/24",
                    "is_default": True,
                },
            ],
            "preferences": {
                "notification_email": True,
                "marketing_emails": True,
                "preferred_gift_types": ["sports", "educational"],
            },
        }
    
    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID"""
        return self._users.get(user_id)
    
    def create_user(self, name: str, email: str) -> UserProfile:
        """Create a new user"""
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        user: UserProfile = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "shipping_addresses": [],
            "payment_methods": [],
            "preferences": {},
        }
        self._users[user_id] = user
        return user
    
    def add_shipping_address(
        self,
        user_id: str,
        name: str,
        street: str,
        city: str,
        state: str,
        zip_code: str,
        country: str = "USA",
        is_default: bool = False,
    ) -> Optional[ShippingAddress]:
        """Add a shipping address to user's profile"""
        user = self._users.get(user_id)
        if not user:
            return None
        
        # If marking as default, unset other defaults
        if is_default:
            for addr in user["shipping_addresses"]:
                addr["is_default"] = False
        
        address: ShippingAddress = {
            "id": f"addr_{uuid.uuid4().hex[:8]}",
            "name": name,
            "street": street,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "country": country,
            "is_default": is_default or len(user["shipping_addresses"]) == 0,
        }
        user["shipping_addresses"].append(address)
        return address
    
    def add_payment_method(
        self,
        user_id: str,
        payment_type: str,
        last_four: str,
        cardholder_name: Optional[str] = None,
        expiry_date: Optional[str] = None,
        is_default: bool = False,
    ) -> Optional[PaymentMethod]:
        """Add a payment method to user's profile"""
        user = self._users.get(user_id)
        if not user:
            return None
        
        # If marking as default, unset other defaults
        if is_default:
            for pm in user["payment_methods"]:
                pm["is_default"] = False
        
        payment_method: PaymentMethod = {
            "id": f"pm_{uuid.uuid4().hex[:8]}",
            "type": payment_type,
            "last_four": last_four,
            "cardholder_name": cardholder_name,
            "expiry_date": expiry_date,
            "is_default": is_default or len(user["payment_methods"]) == 0,
        }
        user["payment_methods"].append(payment_method)
        return payment_method
    
    def get_default_shipping_address(self, user_id: str) -> Optional[ShippingAddress]:
        """Get the default shipping address"""
        user = self._users.get(user_id)
        if not user:
            return None
        
        for address in user["shipping_addresses"]:
            if address["is_default"]:
                return address
        
        # Return first address if no default is set
        return user["shipping_addresses"][0] if user["shipping_addresses"] else None
    
    def get_default_payment_method(self, user_id: str) -> Optional[PaymentMethod]:
        """Get the default payment method"""
        user = self._users.get(user_id)
        if not user:
            return None
        
        for pm in user["payment_methods"]:
            if pm["is_default"]:
                return pm
        
        # Return first payment method if no default is set
        return user["payment_methods"][0] if user["payment_methods"] else None
    
    def get_alternate_shipping_addresses(self, user_id: str) -> List[ShippingAddress]:
        """Get all non-default shipping addresses"""
        user = self._users.get(user_id)
        if not user:
            return []
        
        return [addr for addr in user["shipping_addresses"] if not addr["is_default"]]
    
    def get_alternate_payment_methods(self, user_id: str) -> List[PaymentMethod]:
        """Get all non-default payment methods"""
        user = self._users.get(user_id)
        if not user:
            return []
        
        return [pm for pm in user["payment_methods"] if not pm["is_default"]]
