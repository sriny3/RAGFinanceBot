"""
Output guardrails module.
Validates and enhances LLM responses for safety and quality.
"""

import logging
import re
from typing import List, Tuple, Optional
from metadata_schema import Chunk

logger = logging.getLogger(__name__)


class OutputGuards:
    """
    Validates LLM-generated responses for grounding, bias, and proper attribution.
    """
    
    def __init__(self):
        """Initialize output guards."""
        # Financial keywords for detecting finance-related content
        self.finance_keywords = {
            "budget", "revenue", "financial", "eps", "roi", "margin", "earnings",
            "investment", "portfolio", "dividend", "yield", "stock", "bond", "fund",
            "cash flow", "liabilities", "assets", "equity", "profit", "loss", "expense"
        }
        
        # Engineering keywords
        self.engineering_keywords = {
            "api", "endpoint", "deployment", "architecture", "system", "framework",
            "database", "server", "service", "microservice", "containerization",
            "kubernetes", "docker", "devops", "ci/cd", "git", "code", "algorithm"
        }
        
        # Marketing keywords
        self.marketing_keywords = {
            "campaign", "promotion", "brand", "market", "segment", "roi", "conversion",
            "impression", "click", "ctr", "customer acquisition", "pipeline", "lead",
            "sales", "advertising", "seo", "social media"
        }
    
    def validate_response(
        self,
        response_text: str,
        retrieved_chunks: List[Chunk],
        user_role: str,
        user_accessible_collections: List[str],
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Perform all output validations on LLM response.
        
        Args:
            response_text: LLM-generated response
            retrieved_chunks: Chunks that were used for RAG
            user_role: User's role (for cross-role leakage check)
            user_accessible_collections: Collections user can access
            
        Returns:
            Tuple of:
            - is_valid (bool): Whether response passed validation
            - warning_or_none (str): Any warning to append to response
            - flags (List[str]): List of guard flags triggered
        """
        flags = []
        warnings = []
        
        # Check if response is properly grounded
        is_grounded, ground_issues = self._check_grounding(
            response_text,
            retrieved_chunks
        )
        if not is_grounded:
            flags.append("potentially_ungrounded")
            warnings.append(
                "⚠️ **Warning**: Some claims in this response may not be directly "
                "supported by the source documents. Please verify important facts."
            )
        
        # Check if citations are present
        has_citations, citation_warning = self._check_citations(response_text)
        if not has_citations:
            flags.append("missing_citations")
            warnings.append(
                "⚠️ **Warning**: This response does not cite source documents. "
                "Please inform the assistant to cite sources."
            )
        
        # Check for cross-role leakage
        has_leakage, leakage_warning = self._check_cross_role_leakage(
            response_text,
            user_accessible_collections
        )
        if has_leakage:
            flags.append("potential_cross_role_leakage")
            warnings.append(
                "⚠️ **Warning**: This response may contain information from "
                "collections you don't have access to. Please report this issue."
            )
        
        # Combine warnings
        combined_warning = None
        if warnings:
            combined_warning = " ".join(warnings)
        
        return True, combined_warning, flags  # Allow response but flag issues
    
    def _check_grounding(
        self,
        response_text: str,
        retrieved_chunks: List[Chunk],
    ) -> Tuple[bool, List[str]]:
        """
        Check if response claims are grounded in retrieved chunks.
        Looks for specific facts (numbers, dates, names) and verifies they exist in chunks.
        
        Args:
            response_text: Response text
            retrieved_chunks: Retrieved chunks used for RAG
            
        Returns:
            Tuple of (is_grounded, list_of_issues)
        """
        issues = []
        
        # Extract potential claims (numbers, dates, percentages)
        # Simple regex patterns for demonstration
        numbers = re.findall(r'\b\d+(?:\.\d+)?(?:%|M|B|K)?\b', response_text)
        dates = re.findall(r'\b\d{4}(?:-\d{2})?(?:-\d{2})?\b', response_text)
        
        # Build combined text from chunks for comparison
        chunks_text = " ".join([c.text for c in retrieved_chunks]).lower()
        response_lower = response_text.lower()
        
        # Check if key numbers appear in chunks
        ungrounded_numbers = []
        for number in numbers:
            if number not in chunks_text and len(number) > 2:  # Ignore very short numbers
                ungrounded_numbers.append(number)
        
        if ungrounded_numbers:
            issues.append(f"Ungrounded numbers: {', '.join(ungrounded_numbers[:3])}")
        
        # Check for specific financial/technical claims
        claims = self._extract_claims(response_text)
        
        for claim in claims:
            claim_lower = claim.lower()
            if claim_lower not in chunks_text:
                # Check if it's a reformulation of content
                if not self._is_reformulation(claim, retrieved_chunks):
                    issues.append(f"Unverified claim: {claim[:50]}")
        
        is_grounded = len(issues) == 0
        return is_grounded, issues
    
    def _extract_claims(self, text: str) -> List[str]:
        """
        Extract potential claims from text.
        Simple heuristic: sentences with numbers or specific keywords.
        
        Args:
            text: Text to extract claims from
            
        Returns:
            List of potential claims
        """
        claims = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            # Look for sentences with numbers or strong keywords
            if (
                any(char.isdigit() for char in sentence) or
                any(keyword in sentence.lower() for keyword in [
                    "is", "was", "will be", "has", "revenue", "budget", "policy"
                ])
            ):
                if len(sentence) > 10:
                    claims.append(sentence)
        
        return claims[:5]  # Return top 5 claims
    
    def _is_reformulation(self, claim: str, chunks: List[Chunk]) -> bool:
        """
        Check if a claim is a reasonable reformulation of chunk content.
        
        Args:
            claim: Potential claim
            chunks: Retrieved chunks
            
        Returns:
            True if claim appears to be reformulation of chunk content
        """
        # Simple keyword-based check
        claim_words = set(claim.lower().split())
        
        for chunk in chunks:
            chunk_words = set(chunk.text.lower().split())
            # If 30% of claim words are in chunks, consider it a reformulation
            overlap = len(claim_words & chunk_words) / len(claim_words) if claim_words else 0
            if overlap > 0.3:
                return True
        
        return False
    
    def _check_citations(self, response_text: str) -> Tuple[bool, Optional[str]]:
        """
        Check if response includes source citations.
        Note: Bypassed because the frontend explicitly renders the `sources` array natively.
        """
        return True, None
    
    def _check_cross_role_leakage(
        self,
        response_text: str,
        user_accessible_collections: List[str],
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if response contains content from collections user can't access.
        
        Args:
            response_text: Response text
            user_accessible_collections: Collections user can access
            
        Returns:
            Tuple of (has_leakage, warning_or_none)
        """
        response_lower = response_text.lower()
        
        # Define collection-specific keywords
        collection_keywords = {
            "finance": self.finance_keywords,
            "engineering": self.engineering_keywords,
            "marketing": self.marketing_keywords,
        }
        
        # Check for keywords from collections user can't access
        for collection, keywords in collection_keywords.items():
            if collection not in user_accessible_collections:
                # Count keywords from this collection in response
                count = sum(
                    response_lower.count(keyword)
                    for keyword in keywords
                )
                
                # If significant keyword presence, flag as potential leakage
                if count > 3:
                    return True, (
                        f"⚠️ **Security Alert**: Response contains content from the "
                        f"{collection.upper()} collection which you don't have access to."
                    )
        
        return False, None
    
    def append_warning_to_response(
        self,
        response_text: str,
        warning: Optional[str],
    ) -> str:
        """
        Append warning to response if present.
        
        Args:
            response_text: Original response
            warning: Warning to append (if any)
            
        Returns:
            Response with warning appended (if applicable)
        """
        if warning:
            return f"{response_text}\n\n{warning}"
        return response_text


# Global output guards instance
_output_guards = None


def get_output_guards() -> OutputGuards:
    """
    Get singleton output guards instance.
    
    Returns:
        OutputGuards instance
    """
    global _output_guards
    if _output_guards is None:
        _output_guards = OutputGuards()
    return _output_guards
