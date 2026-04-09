"""
Semantic query router.
Routes queries to appropriate collections based on intent.
Intersects routing decision with user role for RBAC.
"""

import logging
from typing import List, Tuple, Optional
from semantic_router import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder

from routing.semantic_router_config import ALL_ROUTES, ROUTE_COLLECTION_MAPPING
from retrieval.user_auth import get_user_manager

logger = logging.getLogger(__name__)

# Same model family as vector_store.SentenceTransformer("all-MiniLM-L6-v2") so routing
# embeddings align with retrieval; avoids OpenAIEncoder + OPENAI_API_KEY.
_ROUTER_ENCODER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class QueryRouter:
    """
    Routes queries to appropriate collections using semantic routing.
    Enforces RBAC by filtering collections based on user role.
    """
    
    def __init__(self):
        """Initialize semantic router (local embeddings; no OpenAI key)."""
        encoder = HuggingFaceEncoder(name=_ROUTER_ENCODER_MODEL)
        # Build index via add(); passing routes only in the constructor leaves
        # LocalIndex empty (is_ready False) unless auto_sync is configured.
        self.router = SemanticRouter(routes=[], encoder=encoder)
        self.router.add(ALL_ROUTES)
        logger.info(
            "Semantic router initialized (encoder=%s, %d routes)",
            _ROUTER_ENCODER_MODEL,
            len(ALL_ROUTES),
        )
        
        self.user_manager = get_user_manager()
    
    def route_query(
        self,
        query_text: str,
        user_role: str,
    ) -> Tuple[str, List[str], Optional[str]]:
        """
        Route a query to appropriate collections based on intent.
        Enforces RBAC by checking if user can access recommended collections.
        
        Args:
            query_text: User's query
            user_role: User's role (for RBAC)
            
        Returns:
            Tuple of (route_name, authorized_collections, denial_reason)
            - route_name: Name of selected route (or "denied" if RBAC violation)
            - authorized_collections: Collections user can access for this route
            - denial_reason: If denied, explains why (or None)
        """
        try:
            # Get user's accessible collections
            user_accessible = self.user_manager.get_user_accessible_collections(user_role)
            
            if not user_accessible:
                return (
                    "denied",
                    [],
                    f"User role '{user_role}' has no accessible collections",
                )
            
            # Route query using semantic router
            route = self.router(query_text)
            
            # Handle case where no route matches
            if not route or not hasattr(route, 'name'):
                # Default to cross-department
                route_name = "cross_department_route"
                logger.info(f"Query did not match specific route, defaulting to: {route_name}")
            else:
                route_name = route.name
            
            # Get collections for this route
            route_collections = ROUTE_COLLECTION_MAPPING.get(
                route_name,
                ["general"]
            )
            
            # Filter by user's accessible collections
            # This is the RBAC enforcement point
            authorized = [
                c for c in route_collections if c in user_accessible
            ]
            
            if not authorized:
                # User cannot access this route's collections at all
                return (
                    "denied",
                    [],
                    f"User role '{user_role}' cannot access {route_name} collections: "
                    f"{route_collections}. Accessible: {user_accessible}",
                )
            
            # RBAC: if the route targets a *specific* domain (finance/engineering/marketing)
            # and the user doesn't have access to that domain, deny it.
            # This prevents a marketing user from "asking a finance question" and getting
            # an unhelpful "no relevant context" instead of a clear ACCESS DENIED.
            #
            # EXCEPTION: cross_department_route and hr_general_route are accessible
            # to ALL roles — they should simply be filtered to each user's accessible
            # collections (which already happened above on line 92-94).
            if route_name not in ("cross_department_route", "hr_general_route"):
                domain_collections = [c for c in route_collections if c != "general"]
                if domain_collections:
                    # There IS a domain collection for this route
                    user_has_domain = any(c in user_accessible for c in domain_collections)
                    if not user_has_domain:
                        return (
                            "denied",
                            [],
                            f"Access denied: Your role '{user_role}' does not have permission to access "
                            f"{route_name[:-6].replace('_', ' ').title()} information. "  # e.g. "Finance"
                            f"You can only access: {', '.join(user_accessible)}.",
                        )
            
            logger.info(
                f"Routed query to {route_name}: {authorized} "
                f"(user role: {user_role})"
            )
            
            return (route_name, authorized, None)
        
        except Exception as e:
            logger.error(f"Error routing query: {str(e)}")
            # Raise error to stop processing instead of silent fallback
            raise e
    
    def get_route_info(self, route_name: str) -> dict:
        """
        Get information about a specific route.
        
        Args:
            route_name: Route name
            
        Returns:
            Dictionary with route information
        """
        collections = ROUTE_COLLECTION_MAPPING.get(route_name, [])
        
        rout = next((r for r in ALL_ROUTES if r.name == route_name), None)
        
        return {
            "name": route_name,
            "collections": collections,
            "description": rout.description if rout and hasattr(rout, 'description') else "Unknown",
        }
    
    def list_routes(self) -> List[dict]:
        """
        Get list of all available routes.
        
        Returns:
            List of route information dictionaries
        """
        return [self.get_route_info(r.name) for r in ALL_ROUTES]
    
    def check_route_authorization(
        self,
        route_name: str,
        user_role: str,
    ) -> Tuple[bool, str]:
        """
        Check if a user can access a specific route.
        
        Args:
            route_name: Route name to check
            user_role: User role
            
        Returns:
            Tuple of (is_authorized, explanation)
        """
        user_accessible = self.user_manager.get_user_accessible_collections(user_role)
        route_collections = ROUTE_COLLECTION_MAPPING.get(route_name, [])
        
        # Check if any of the route's collections are accessible to the user
        authorized = any(c in user_accessible for c in route_collections)
        
        if authorized:
            allowed_collections = [c for c in route_collections if c in user_accessible]
            explanation = f"User role '{user_role}' can access {', '.join(allowed_collections)}"
        else:
            explanation = (
                f"User role '{user_role}' cannot access {route_name}. "
                f"Route requires: {', '.join(route_collections)}. "
                f"User has access to: {', '.join(user_accessible)}"
            )
        
        return authorized, explanation


# Global router instance
_router = None


def get_router() -> QueryRouter:
    """
    Get singleton query router instance.
    
    Returns:
        QueryRouter instance
    """
    global _router
    if _router is None:
        _router = QueryRouter()
    return _router
