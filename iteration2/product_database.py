"""Product database with vector embeddings using ChromaDB for semantic search"""
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from common.config import settings

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

class VectorProductDatabase:
    """Product database with vector embeddings for semantic search using LangChain Chroma"""
    
    def __init__(self, persist_dir: str = ".chroma_db"):
        """Initialize the vector database with LangChain Chroma wrapper"""
        self.persist_dir = persist_dir
        
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model="text-embedding-3-small"
        )
        
        # Initialize LangChain Chroma vectorstore
        self.vectorstore = Chroma(
            collection_name="products",
            embedding_function=self.embeddings,
            persist_directory=persist_dir
        )
        
        # Initialize database if empty
        if self.vectorstore._collection.count() == 0:
            self._initialize_products()
    
    def _initialize_products(self):
        """Load products into the vector database"""
        documents = []
        metadatas = []
        ids = []
        
        for product in PRODUCT_DATABASE:
            # Create focused document optimized for semantic embedding
            doc_text = f"{product['name']}. {product['description']} Features: {', '.join(product['features'])}. Best for: {', '.join(product['occasion'])}."
            
            documents.append(doc_text)
            
            # Store complete product data in metadata for direct retrieval
            metadata = {
                "id": product['id'],
                "name": product['name'],
                "category": product['category'],
                "price": float(product['price']),
                "age_range": product['age_range'],
                "description": product['description'],
                "features": json.dumps(product['features']),
                "occasion": json.dumps(product['occasion']),
                "educational": product['educational'],
                "eco_friendly": product['eco_friendly'],
            }
            metadatas.append(metadata)
            ids.append(product['id'])
        
        # Add documents to vectorstore
        self.vectorstore.add_documents(
            documents=[
                self._create_langchain_document(doc, meta, doc_id)
                for doc, meta, doc_id in zip(documents, metadatas, ids)
            ],
            ids=ids
        )
    
    @staticmethod
    def _create_langchain_document(content: str, metadata: Dict[str, Any], doc_id: str):
        """Create a LangChain Document object"""
        from langchain_core.documents import Document
        return Document(page_content=content, metadata=metadata)
    
    def similarity_search(
        self,
        query: str,
        max_price: Optional[float] = None,
        age_range: Optional[str] = None,
        educational: Optional[bool] = None,
        eco_friendly: Optional[bool] = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Similarity search for products using native ChromaDB similarity_search with metadata filters
        
        Args:
            query: Natural language search query
            max_price: Maximum price filter
            age_range: Age range filter
            educational: Filter for educational products
            eco_friendly: Filter for eco-friendly products
            top_k: Number of results to return (default 4 for optimal relevance)
            
        Returns:
            List of product dictionaries
        """
        
        # Build filter expression for metadata
        filter_conditions = []
        
        if max_price is not None:
            filter_conditions.append({"price": {"$lte": max_price}})
        
        if age_range is not None:
            filter_conditions.append({"age_range": {"$eq": age_range}})
        
        if educational is not None:
            filter_conditions.append({"educational": {"$eq": educational}})
        
        if eco_friendly is not None:
            filter_conditions.append({"eco_friendly": {"$eq": eco_friendly}})
        
        # Construct combined filter
        where_filter = None
        if filter_conditions:
            where_filter = filter_conditions[0] if len(filter_conditions) == 1 else {"$and": filter_conditions}
        
        # Use native similarity_search with filter
        docs = self.vectorstore.similarity_search(
            query=query,
            k=top_k,
            filter=where_filter
        )
        
        # Convert documents to product dictionaries using metadata
        products = []
        for doc in docs:
            product_dict = {
                "id": doc.metadata["id"],
                "name": doc.metadata["name"],
                "category": doc.metadata["category"],
                "price": doc.metadata["price"],
                "age_range": doc.metadata["age_range"],
                "description": doc.metadata["description"],
                "features": json.loads(doc.metadata["features"]),
                "occasion": json.loads(doc.metadata["occasion"]),
                "educational": doc.metadata["educational"],
                "eco_friendly": doc.metadata["eco_friendly"],
            }
            products.append(product_dict)
        
        return products


# Global instance
_db_instance = None

def get_product_db() -> VectorProductDatabase:
    """Get or create the vector product database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = VectorProductDatabase()
    return _db_instance

