"""Agent tools - actions the autonomous agent can take"""
from typing import List, Dict, Any, Optional
from .agentic_types import Product
from .product_database import get_product_db, initialize_vector_search
from .vector_search import semantic_product_search
from langchain_core.tools import tool
import json
import logging

logger = logging.getLogger(__name__)


@tool
def search_products_by_criteria(
    occasion: Optional[str] = None,
    age_group: Optional[str] = None,
    budget_max: Optional[float] = None,
    features: Optional[List[str]] = None,
    educational: Optional[bool] = None,
    eco_friendly: Optional[bool] = None,
) -> List[Product]:
    """
    Search for products using semantic similarity.
    
    Args:
        occasion: Type of occasion (e.g., 'birthday party', 'outdoor play')
        age_group: Age range (e.g., '5-7', '8-10', '5-12')
        budget_max: Maximum price in dollars
        features: List of features to filter by
        educational: Filter for educational products
        eco_friendly: Filter for eco-friendly products
    
    Returns:
        List of matching products ranked by relevance
    """
    # Initialize vector search on first use
    initialize_vector_search()
    
    # Build a semantic query from the criteria
    query_parts = []
    
    if occasion:
        query_parts.append(f"for {occasion}")
    
    if age_group:
        query_parts.append(f"age {age_group}")
    
    if budget_max:
        query_parts.append(f"budget under ${budget_max}")
    
    if features:
        query_parts.append(f"with features: {', '.join(features)}")
    
    if educational is True:
        query_parts.append("educational")
    
    if eco_friendly is True:
        query_parts.append("eco-friendly sustainable")
    
    query = "Find toys " + " ".join(query_parts) if query_parts else "Find great toys"
    
    logger.info(f"Semantic search query: {query}")
    
    # Use semantic search with filters
    results = semantic_product_search(
        query=query,
        top_k=10,
        budget_max=budget_max,
        age_group=age_group,
        category=None,  # We rely on semantic search for category matching
        educational=educational,
        eco_friendly=eco_friendly,
    )
    
    # Filter by features if specified (post-filter semantic results)
    if features:
        filtered_results = []
        for product in results:
            product_features = set(product.get("features", []))
            if any(f.lower() in [pf.lower() for pf in product_features] for f in features):
                filtered_results.append(product)
        results = filtered_results
    
    return results


@tool
def get_product_details(product_id: str) -> Optional[Product]:
    """
    Get detailed information about a specific product.
    
    Args:
        product_id: The product ID
    
    Returns:
        Product details or None if not found
    """
    db = get_product_db()
    for product in db:
        if product.get("id") == product_id:
            return product
    
    return None


@tool
def get_all_products() -> List[Product]:
    """Get all available products."""
    return get_product_db()


@tool
def compare_products(product_ids: List[str]) -> Dict[str, Any]:
    """
    Compare multiple products side by side.
    
    Args:
        product_ids: List of product IDs to compare
    
    Returns:
        Comparison data
    """
    db = get_product_db()
    products = []
    
    for product_id in product_ids:
        for product in db:
            if product.get("id") == product_id:
                products.append(product)
                break
    
    comparison = {
        "products": products,
        "price_range": {
            "min": min(p.get("price", 0) for p in products),
            "max": max(p.get("price", 0) for p in products),
        },
        "common_features": list(set.intersection(*[
            set(p.get("features", [])) for p in products
        ])) if products else [],
    }
    
    return comparison


# Define the tools list for the agent
AGENT_TOOLS = [
    search_products_by_criteria,
    get_product_details,
    get_all_products,
    compare_products,
]
