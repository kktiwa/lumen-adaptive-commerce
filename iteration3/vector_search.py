"""Vector-based semantic search using ChromaDB and embeddings for products"""
import chromadb
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any, Optional
import json
import logging
import os

logger = logging.getLogger(__name__)

# Initialize ChromaDB client with persistent storage using new API
# Create chroma_data directory if it doesn't exist
os.makedirs("./chroma_data", exist_ok=True)

chroma_client = chromadb.PersistentClient(path="./chroma_data")

# Initialize embeddings using OpenAI
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Collection name for products
PRODUCTS_COLLECTION_NAME = "products"

# Global collection reference
_product_collection = None

# Initialize sentence-based text splitter
# Splits on sentences first, then paragraphs, then words if needed
_sentence_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    chunk_size=512,
    chunk_overlap=50,
    length_function=len,
)


def _split_text_into_sentences(text: str) -> List[str]:
    """
    Split text into sentence-based chunks using langchain_text_splitters.
    
    Args:
        text: Text to split into sentences
        
    Returns:
        List of sentence chunks
    """
    if not text or not text.strip():
        return []
    
    chunks = _sentence_splitter.split_text(text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def get_or_create_collection():
    """Get or create the products collection in ChromaDB"""
    global _product_collection
    if _product_collection is None:
        try:
            _product_collection = chroma_client.get_collection(
                name=PRODUCTS_COLLECTION_NAME
            )
        except Exception:
            # Collection doesn't exist, will be created on first product add
            _product_collection = chroma_client.create_collection(
                name=PRODUCTS_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
    return _product_collection


def initialize_product_embeddings(products: List[Dict[str, Any]]) -> None:
    """
    Initialize ChromaDB with product embeddings using sentence-based chunking.
    This should be called once at startup.
    
    Args:
        products: List of product dictionaries from product_database
    """
    collection = get_or_create_collection()
    
    # Check if collection already has products to avoid re-embedding
    if collection.count() > 0:
        logger.info(f"Product collection already has {collection.count()} products, skipping re-embedding")
        return
    
    logger.info(f"Initializing embeddings for {len(products)} products with sentence-based chunking...")
    
    for product in products:
        # Get product description and split into sentences
        description = product.get("description", "")
        sentence_chunks = _split_text_into_sentences(description) if description else []
        
        # If no chunks from description, create one from product summary
        if not sentence_chunks:
            sentence_chunks = [_create_product_embedding_text(product)]
        
        # Add each sentence chunk to the collection
        for idx, chunk in enumerate(sentence_chunks):
            chunk_id = f"{product['id']}_chunk_{idx}" if len(sentence_chunks) > 1 else product["id"]
            
            # Create metadata with product info and chunk info
            metadata = {
                "name": product.get("name", ""),
                "category": product.get("category", ""),
                "price": product.get("price", 0),
                "age_range": product.get("age_range", ""),
                "occasion": json.dumps(product.get("occasion", [])),
                "educational": str(product.get("educational", False)),
                "eco_friendly": str(product.get("eco_friendly", False)),
                "features": json.dumps(product.get("features", [])),
                "product_id": product["id"],
                "chunk_index": idx,
                "total_chunks": len(sentence_chunks),
            }
            
            collection.add(
                ids=[chunk_id],
                documents=[chunk],
                metadatas=[metadata],
            )
    
    logger.info(f"Loaded {len(products)} products with sentence-based chunking into ChromaDB")


def _create_product_embedding_text(product: Dict[str, Any]) -> str:
    """
    Create a rich text representation of a product for embedding.
    This combines multiple fields to create meaningful embeddings.
    """
    parts = [
        product.get("name", ""),
        product.get("category", ""),
        product.get("description", ""),
        " ".join(product.get("features", [])),
        " ".join(product.get("occasion", [])),
        f"Age range: {product.get('age_range', '')}",
        f"Price: ${product.get('price', 0)}",
    ]
    if product.get("educational"):
        parts.append("educational")
    if product.get("eco_friendly"):
        parts.append("eco-friendly sustainable")
    
    return " ".join(filter(None, parts))


def semantic_product_search(
    query: str,
    top_k: int = 10,
    budget_max: Optional[float] = None,
    age_group: Optional[str] = None,
    category: Optional[str] = None,
    educational: Optional[bool] = None,
    eco_friendly: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """
    Search for products using semantic similarity with sentence-based chunking.
    
    Args:
        query: Natural language query describing what the user wants
        top_k: Number of results to return
        budget_max: Maximum price filter
        age_group: Age range filter (e.g., "5-8", "8-10")
        category: Product category filter
        educational: Filter for educational products
        eco_friendly: Filter for eco-friendly products
    
    Returns:
        List of matching products with similarity scores
    """
    collection = get_or_create_collection()
    
    if collection.count() == 0:
        logger.warning("Product collection is empty. No products to search.")
        return []
    
    # Build metadata filter
    where_filter = None
    filters = []
    
    if budget_max is not None:
        filters.append({"price": {"$lte": budget_max}})
    
    if age_group:
        filters.append({"age_range": {"$eq": age_group}})
    
    if category:
        filters.append({"category": {"$eq": category}})
    
    if educational is not None:
        filters.append({"educational": {"$eq": str(educational)}})
    
    if eco_friendly is not None:
        filters.append({"eco_friendly": {"$eq": str(eco_friendly)}})
    
    # Combine filters with AND logic if multiple
    if len(filters) > 1:
        where_filter = {"$and": filters}
    elif filters:
        where_filter = filters[0]
    
    # Query the collection
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances", "embeddings"]
    )
    
    # Parse results and deduplicate by product_id (since we have multiple chunks per product)
    product_map = {}
    if results and results["ids"] and len(results["ids"]) > 0:
        for i, chunk_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0
            
            # Convert distance to similarity score (cosine distance: 0 = most similar)
            similarity_score = 1 - (distance / 2)  # Normalize to 0-1 range
            
            # Use product_id from metadata, fallback to chunk_id
            product_id = metadata.get("product_id", chunk_id.split("_chunk_")[0])
            
            # Keep the best scoring chunk for each product
            if product_id not in product_map or similarity_score > product_map[product_id]["similarity_score"]:
                product_map[product_id] = {
                    "id": product_id,
                    "name": metadata.get("name", ""),
                    "category": metadata.get("category", ""),
                    "price": int(metadata.get("price", 0)),
                    "age_range": metadata.get("age_range", ""),
                    "occasion": json.loads(metadata.get("occasion", "[]")),
                    "educational": metadata.get("educational", "False") == "True",
                    "eco_friendly": metadata.get("eco_friendly", "False") == "True",
                    "features": json.loads(metadata.get("features", "[]")),
                    "similarity_score": similarity_score,
                    "matching_sentence": results["documents"][0][i] if results["documents"] else "",
                }
    
    products = list(product_map.values())
    logger.info(f"Semantic search found {len(products)} products matching query: {query}")
    return products


def reindex_products(products: List[Dict[str, Any]]) -> None:
    """
    Reindex all products. Useful when product database changes.
    
    Args:
        products: List of product dictionaries
    """
    try:
        chroma_client.delete_collection(name=PRODUCTS_COLLECTION_NAME)
        global _product_collection
        _product_collection = None
        initialize_product_embeddings(products)
        logger.info("Product index reinitialized successfully")
    except Exception as e:
        logger.error(f"Error reindexing products: {e}")
