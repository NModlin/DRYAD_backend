import logging
import weaviate
import weaviate.classes as wvc
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Interface for Vector Database (Weaviate).
    """
    def __init__(self, url: str = "http://localhost:8080", api_key: Optional[str] = None):
        self.url = url
        self.client = None
        
        try:
             # Connect to Weaviate
            if api_key:
                auth_credentials = weaviate.auth.AuthApiKey(api_key)
            else:
                auth_credentials = None

            self.client = weaviate.connect_to_local(
                port=8080,
                grpc_port=50051 # Default gRPC port
            ) if "localhost" in url else weaviate.connect_to_custom(
                http_host=url.split(":")[0],
                http_port=int(url.split(":")[1]) if ":" in url else 80,
                http_secure=False,
                grpc_host=url.split(":")[0],
                grpc_port=50051,
                grpc_secure=False,
                auth_credentials=auth_credentials
            )

            # Check readiness?
            # self.client.is_ready() 
            # In v4 connect is immediate, but connection opens on use? 
            # Actually connect_to_local context manager is preferred but we need persistent client?
            # V4 client should be closed. We might need to wrap this properly.
            # For simplicity in this "Core" rebuild, we hold the client.

            logger.info("✅ Weaviate Client Initialized")
            
        except Exception as e:
            logger.warning(f"⚠️ Weaviate connection failed: {e}. Vector Store will be unavailable.")
            self.client = None

    def ensure_schema(self):
        """
        Create KnowledgeVessel collection if not exists.
        """
        if not self.client:
            return

        try:
            if not self.client.collections.exists("KnowledgeVessel"):
                self.client.collections.create(
                    name="KnowledgeVessel",
                    properties=[
                        wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                        wvc.config.Property(name="source", data_type=wvc.config.DataType.TEXT),
                        wvc.config.Property(name="vessel_id", data_type=wvc.config.DataType.UUID),
                    ],
                    # Configure vectorizer if we want Weaviate to embed, 
                    # or 'image' if multimodal. For now explicit user-provided vectors often safer
                    # or configure 'text2vec-openai' module if present in Weaviate.
                )
                logger.info("✅ KnowledgeVessel schema created.")
        except Exception as e:
             logger.error(f"Failed to ensure schema: {e}")

    def add_document(self, vessel_id: str, content: str, source: str = "unknown"):
        """
        Add a document to the index.
        """
        if not self.client:
            logger.warning("Vector store unavailable, skipping add_document")
            return

        try:
            collection = self.client.collections.get("KnowledgeVessel")
            collection.data.insert(
                properties={
                    "content": content,
                    "source": source,
                    "vessel_id": vessel_id
                }
            )
        except Exception as e:
            logger.error(f"Failed to add document: {e}")

    def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Semantic search.
        Requires Weaviate to have a Vectorizer module configured (e.g. text2vec-transformers or openai).
        """
        if not self.client:
            return []

        try:
            collection = self.client.collections.get("KnowledgeVessel")
            response = collection.query.near_text(
                query=query,
                limit=limit
            )
            
            return [
                {
                    "content": o.properties["content"],
                    "source": o.properties["source"],
                    "vessel_id": str(o.properties["vessel_id"])
                } 
                for o in response.objects
            ]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def close(self):
        if self.client:
            self.client.close()
