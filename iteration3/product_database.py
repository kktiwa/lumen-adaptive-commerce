"""Product database for iteration3"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Product database
PRODUCT_DATABASE = [
    {
        "id": "prod_001",
        "name": "Superhero Cape & Mask Set",
        "category": "costumes",
        "price": 25,
        "age_range": "5-8",
        "occasion": ["birthday party", "costume party", "outdoor play"],
        "features": ["comfortable", "washable", "vibrant colors"],
        "description": "Transform kids into superheroes with this colorful cape and mask set. Perfect for birthday parties and imaginative play.",
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
        "description": "Build and program your own robot! Interactive STEM learning kit with easy assembly and multiple programming modes.",
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
        "description": "Get kids outdoors with this complete scavenger hunt kit including maps, scorecards, and exciting challenges for groups.",
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
        "description": "Comprehensive art supplies including markers, colored pencils, paints, and specialty materials for creative projects.",
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
        "description": "Beautiful bamboo toys made from sustainable materials. Perfect for eco-conscious families who care about the environment.",
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
        "description": "Complete sports bundle including soccer ball, basketball, badminton set, and more for active kids. Professional quality gear.",
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
        "description": "24-piece party game collection perfect for birthday celebrations. Games, activities, and entertainment for groups of kids.",
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
        "description": "Advanced learning device with curated educational apps, age-appropriate content, and built-in parental controls.",
        "educational": True,
        "eco_friendly": False,
    },
]


def get_product_db() -> List[Dict[str, Any]]:
    """Get the product database"""
    return PRODUCT_DATABASE


def get_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """Get a product by ID"""
    for product in PRODUCT_DATABASE:
        if product["id"] == product_id:
            return product
    return None


# Vector search initialization (lazy-loaded on first use)
_vector_search_initialized = False


def initialize_vector_search() -> None:
    """
    Initialize the vector search/embedding index for products.
    This should be called once at application startup.
    """
    global _vector_search_initialized
    
    if _vector_search_initialized:
        logger.info("Vector search already initialized")
        return
    
    try:
        from .vector_search import initialize_product_embeddings
        initialize_product_embeddings(PRODUCT_DATABASE)
        _vector_search_initialized = True
        logger.info("Product embeddings initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing product embeddings: {e}")
        _vector_search_initialized = False
