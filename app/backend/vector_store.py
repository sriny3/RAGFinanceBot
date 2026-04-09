"""
Vector store module for Qdrant integration.
Handles embedding generation, storage, and retrieval from Qdrant.
"""

import logging
import os
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, HasIdCondition
from sentence_transformers import SentenceTransformer
from metadata_schema import Chunk
from config import QDRANT_CONFIG, LLM_CONFIG

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Manages embeddings and vector storage in Qdrant.
    Handles both in-memory and network-based Qdrant instances.
    """
    
    def __init__(self):
        """Initialize vector store client."""
        self.client = self._init_qdrant_client()
        # Using sentence-transformers for embeddings (all-MiniLM-L6-v2)
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.vector_size = 384  # all-MiniLM-L6-v2 produces 384-dimensional vectors
    
    def _init_qdrant_client(self) -> QdrantClient:
        """
        Initialize Qdrant client based on configuration.
        
        Returns:
            QdrantClient instance
        """
        mode = QDRANT_CONFIG.get("mode", "memory")
        
        try:
            if mode == "memory":
                # In-memory Qdrant for development
                logger.info("Initializing Qdrant in-memory mode")
                return QdrantClient(":memory:")
            
            elif mode == "local":
                # Local persistent storage
                path = QDRANT_CONFIG.get("path", "qdrant_storage")
                logger.info(f"Initializing Qdrant in local persistent mode at: {path}")
                # Ensure directory exists
                os.makedirs(path, exist_ok=True)
                return QdrantClient(path=path)
            
            elif mode == "url":
                # Network Qdrant
                url = QDRANT_CONFIG.get("url", "localhost:6333")
                api_key = QDRANT_CONFIG.get("api_key")
                logger.info(f"Initializing Qdrant with URL: {url}")
                return QdrantClient(
                    url=url,
                    api_key=api_key,
                    timeout=30,
                )
            
            else:
                logger.warning(f"Unknown Qdrant mode: {mode}, defaulting to memory")
                return QdrantClient(":memory:")
        
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {str(e)}")
            # Fallback to memory mode
            return QdrantClient(":memory:")
    
    def create_collection(self, collection_name: str, vector_size: int = None) -> bool:
        """
        Create a collection in Qdrant.
        
        Args:
            collection_name: Name of the collection
            vector_size: Size of vectors (default from config)
            
        Returns:
            True if successful, False otherwise
        """
        if vector_size is None:
            vector_size = self.vector_size
        
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            if any(c.name == collection_name for c in collections.collections):
                logger.info(f"Collection '{collection_name}' already exists")
                return True
            
            # Create new collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info(f"Created collection: {collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {str(e)}")
            return False
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using SentenceTransformer.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if error
        """
        try:
            # Truncate if too long (max ~512 tokens for sentence-transformers)
            if len(text) > 30000:
                text = text[:30000]
            
            embedding = self.embedding_model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        
        except Exception as e:
            logger.error(f"Error generating embedding with SentenceTransformer: {str(e)}")
            return None
    
    def store_chunks(
        self,
        chunks: List[Chunk],
        collection_name: str,
    ) -> bool:
        """
        Store chunks with embeddings in Qdrant.
        
        Args:
            chunks: List of Chunk objects
            collection_name: Target collection name
            
        Returns:
            True if successful
        """
        try:
            # Ensure collection exists
            if not self.create_collection(collection_name):
                logger.error(f"Failed to create collection {collection_name}")
                return False
            
            # Generate embeddings and prepare points
            points = []
            
            for chunk in chunks:
                # Generate embedding
                embedding = self.embed_text(chunk.text)
                if not embedding:
                    logger.warning(f"Failed to embed chunk {chunk.id}")
                    continue
                
                # Create point with metadata payload
                point = PointStruct(
                    id=self._hash_id(chunk.id),
                    vector=embedding,
                    payload=chunk.to_qdrant_payload(),
                )
                points.append(point)
            
            if not points:
                logger.warning(f"No points to store in {collection_name}")
                return True
            
            # Upload points to Qdrant
            self.client.upsert(
                collection_name=collection_name,
                points=points,
            )
            
            logger.info(f"Stored {len(points)} chunks in collection {collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing chunks in {collection_name}: {str(e)}")
            return False
    
    def search_with_filter(
        self,
        collection_name: str,
        query_embedding: List[float],
        access_roles: List[str],
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> List[dict]:
        """
        Search collection with RBAC filter.
        CRITICAL: This ensures only chunks accessible to the user are returned.
        
        Args:
            collection_name: Collection to search
            query_embedding: Query embedding vector
            access_roles: Roles the user has (determines what they can access)
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of matching chunks with metadata
        """
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchAny
            
            # Build native Qdrant RBAC filter
            # Checks if chunk's access_roles field contains any of the user's roles
            rbac_filter = Filter(
                must=[
                    FieldCondition(
                        key="access_roles",
                        match=MatchAny(any=access_roles)
                    )
                ]
            )
            
            # qdrant-client >= 1.14 uses query_points; legacy .search() was removed.
            query_response = self.client.query_points(
                collection_name=collection_name,
                query=query_embedding,
                query_filter=rbac_filter,
                limit=top_k,
                score_threshold=score_threshold,
                with_payload=True,
            )
            results = getattr(query_response, "points", None) or []

            filtered_results = []
            for scored_point in results:
                payload = scored_point.payload or {}
                filtered_results.append({
                    "id": scored_point.id,
                    "score": scored_point.score,
                    "source_document": payload.get("source_document", "unknown"),
                    "collection": payload.get("collection", "unknown"),
                    "access_roles": payload.get("access_roles", []),
                    "section_title": payload.get("section_title", ""),
                    "subsection_title": payload.get("subsection_title", ""),
                    "page_number": payload.get("page_number", 0),
                    "chunk_type": payload.get("chunk_type", "text"),
                    "text": payload.get("text", ""),
                    "parent_chunk_id": payload.get("parent_chunk_id", ""),
                    "parent_summary": payload.get("parent_summary", ""),
                })
            
            logger.info(
                f"Retrieved {len(filtered_results)} chunks from {collection_name} "
                f"after RBAC filtering (user roles: {access_roles})"
            )
            
            return filtered_results[:top_k]
        
        except Exception as e:
            logger.error(f"Error searching collection {collection_name}: {str(e)}")
            return []
    
    def search_by_text(
        self,
        collection_name: str,
        query_text: str,
        access_roles: List[str],
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> List[dict]:
        """
        Search by text query (convenience wrapper).
        
        Args:
            collection_name: Collection to search
            query_text: Query text
            access_roles: User's accessible roles
            top_k: Number of results
            score_threshold: Minimum score
            
        Returns:
            List of matching chunks
        """
        # Embed query
        query_embedding = self.embed_text(query_text)
        if not query_embedding:
            logger.error("Failed to embed query")
            return []
        
        # Search with RBAC filter
        return self.search_with_filter(
            collection_name=collection_name,
            query_embedding=query_embedding,
            access_roles=access_roles,
            top_k=top_k,
            score_threshold=score_threshold,
        )
    
    def list_collections(self) -> List[str]:
        """
        Get list of all collections in vector store.
        
        Returns:
            List of collection names
        """
        try:
            collections = self.client.get_collections()
            return [c.name for c in collections.collections]
        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.
        
        Args:
            collection_name: Collection to delete
            
        Returns:
            True if successful
        """
        try:
            self.client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {str(e)}")
            return False
    
    def get_collection_stats(self, collection_name: str) -> Optional[dict]:
        """
        Get statistics about a collection.
        
        Args:
            collection_name: Collection name
            
        Returns:
            Dictionary with collection stats, or zeros if the collection does not exist
            in Qdrant yet (e.g. not ingested). None only on unexpected errors.
        """
        try:
            if not self.client.collection_exists(collection_name=collection_name):
                return {
                    "name": collection_name,
                    "points_count": 0,
                    "vectors_count": 0,
                }
            info = self.client.get_collection(collection_name=collection_name)
            # Qdrant REST CollectionInfo has no `name` (we already have it) or top-level
            # `vectors_count`; use points_count and indexed_vectors_count.
            # Use points_count as the definitive total document count
            points = info.points_count if info.points_count is not None else 0
            
            # indexed_vectors_count shows how many have been HNSW-indexed (can be 0 initially)
            indexed = info.indexed_vectors_count
            
            # For the summary 'vectors_count', we prefer the total points if indexing is still 0
            vectors_count = indexed if indexed is not None and indexed > 0 else points
            
            return {
                "name": collection_name,
                "points_count": points,
                "vectors_count": vectors_count,
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return None
    
    @staticmethod
    def _hash_id(text_id: str) -> int:
        """
        Convert string ID to integer hash for Qdrant.
        
        Args:
            text_id: Text ID
            
        Returns:
            Integer hash
        """
        return abs(hash(text_id)) % (2**63)


# Global vector store instance
_vector_store = None


def get_vector_store() -> VectorStore:
    """
    Get singleton vector store instance.
    
    Returns:
        VectorStore instance
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
