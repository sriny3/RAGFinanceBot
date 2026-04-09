"""
Input guardrails module.
Validates and sanitizes user queries before processing.
"""

import logging
import re
from typing import Tuple, Optional, List
from config import (
    OFF_TOPIC_KEYWORDS,
    INJECTION_PATTERNS,
    PII_PATTERNS,
    RATE_LIMIT_CONFIG,
)

logger = logging.getLogger(__name__)


class InputGuards:
    """
    Validates user input for harmful patterns and violations.
    """
    
    def __init__(self):
        """Initialize input guards."""
        self.session_query_counts = {}  # user_id -> query_count
        self.max_queries = RATE_LIMIT_CONFIG.get("max_queries_per_session", 20)
    
    def validate_query(
        self,
        query_text: str,
        user_role: str = None,
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Perform all input validations on query.
        
        Args:
            query_text: User's query
            user_role: User's role (optional, for context)
            
        Returns:
            Tuple of:
            - is_valid (bool): Whether query passed all guards
            - rejection_reason (str): If invalid, why it was rejected
            - flags (List[str]): List of guard flags that were triggered
        """
        flags = []
        
        # Check for prompt injection
        is_injection, injection_reason = self._check_prompt_injection(query_text)
        if is_injection:
            flags.append("prompt_injection_detected")
            return False, injection_reason, flags
        
        # Check for off-topic content
        is_off_topic, offtopic_reason = self._check_off_topic(query_text)
        if is_off_topic:
            flags.append("off_topic_detected")
            return False, offtopic_reason, flags
        
        # Check for PII
        has_pii, pii_types = self._check_pii(query_text)
        if has_pii:
            flags.append("pii_detected")
            sanitized = self._sanitize_pii(query_text)
            logger.warning(
                f"PII detected in query: {pii_types}. Sanitizing."
            )
            return True, None, flags  # Allow but flag for sanitization
        
        # All checks passed
        return True, None, flags
    
    def _check_prompt_injection(self, query_text: str) -> Tuple[bool, Optional[str]]:
        """
        Detect common prompt injection patterns.
        
        Args:
            query_text: Query text
            
        Returns:
            Tuple of (is_injection, reason_or_none)
        """
        query_lower = query_text.lower()
        
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                reason = f"Query matches prohibited pattern: {pattern}"
                logger.warning(f"Prompt injection detected: {reason}")
                return True, reason
        
        return False, None
    
    def _check_off_topic(self, query_text: str) -> Tuple[bool, Optional[str]]:
        """
        Detect off-topic queries unrelated to FinSolve business.
        
        Args:
            query_text: Query text
            
        Returns:
            Tuple of (is_off_topic, reason_or_none)
        """
        query_lower = query_text.lower()
        
        # Count off-topic keyword matches
        matches = sum(
            1 for keyword in OFF_TOPIC_KEYWORDS
            if keyword in query_lower
        )
        
        if matches > 0:
            reason = (
                "Your query appears to be off-topic. I'm designed to answer questions "
                "about FinSolve's business, not general topics like entertainment or sports."
            )
            logger.info(f"Off-topic query detected: {query_text[:100]}")
            return True, reason
        
        return False, None
    
    def _check_pii(self, query_text: str) -> Tuple[bool, List[str]]:
        """
        Detect personally identifiable information in query.
        
        Args:
            query_text: Query text
            
        Returns:
            Tuple of (has_pii, list_of_pii_types_found)
        """
        pii_types = []
        
        for pii_type, pattern in PII_PATTERNS.items():
            if re.search(pattern, query_text):
                pii_types.append(pii_type)
        
        if pii_types:
            logger.warning(f"PII detected in query: {pii_types}")
        
        return len(pii_types) > 0, pii_types
    
    def _sanitize_pii(self, query_text: str) -> str:
        """
        Remove or mask PII in query text.
        
        Args:
            query_text: Original query text
            
        Returns:
            Sanitized query text
        """
        sanitized = query_text
        
        # Mask email addresses
        sanitized = re.sub(
            PII_PATTERNS["email"],
            "[EMAIL_REDACTED]",
            sanitized,
            flags=re.IGNORECASE
        )
        
        # Mask phone numbers
        sanitized = re.sub(
            PII_PATTERNS["phone"],
            "[PHONE_REDACTED]",
            sanitized,
        )
        
        # Mask Aadhaar numbers
        sanitized = re.sub(
            PII_PATTERNS["aadhaar"],
            "[AADHAAR_REDACTED]",
            sanitized,
        )
        
        # Mask bank account numbers
        sanitized = re.sub(
            PII_PATTERNS["bank_account"],
            "[ACCOUNT_REDACTED]",
            sanitized,
        )
        
        return sanitized
    
    def check_rate_limit(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user has exceeded query rate limit.
        
        Args:
            user_id: User identifier
            
        Returns:
            Tuple of (is_under_limit, warning_or_none)
        """
        if user_id not in self.session_query_counts:
            self.session_query_counts[user_id] = 0
        
        current_count = self.session_query_counts[user_id]
        self.session_query_counts[user_id] += 1
        
        if current_count >= self.max_queries:
            reason = (
                f"You have exceeded the query limit of {self.max_queries} "
                "queries per session. Please start a new session."
            )
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False, reason
        
        # Warning at 80% of limit
        if current_count >= int(self.max_queries * 0.8):
            warning = (
                f"Warning: You are approaching the query limit "
                f"({current_count}/{self.max_queries})."
            )
            return True, warning
        
        return True, None
    
    def reset_session(self, user_id: str):
        """
        Reset query count for a user session.
        
        Args:
            user_id: User identifier
        """
        if user_id in self.session_query_counts:
            self.session_query_counts[user_id] = 0


# Global input guards instance
_input_guards = None


def get_input_guards() -> InputGuards:
    """
    Get singleton input guards instance.
    
    Returns:
        InputGuards instance
    """
    global _input_guards
    if _input_guards is None:
        _input_guards = InputGuards()
    return _input_guards
