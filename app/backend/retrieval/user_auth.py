"""
User authentication and management module.
Handles demo users and user role verification.
"""

from typing import Optional, List
from metadata_schema import User
from config import DEMO_USERS, UserRole, ROLE_COLLECTION_ACCESS


class UserManager:
    """
    Manages user authentication and authorization.
    For production, this would integrate with OAuth/LDAP.
    """
    
    def __init__(self):
        """Initialize user manager with demo users."""
        self.users = {
            username: User(
                username=data["username"],
                name=data["name"],
                role=data["role"],
                department=data["department"],
            )
            for username, data in DEMO_USERS.items()
        }
    
    def get_user(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username to look up
            
        Returns:
            User object if found, None otherwise
        """
        return self.users.get(username)
    
    def list_users(self) -> List[User]:
        """
        Get list of all available users (for demo/login screen).
        
        Returns:
            List of User objects
        """
        return list(self.users.values())
    
    def get_user_accessible_collections(self, role: str) -> List[str]:
        """
        Get list of document collections accessible to a user by their role.
        
        Args:
            role: User role (from UserRole enum)
            
        Returns:
            List of collection names the role can access
        """
        try:
            role_enum = UserRole(role)
            collections = ROLE_COLLECTION_ACCESS.get(role_enum, [])
            return [c.value for c in collections]
        except ValueError:
            # Unknown role
            return []
    
    def is_role_authorized_for_collection(self, role: str, collection: str) -> bool:
        """
        Check if a user role is authorized to access a specific collection.
        This is used for RBAC enforcement.
        
        Args:
            role: User role
            collection: Collection name
            
        Returns:
            True if role has access to collection, False otherwise
        """
        accessible = self.get_user_accessible_collections(role)
        return collection in accessible
    
    def verify_user_credentials(self, username: str) -> bool:
        """
        Verify that a user exists.
        For demo purposes, we just check existence.
        In production, verify against auth system.
        
        Args:
            username: Username to verify
            
        Returns:
            True if user exists, False otherwise
        """
        return username in self.users


# Global user manager instance
_user_manager = None


def get_user_manager() -> UserManager:
    """
    Get singleton user manager instance.
    """
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager
