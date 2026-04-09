"""
RBAC (Role-Based Access Control) retrieval module.
Enforces access controls at the vector database retrieval layer.
"""

import logging
from typing import List, Optional, Tuple
from metadata_schema import Chunk, RetrievalResult
from vector_store import get_vector_store
from retrieval.user_auth import get_user_manager
from config import RETRIEVAL_CONFIG

logger = logging.getLogger(__name__)


class RBACRetriever:
    """
    Retrieves chunks from vector database with RBAC enforcement.
    CRITICAL: Filter is applied at Qdrant level, not post-processing.
    """
    
    def __init__(self):
        """Initialize retriever."""
        self.vector_store = get_vector_store()
        self.user_manager = get_user_manager()
    
    def retrieve(
        self,
        user_role: str,
        collections: List[str],
        query_text: str,
        top_k: int = None,
        score_threshold: float = None,
    ) -> RetrievalResult:
        """
        Retrieve chunks with RBAC enforcement.
        
        Key principle: Only return chunks that:
        1. Match the query (via embedding similarity)
        2. Belong to collections the user can access
        3. Have access roles that include the user's role
        
        Args:
            user_role: User's role
            collections: List of collections to search
            query_text: Query text
            top_k: Number of results to return (default from config)
            score_threshold: Minimum similarity score (default from config)
            
        Returns:
            RetrievalResult with RBAC status
        """
        if top_k is None:
            top_k = RETRIEVAL_CONFIG.get("top_k", 5)
        if score_threshold is None:
            score_threshold = RETRIEVAL_CONFIG.get("score_threshold", 0.5)
        
        # Validate user role
        accessible_collections = self.user_manager.get_user_accessible_collections(user_role)
        
        if not accessible_collections:
            return RetrievalResult(
                chunks=[],
                rbac_passed=False,
                reason=f"User role '{user_role}' has no accessible collections",
            )
        
        # Validate requested collections against user's access
        authorized_collections = [
            c for c in collections if c in accessible_collections
        ]
        
        if not authorized_collections:
            return RetrievalResult(
                chunks=[],
                rbac_passed=False,
                reason=f"User role '{user_role}' cannot access collections: {collections}. "
                       f"Accessible collections: {accessible_collections}",
            )
        
        # Search each authorized collection
        all_results = []
        
        for collection in authorized_collections:
            results = self.vector_store.search_by_text(
                collection_name=collection,
                query_text=query_text,
                access_roles=[user_role],  # CRITICAL: Pass user's role for RBAC
                top_k=top_k,
                score_threshold=score_threshold,
            )
            
            # Convert results to Chunk objects
            for result in results:
                chunk = self._dict_to_chunk(result)
                if chunk:
                    all_results.append(chunk)
        
        # Sort by score and return top results
        all_results = sorted(
            all_results,
            key=lambda c: c.embedding[-1] if c.embedding else 0,
            reverse=True,
        )[:top_k]
        
        logger.info(
            f"RBAC retrieval for user '{user_role}': "
            f"queried collections {authorized_collections}, "
            f"returned {len(all_results)} chunks"
        )
        
        return RetrievalResult(
            chunks=all_results,
            rbac_passed=True,
            reason=None,
        )
    
    def retrieve_from_collection(
        self,
        user_role: str,
        collection: str,
        query_text: str,
        top_k: int = None,
    ) -> RetrievalResult:
        """
        Retrieve from specific collection with RBAC.
        
        Args:
            user_role: User's role
            collection: Specific collection to search
            query_text: Query text
            top_k: Number of results
            
        Returns:
            RetrievalResult with RBAC status
        """
        # Check authorization for this specific collection
        if not self.user_manager.is_role_authorized_for_collection(user_role, collection):
            return RetrievalResult(
                chunks=[],
                rbac_passed=False,
                reason=f"User role '{user_role}' is not authorized to access collection '{collection}'",
            )
        
        return self.retrieve(
            user_role=user_role,
            collections=[collection],
            query_text=query_text,
            top_k=top_k,
        )
    
    def multi_collection_search(
        self,
        user_role: str,
        query_text: str,
        top_k_per_collection: int = 3,
    ) -> dict:
        """
        Search across multiple collections with per-collection results.
        Useful for understanding what came from which department.
        
        Args:
            user_role: User's role
            query_text: Query text
            top_k_per_collection: Results per collection
            
        Returns:
            Dictionary mapping collection names to list of chunks
        """
        results_by_collection = {}
        
        accessible_collections = self.user_manager.get_user_accessible_collections(user_role)
        
        for collection in accessible_collections:
            result = self.retrieve_from_collection(
                user_role=user_role,
                collection=collection,
                query_text=query_text,
                top_k=top_k_per_collection,
            )
            
            if result.rbac_passed:
                results_by_collection[collection] = result.chunks
            else:
                results_by_collection[collection] = []
        
        return results_by_collection
    
    @staticmethod
    def _dict_to_chunk(result_dict: dict) -> Optional[Chunk]:
        """
        Convert search result dictionary to Chunk object.
        
        Args:
            result_dict: Result from vector search
            
        Returns:
            Chunk object or None
        """
        try:
            from metadata_schema import ChunkType
            
            return Chunk(
                id=f"result_{result_dict['id']}",
                text=result_dict.get("text", ""),
                source_document=result_dict.get("source_document", ""),
                collection=result_dict.get("collection", ""),
                access_roles=result_dict.get("access_roles", []),
                section_title=result_dict.get("section_title"),
                subsection_title=result_dict.get("subsection_title"),
                page_number=result_dict.get("page_number"),
                chunk_type=ChunkType(result_dict.get("chunk_type", "text")),
                parent_chunk_id=result_dict.get("parent_chunk_id"),
                parent_summary=result_dict.get("parent_summary"),
                depth=result_dict.get("depth", 0),
                embedding=[result_dict.get("score", 0)],  # Store score as embedding marker
            )
        except Exception as e:
            logger.error(f"Error converting result to chunk: {str(e)}")
            return None


# Global retriever instance
_retriever = None


def get_rbac_retriever() -> RBACRetriever:
    """
    Get singleton RBAC retriever instance.
    
    Returns:
        RBACRetriever instance
    """
    global _retriever
    if _retriever is None:
        _retriever = RBACRetriever()
    return _retriever
