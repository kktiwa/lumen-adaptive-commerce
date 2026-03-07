"""Test script to verify vector search and semantic product matching"""
import logging
from iteration3.product_database import get_product_db, initialize_vector_search
from iteration3.vector_search import semantic_product_search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vector_search():
    """Test vector search functionality"""
    print("\n" + "="*80)
    print("Testing Vector Search for Products")
    print("="*80 + "\n")
    
    # Initialize vector search
    print("1. Initializing vector search with products...")
    try:
        initialize_vector_search()
        print("   ✓ Vector search initialized successfully\n")
    except Exception as e:
        print(f"   ✗ Error initializing vector search: {e}\n")
        return False
    
    # Test semantic search queries
    test_queries = [
        ("toys for 8 year old birthday under $50", {"age_group": "5-10", "budget_max": 50}),
        ("educational toys for kids", {"educational": True}),
        ("eco-friendly sustainable toys", {"eco_friendly": True}),
        ("outdoor games for parties", {}),
        ("arts and crafts supplies", {}),
    ]
    
    print("2. Testing semantic search queries:\n")
    
    for query, filters in test_queries:
        print(f"   Query: '{query}'")
        print(f"   Filters: {filters if filters else 'None'}")
        
        try:
            results = semantic_product_search(
                query=query,
                top_k=3,
                **filters
            )
            
            if results:
                print(f"   Found {len(results)} products:")
                for i, product in enumerate(results, 1):
                    similarity = product.get("similarity_score", 0)
                    print(f"      {i}. {product.get('name')} (${product.get('price')}) - Similarity: {similarity:.2f}")
            else:
                print(f"   No products found")
            print()
        except Exception as e:
            print(f"   ✗ Error searching: {e}\n")
            return False
    
    print("="*80)
    print("✓ Vector search tests completed successfully!")
    print("="*80)
    return True

if __name__ == "__main__":
    success = test_vector_search()
    exit(0 if success else 1)
