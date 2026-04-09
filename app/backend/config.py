"""
Configuration module for FinBot RAG system.
Centralizes all constants, role-collection mappings, and configuration.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Absolute path to the data directory (always relative to THIS file: backend/config.py)
# config.py lives at: Assignment1/app/backend/config.py
# data dir lives at:  Assignment1/data/
_CONFIG_DIR = Path(__file__).parent          # → Assignment1/app/backend/
_APP_DIR    = _CONFIG_DIR.parent             # → Assignment1/app/
_ROOT_DIR   = _APP_DIR.parent               # → Assignment1/
DATA_BASE_PATH = str(_ROOT_DIR / "data")     # → Assignment1/data/  (absolute)

# ====================
# USER ROLES & COLLECTIONS
# ====================

class UserRole(str, Enum):
    """User roles in FinSolve organization."""
    EMPLOYEE = "employee"
    FINANCE = "finance"
    ENGINEERING = "engineering"
    MARKETING = "marketing"
    C_LEVEL = "c_level"


class DocumentCollection(str, Enum):
    """Document collections in knowledge base."""
    GENERAL = "general"
    FINANCE = "finance"
    ENGINEERING = "engineering"
    MARKETING = "marketing"
    HR = "hr"


# Role -> Accessible Collections mapping (CRITICAL for RBAC)
ROLE_COLLECTION_ACCESS: Dict[UserRole, List[DocumentCollection]] = {
    UserRole.EMPLOYEE: [DocumentCollection.GENERAL],
    UserRole.FINANCE: [DocumentCollection.GENERAL, DocumentCollection.FINANCE],
    UserRole.ENGINEERING: [DocumentCollection.GENERAL, DocumentCollection.ENGINEERING],
    UserRole.MARKETING: [DocumentCollection.GENERAL, DocumentCollection.MARKETING],
    UserRole.C_LEVEL: [
        DocumentCollection.GENERAL,
        DocumentCollection.FINANCE,
        DocumentCollection.ENGINEERING,
        DocumentCollection.MARKETING,
        DocumentCollection.HR,
    ],
}

# Collection -> Access Roles mapping (for metadata tagging in vector store)
COLLECTION_ACCESS_ROLES: Dict[DocumentCollection, List[str]] = {
    DocumentCollection.GENERAL: ["employee", "finance", "engineering", "marketing", "c_level"],
    DocumentCollection.FINANCE: ["finance", "c_level"],
    DocumentCollection.ENGINEERING: ["engineering", "c_level"],
    DocumentCollection.MARKETING: ["marketing", "c_level"],
    DocumentCollection.HR: ["employee", "finance", "engineering", "marketing", "c_level"],  # HR is for all roles
}

# ====================
# DEMO USERS (for testing and demo)
# ====================

DEMO_USERS = {
    "emp_john": {
        "username": "emp_john",
        "name": "John Employee",
        "role": UserRole.EMPLOYEE,
        "department": "General",
    },
    "fin_alice": {
        "username": "fin_alice",
        "name": "Alice Finance",
        "role": UserRole.FINANCE,
        "department": "Finance",
    },
    "eng_bob": {
        "username": "eng_bob",
        "name": "Bob Engineer",
        "role": UserRole.ENGINEERING,
        "department": "Engineering",
    },
    "mkt_carol": {
        "username": "mkt_carol",
        "name": "Carol Marketing",
        "role": UserRole.MARKETING,
        "department": "Marketing",
    },
    "ceo_dave": {
        "username": "ceo_dave",
        "name": "Dave C-Level",
        "role": UserRole.C_LEVEL,
        "department": "Executive",
    },
}

# ====================
# DOCUMENT PATHS & METADATA
# ====================

# DATA_BASE_PATH is now an absolute path defined above (near imports)

COLLECTION_CONFIGS = {
    DocumentCollection.GENERAL: {
        "path": f"{DATA_BASE_PATH}/general",
        "access_roles": COLLECTION_ACCESS_ROLES[DocumentCollection.GENERAL],
        "description": "Company policies, HR handbook, FAQs",
    },
    DocumentCollection.FINANCE: {
        "path": f"{DATA_BASE_PATH}/finance",
        "access_roles": COLLECTION_ACCESS_ROLES[DocumentCollection.FINANCE],
        "description": "Financial reports, budgets, investor documents",
    },
    DocumentCollection.ENGINEERING: {
        "path": f"{DATA_BASE_PATH}/engineering",
        "access_roles": COLLECTION_ACCESS_ROLES[DocumentCollection.ENGINEERING],
        "description": "Technical specs, architecture docs, runbooks",
    },
    DocumentCollection.MARKETING: {
        "path": f"{DATA_BASE_PATH}/marketing",
        "access_roles": COLLECTION_ACCESS_ROLES[DocumentCollection.MARKETING],
        "description": "Campaign reports, brand guidelines, market research",
    },
    DocumentCollection.HR: {
        "path": f"{DATA_BASE_PATH}/hr",
        "access_roles": COLLECTION_ACCESS_ROLES[DocumentCollection.HR],
        "description": "HR policies, employee handbook",
    },
}

# ====================
# SEMANTIC ROUTER CONFIGURATION
# ====================

# Routes and their utterances for semantic routing
SEMANTIC_ROUTES = {
    "finance_route": {
        "name": "finance_route",
        "utterances": [
            "What is our Q3 revenue?",
            "How much did we budget for marketing this year?",
            "Show me financial metrics for 2024.",
            "What are our investor relations like?",
            "Can you provide details on ROI?",
            "What's our profit margin?",
            "Tell me about quarterly earnings.",
            "What are our expense allocations?",
            "Show me the annual financial report.",
            "What are vendor payments?",
            "Can you help with budget planning?",
            "What's the cost of goods sold?",
        ],
        "description": "Queries about finances, budgets, revenue, and investor information",
        "collection_priority": [DocumentCollection.FINANCE, DocumentCollection.GENERAL],
    },
    "engineering_route": {
        "name": "engineering_route",
        "utterances": [
            "How do I onboard to the platform?",
            "Tell me about our system architecture.",
            "What are our API endpoints?",
            "How do we handle incidents?",
            "Show me the technical specifications.",
            "What's our deployment process?",
            "How do we manage SLAs?",
            "Tell me about our sprint metrics.",
            "What are the incident response procedures?",
            "Can you explain our system design?",
            "Show me the API reference documentation.",
            "How do we do code reviews?",
        ],
        "description": "Queries about systems, architecture, APIs, incidents, and technical topics",
        "collection_priority": [DocumentCollection.ENGINEERING, DocumentCollection.GENERAL],
    },
    "marketing_route": {
        "name": "marketing_route",
        "utterances": [
            "What's our campaign performance?",
            "Tell me about our brand guidelines.",
            "What's our market share?",
            "Who are our competitors?",
            "Show me customer acquisition data.",
            "What are our marketing metrics?",
            "Tell me about our brand positioning.",
            "How are our campaigns performing?",
            "What's our customer acquisition strategy?",
            "Show me competitive analysis.",
            "What are current marketing initiatives?",
            "Tell me about promotional campaigns.",
        ],
        "description": "Queries about campaigns, brand, market research, and marketing strategy",
        "collection_priority": [DocumentCollection.MARKETING, DocumentCollection.GENERAL],
    },
    "hr_general_route": {
        "name": "hr_general_route",
        "utterances": [
            "What are our HR policies?",
            "How much leave am I entitled to?",
            "Tell me about company benefits.",
            "What's the company culture like?",
            "How do I request time off?",
            "What are the company policies?",
            "Tell me about employee handbook.",
            "What benefits do employees get?",
            "How do we handle remote work?",
            "What's the dress code policy?",
            "Tell me about professional development.",
            "What are the vacation policies?",
        ],
        "description": "Queries about HR policies, leave, benefits, and company culture",
        "collection_priority": [DocumentCollection.GENERAL, DocumentCollection.HR],
    },
    "cross_department_route": {
        "name": "cross_department_route",
        "utterances": [
            "Tell me about FinSolve Technologies.",
            "What does the company do?",
            "Give me an overview of FinSolve.",
            "What are our company values?",
            "Tell me about our organization.",
            "What's the company mission?",
            "Can you provide general company information?",
            "What is FinSolve?",
            "Tell me about company history.",
            "What sectors do we serve?",
        ],
        "description": "Broad queries that should search across all accessible collections",
        "collection_priority": [
            DocumentCollection.GENERAL,
            DocumentCollection.FINANCE,
            DocumentCollection.ENGINEERING,
            DocumentCollection.MARKETING,
        ],
    },
}

# ====================
# GUARDRAILS CONFIGURATION
# ====================

# Off-topic keywords/patterns
OFF_TOPIC_KEYWORDS = [
    "poem", "poem", "joke", "cricket", "sports", "music", "movie", "recipe",
    "weather", "horoscope", "lottery", "gaming tips", "dating advice",
    "write me", "tell me a", "generate", "compose", "create a",
]

# Prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore.*instruction",
    r"act as",
    r"forget.*prompt",
    r"override",
    r"bypass",
    r"no restriction",
    r"show me all",
    r"regardless of role",
    r"disable.*filter",
    r"disregard",
]

# PII patterns (simple regex patterns for demo)
PII_PATTERNS = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "aadhaar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "bank_account": r"\b\d{10,12}\b",
}

# ====================
# VECTOR STORE CONFIGURATION
# ====================

import os

QDRANT_CONFIG = {
    "mode": os.getenv("QDRANT_MODE", "local"),  # "memory", "local", or "url" (for Qdrant Cloud)
    "path": os.getenv("QDRANT_STORAGE_PATH", str(_ROOT_DIR / "app" / "backend" / "qdrant_storage")),
    "url": os.getenv("QDRANT_URL", "localhost:6333"),
    "api_key": os.getenv("QDRANT_API_KEY") or None,
    "vector_size": 384,  # Sentence-Transformers all-MiniLM-L6-v2 dimension
}

# ====================
# RETRIEVAL CONFIGURATION
# ====================

RETRIEVAL_CONFIG = {
    "top_k": 5,  # Number of top chunks to retrieve
    "score_threshold": 0.3,  # Minimum similarity score (lowered from 0.5 to avoid missing relevant chunks)
}

# ====================
# LLM CONFIGURATION
# ====================

LLM_CONFIG = {
    "model": "llama-3.3-70b-versatile",  # Groq fast versatile model
    "temperature": 0.2,  # Low temperature for factual answers
    "max_tokens": 500,
    "timeout": 30,
}

# ====================
# CHUNKING CONFIGURATION
# ====================

CHUNKING_CONFIG = {
    "max_leaf_chunk_tokens": 500,
    "overlap_tokens": 50,
    "min_chunk_tokens": 100,
}

# ====================
# SESSION & RATE LIMITING
# ====================

RATE_LIMIT_CONFIG = {
    "max_queries_per_session": 20,
    "session_timeout_minutes": 60,
}

# ====================
# LOGGING
# ====================

LOG_CONFIG = {
    "log_level": "INFO",
    "log_file": "finbot.log",
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}
