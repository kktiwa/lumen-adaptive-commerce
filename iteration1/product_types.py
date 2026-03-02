from typing import List, TypedDict

class UserProfile(TypedDict):
    budget: str
    style_preference: str
    interest: str

class Product(TypedDict):
    name: str
    category: str
    price: float
    features: List[str]