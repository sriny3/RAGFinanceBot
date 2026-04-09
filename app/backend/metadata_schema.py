"""
Metadata schema for FinBot RAG system.
Defines data structures for chunks, users, and retrieval results.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List
from enum import Enum


class ChunkType(str, Enum):
    """Type of content in a chunk."""
    TEXT = "text"
    TABLE = "table"
    HEADING = "heading"
    CODE = "code"


@dataclass
class Chunk:
    """
    Represents a hierarchically-chunked document segment.
    
    This is the fundamental unit stored in the vector database.
    Each chunk carries metadata about its source, hierarchy, and access controls.
    """
    # Content
    id: str  # Unique identifier (e.g., "doc_name_chunk_0")
    text: str  # The actual text content of this chunk
    
    # Document source metadata (REQUIRED)
    source_document: str  # Filename (e.g., "system_architecture.md")
    collection: str  # Collection name (general, finance, engineering, marketing, hr)
    access_roles: List[str]  # Roles that can access this chunk (e.g., ["engineering", "c_level"])
    
    # Hierarchical structure metadata
    section_title: Optional[str] = None  # Parent section heading
    subsection_title: Optional[str] = None  # Sub-heading if applicable
    page_number: Optional[int] = None  # Page number in source document
    chunk_type: ChunkType = ChunkType.TEXT  # Type of content (text, table, heading, code)
    parent_chunk_id: Optional[str] = None  # ID of parent section chunk for hierarchy
    parent_summary: Optional[str] = None  # Summary of parent section
    
    # For tracking hierarchy depth
    depth: int = 0  # Depth in document tree (0 = root)
    
    # Embedding (populated after vectorization)
    embedding: Optional[List[float]] = field(default_factory=list)
    
    def to_qdrant_payload(self) -> dict:
        """
        Convert chunk to Qdrant payload format.
        Used when storing in vector database.
        """
        return {
            "source_document": self.source_document,
            "collection": self.collection,
            "access_roles": self.access_roles,
            "section_title": self.section_title or "",
            "subsection_title": self.subsection_title or "",
            "page_number": self.page_number or 0,
            "chunk_type": self.chunk_type.value,
            "parent_chunk_id": self.parent_chunk_id or "",
            "parent_summary": self.parent_summary or "",
            "depth": self.depth,
            "text": self.text,
        }
    
    def to_dict(self) -> dict:
        """Convert chunk to dictionary (excludes embedding)."""
        return asdict(self)


@dataclass
class User:
    """
    Represents a FinSolve employee with role and permissions.
    """
    username: str
    name: str
    role: str  # UserRole enum value (employee, finance, engineering, marketing, c_level)
    department: str
    
    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return asdict(self)


@dataclass
class QueryMetadata:
    """
    Metadata captured for every query for auditing and logging.
    """
    user_role: str
    user_department: str
    query_text: str
    route_selected: str
    collections_queried: List[str]
    chunks_retrieved: int
    guardrail_flags: List[str] = field(default_factory=list)  # e.g., ["prompt_injection_detected"]
    rbac_denied: bool = False
    answer: Optional[str] = None
    sources: List[str] = field(default_factory=list)  # List of source doc names
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class RetrievalResult:
    """
    Result from a RBAC-checked retrieval operation.
    """
    chunks: List[Chunk]
    rbac_passed: bool
    reason: Optional[str] = None  # If RBAC failed, explain why
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "chunks": [c.to_dict() for c in self.chunks],
            "rbac_passed": self.rbac_passed,
            "reason": self.reason,
        }


@dataclass
class RAGResponse:
    """
    Final response from the RAG pipeline.
    Contains answer, sources, metadata, and any warnings.
    """
    answer: str
    sources: List[dict]  # List of {document, page_number, section_title}
    route: str
    user_role: str
    accessible_collections: List[str]
    guardrail_flags: List[str] = field(default_factory=list)
    guardrail_warnings: List[str] = field(default_factory=list)
    rbac_denied: bool = False
    rbac_reason: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


# Validation helpers

def validate_chunk_metadata(chunk: Chunk) -> tuple[bool, str]:
    """
    Validate that a chunk has all required metadata.
    Returns (is_valid, error_message).
    """
    errors = []
    
    if not chunk.id:
        errors.append("Chunk id is required")
    if not chunk.text:
        errors.append("Chunk text is required")
    if not chunk.source_document:
        errors.append("source_document is required")
    if not chunk.collection:
        errors.append("collection is required")
    if not chunk.access_roles or len(chunk.access_roles) == 0:
        errors.append("access_roles must not be empty")
    
    if errors:
        return False, "; ".join(errors)
    return True, ""


def validate_user(user: User) -> tuple[bool, str]:
    """
    Validate that a user has required fields.
    Returns (is_valid, error_message).
    """
    errors = []
    
    if not user.username:
        errors.append("username is required")
    if not user.name:
        errors.append("name is required")
    if not user.role:
        errors.append("role is required")
    if not user.department:
        errors.append("department is required")
    
    if errors:
        return False, "; ".join(errors)
    return True, ""
