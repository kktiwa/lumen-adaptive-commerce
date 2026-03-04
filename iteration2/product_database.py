"""Sample product database for recommendations"""
from typing import List, Dict, Any

PRODUCT_DATABASE = [
    {
        "id": "prod_001",
        "name": "Superhero Cape & Mask Set",
        "category": "costumes",
        "price": 25,
        "age_range": "5-8",
        "occasion": ["birthday party", "costume party", "outdoor play"],
        "features": ["comfortable", "washable", "vibrant colors"],
        "educational": False,
        "eco_friendly": False,
    },
    {
        "id": "prod_002",
        "name": "STEM Building Robot Kit",
        "category": "educational toys",
        "price": 45,
        "age_range": "5-10",
        "occasion": ["birthday"],
        "features": ["educational", "interactive", "batteries included"],
        "educational": True,
        "eco_friendly": False,
    },
    {
        "id": "prod_003",
        "name": "Outdoor Scavenger Hunt Pack",
        "category": "outdoor games",
        "price": 30,
        "age_range": "5-12",
        "occasion": ["birthday party", "outdoor play", "family gathering"],
        "features": ["group activity", "eco-friendly", "reusable"],
        "educational": True,
        "eco_friendly": True,
    },
    {
        "id": "prod_004",
        "name": "Deluxe Art & Craft Supply Box",
        "category": "arts and crafts",
        "price": 55,
        "age_range": "5-12",
        "occasion": ["birthday", "rainy day activity"],
        "features": ["100+ pieces", "non-toxic", "organized storage"],
        "educational": True,
        "eco_friendly": False,
    },
    {
        "id": "prod_005",
        "name": "Eco-friendly Bamboo Toy Set",
        "category": "sustainable toys",
        "price": 40,
        "age_range": "3-8",
        "occasion": ["birthday", "eco-conscious gift"],
        "features": ["biodegradable", "natural materials", "safe for kids"],
        "educational": False,
        "eco_friendly": True,
    },
    {
        "id": "prod_006",
        "name": "Premium Sports Equipment Bundle",
        "category": "sports",
        "price": 120,
        "age_range": "5-12",
        "occasion": ["birthday", "outdoor activities"],
        "features": ["durable", "professional grade", "multiple sports"],
        "educational": False,
        "eco_friendly": False,
    },
    {
        "id": "prod_007",
        "name": "Budget Party Game Pack (24 pieces)",
        "category": "party games",
        "price": 35,
        "age_range": "5-10",
        "occasion": ["birthday party"],
        "features": ["group entertainment", "party favor set", "multiple games"],
        "educational": False,
        "eco_friendly": False,
    },
    {
        "id": "prod_008",
        "name": "Interactive Learning Tablet",
        "category": "educational tech",
        "price": 180,
        "age_range": "5-12",
        "occasion": ["birthday", "long-term learning"],
        "features": ["educational apps", "interactive content", "parental controls"],
        "educational": True,
        "eco_friendly": False,
    },
]

def search_products(
    occasion: str = None,
    age_range: str = None,
    max_price: float = None,
    educational: bool = None,
    eco_friendly: bool = None,
    category: str = None,
) -> List[Dict[str, Any]]:
    """
    Search products based on criteria
    Returns filtered list of products
    """
    results = PRODUCT_DATABASE.copy()
    
    # Filter by occasion
    if occasion:
        results = [p for p in results if occasion.lower() in [o.lower() for o in p["occasion"]]]
    
    # Filter by age range (simple check)
    if age_range:
        results = [p for p in results if age_range.lower() in p["age_range"].lower()]
    
    # Filter by max price
    if max_price:
        results = [p for p in results if p["price"] <= max_price]
    
    # Filter by educational
    if educational is not None:
        results = [p for p in results if p["educational"] == educational]
    
    # Filter by eco-friendly
    if eco_friendly is not None:
        results = [p for p in results if p["eco_friendly"] == eco_friendly]
    
    # Filter by category
    if category:
        results = [p for p in results if category.lower() in p["category"].lower()]
    
    return results

def get_product_by_id(product_id: str) -> Dict[str, Any]:
    """Get a specific product by ID"""
    for product in PRODUCT_DATABASE:
        if product["id"] == product_id:
            return product
    return None
