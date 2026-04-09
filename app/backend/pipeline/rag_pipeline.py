"""
RAG pipeline orchestration module.
Ties together all components: routing, retrieval, guardrails, and LLM.
"""

import logging
import os
from typing import List, Optional
from groq import Groq
from metadata_schema import RAGResponse, QueryMetadata
from routing.router import get_router
from retrieval.rbac_retriever import get_rbac_retriever
from retrieval.user_auth import get_user_manager
from guardrails.input_guards import get_input_guards
from guardrails.output_guards import get_output_guards
from config import LLM_CONFIG, RETRIEVAL_CONFIG
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Orchestrates the complete RAG pipeline:
    1. Input validation (guardrails)
    2. Query routing (semantic router)
    3. RBAC-enforced retrieval
    4. LLM generation with context
    5. Output validation (guardrails)
    """
    
    def __init__(self):
        """Initialize RAG pipeline components."""
        self.router = get_router()
        self.retriever = get_rbac_retriever()
        self.user_manager = get_user_manager()
        self.input_guards = get_input_guards()
        self.output_guards = get_output_guards()
        
        self.llm_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.llm_model = LLM_CONFIG.get("model", "openai/gpt-oss-120b")
        self.llm_temperature = LLM_CONFIG.get("temperature", 0.2)
        self.llm_max_tokens = LLM_CONFIG.get("max_tokens", 500)
    
    def answer_query(
        self,
        user_role: str,
        query_text: str,
        user_id: Optional[str] = None,
    ) -> RAGResponse:
        """
        Process a user query through the complete RAG pipeline.
        
        Args:
            user_role: User's role
            query_text: User's query
            user_id: Optional user ID for rate limiting
            
        Returns:
            RAGResponse with answer, sources, and metadata
        """
        try:
            return self._process_query(user_role, query_text, user_id)
        except Exception as e:
            logger.error(f"Unexpected error in RAG pipeline: {str(e)}", exc_info=True)
            return RAGResponse(
                answer="I'm sorry, I encountered an unexpected error while processing your question. Please try again in a moment.",
                sources=[],
                route="error",
                user_role=user_role,
                accessible_collections=[],
                guardrail_flags=["pipeline_error"],
                guardrail_warnings=[f"Internal error: {str(e)}"],
            )
    
    def _process_query(
        self,
        user_role: str,
        query_text: str,
        user_id: Optional[str] = None,
    ) -> RAGResponse:
        """Internal query processing. Separated so answer_query can wrap with try/except."""
        metadata = QueryMetadata(
            user_role=user_role,
            user_department=self._get_department(user_role),
            query_text=query_text,
            route_selected="",
            collections_queried=[],
            chunks_retrieved=0,
        )
        
        logger.info(f"Processing query from user role '{user_role}': {query_text[:100]}")
        
        with tracer.start_as_current_span("rag_pipeline_process_query") as span:
            span.set_attribute("user.role", user_role)
            span.set_attribute("query.text", query_text)
            
            # ====================
            # STEP 1: INPUT GUARDS
            # ====================
            with tracer.start_as_current_span("stage_1_input_guards"):
                logger.info("STEP 1: Input validation...")
                
                # Check rate limiting if user_id provided
                if user_id:
                    is_under_limit, rate_warning = self.input_guards.check_rate_limit(user_id)
                    if not is_under_limit:
                        return RAGResponse(
                            answer=rate_warning or "Rate limit exceeded",
                            sources=[],
                            route="rate_limited",
                            user_role=user_role,
                            accessible_collections=self.user_manager.get_user_accessible_collections(user_role),
                            guardrail_flags=["rate_limit_exceeded"],
                        )
                
                # Validate query for injection, off-topic, PII
                is_valid, rejection_reason, input_flags = self.input_guards.validate_query(
                    query_text,
                    user_role
                )
                
                if not is_valid:
                    logger.warning(f"Query rejected by input guards: {rejection_reason}")
                    return RAGResponse(
                        answer=rejection_reason or "Query validation failed",
                        sources=[],
                        route="blocked_by_guardrails",
                        user_role=user_role,
                        accessible_collections=self.user_manager.get_user_accessible_collections(user_role),
                        guardrail_flags=input_flags,
                        guardrail_warnings=[rejection_reason] if rejection_reason else [],
                    )
            
            metadata.guardrail_flags.extend(input_flags)
            
            # ====================
            # STEP 2: QUERY ROUTING
            # ====================
            with tracer.start_as_current_span("stage_2_routing") as route_span:
                logger.info("STEP 2: Semantic routing...")
                
                route_name, authorized_collections, denial_reason = self.router.route_query(
                    query_text,
                    user_role
                )
                
                route_span.set_attribute("route.name", route_name)
                route_span.set_attribute("route.authorized_collections", str(authorized_collections))
            
            metadata.route_selected = route_name
            metadata.collections_queried = authorized_collections
            
            # Check if RBAC denied this query
            if route_name == "denied":
                logger.warning(f"Query denied by RBAC: {denial_reason}")
                return RAGResponse(
                    answer=denial_reason or "You don't have access to the requested information.",
                    sources=[],
                    route=route_name,
                    user_role=user_role,
                    accessible_collections=self.user_manager.get_user_accessible_collections(user_role),
                    rbac_denied=True,
                    rbac_reason=denial_reason,
                    guardrail_flags=["rbac_denied"],
                )
            
            logger.info(f"Routed to: {route_name} → collections: {authorized_collections}")
            
            # ====================
            # STEP 3: RETRIEVAL
            # ====================
            with tracer.start_as_current_span("stage_3_retrieval") as retr_span:
                logger.info("STEP 3: RBAC-enforced retrieval...")
                
                retrieval_result = self.retriever.retrieve(
                    user_role=user_role,
                    collections=authorized_collections,
                    query_text=query_text,
                    top_k=RETRIEVAL_CONFIG.get("top_k", 5),
                )
                
                retr_span.set_attribute("retrieval.rbac_passed", retrieval_result.rbac_passed)
                retr_span.set_attribute("retrieval.chunks_count", len(retrieval_result.chunks))
            
            if not retrieval_result.rbac_passed:
                logger.warning(f"Retrieval RBAC check failed: {retrieval_result.reason}")
                return RAGResponse(
                    answer="Unable to retrieve documents due to access restrictions.",
                    sources=[],
                    route=route_name,
                    user_role=user_role,
                    accessible_collections=self.user_manager.get_user_accessible_collections(user_role),
                    rbac_denied=True,
                    rbac_reason=retrieval_result.reason,
                )
            
            chunks = retrieval_result.chunks
            metadata.chunks_retrieved = len(chunks)
            
            if not chunks:
                logger.info(f"No relevant documents found")
                return RAGResponse(
                    answer="I couldn't find relevant information to answer your question.",
                    sources=[],
                    route=route_name,
                    user_role=user_role,
                    accessible_collections=self.user_manager.get_user_accessible_collections(user_role),
                    guardrail_flags=["no_relevant_context"],
                )
            
            logger.info(f"Retrieved {len(chunks)} chunks")
            
            # ====================
            # STEP 4: LLM GENERATION
            # ====================
            with tracer.start_as_current_span("stage_4_generation") as gen_span:
                logger.info("STEP 4: LLM generation...")
                
                # Build context from chunks
                context = self._build_context(chunks)
                
                # Generate answer
                answer = self._generate_answer(query_text, context, user_role)
                
                gen_span.set_attribute("generation.successful", bool(answer))
            
            if not answer or not answer.strip():
                return RAGResponse(
                    answer="I wasn't able to generate a response for your question. Please try rephrasing or ask a different question.",
                    sources=[],
                    route=route_name,
                    user_role=user_role,
                    accessible_collections=self.user_manager.get_user_accessible_collections(user_role),
                    guardrail_flags=["generation_failed"],
                )
            
            logger.info(f"Generated answer: {answer[:100]}...")
            
            # ====================
            # STEP 5: OUTPUT GUARDS
            # ====================
            with tracer.start_as_current_span("stage_5_output_guards"):
                logger.info("STEP 5: Output validation...")
                
                is_safe, output_warning, output_flags = self.output_guards.validate_response(
                    answer,
                    chunks,
                    user_role,
                    authorized_collections
                )
            
            metadata.guardrail_flags.extend(output_flags)
            
            # Append warning to answer if applicable
            if output_warning:
                answer = self.output_guards.append_warning_to_response(answer, output_warning)
            
            # ====================
            # BUILD SOURCES
            # ====================
            sources = []
            seen_sources = set()
            
            for chunk in chunks:
                if len(sources) >= 3:
                    break
                    
                source_key = (
                    chunk.source_document,
                    chunk.page_number or 1,
                    chunk.section_title or ""
                )
                
                if source_key not in seen_sources:
                    seen_sources.add(source_key)
                    sources.append({
                        "document": chunk.source_document,
                        "page_number": chunk.page_number or 1,
                        "section_title": chunk.section_title,
                    })
            
            metadata.sources = [s["document"] for s in sources]
            metadata.answer = answer
            
            logger.info("Query processing complete")
            
            # Return final response
            return RAGResponse(
                answer=answer,
                sources=sources,
                route=route_name,
                user_role=user_role,
                accessible_collections=self.user_manager.get_user_accessible_collections(user_role),
                guardrail_flags=metadata.guardrail_flags,
                guardrail_warnings=[output_warning] if output_warning else [],
            )
    
    def _build_context(self, chunks: List) -> str:
        """
        Build context string from retrieved chunks.
        
        Args:
            chunks: Retrieved chunks
            
        Returns:
            Context string for LLM
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            section_info = f"[Section: {chunk.section_title}]" if chunk.section_title else ""
            source_info = f"(From: {chunk.source_document}, Page {chunk.page_number or 1})"
            
            context_parts.append(
                f"{i}. {section_info}\n{chunk.text}\n{source_info}\n"
            )
        
        return "\n".join(context_parts)
    
    def _generate_answer(
        self,
        query: str,
        context: str,
        user_role: str,
    ) -> Optional[str]:
        """
        Call LLM to generate answer based on context.
        
        Args:
            query: User's query
            context: Retrieved context
            user_role: User's role
            
        Returns:
            Generated answer or None if error
        """
        try:
            with tracer.start_as_current_span("llm_generation") as span:
                span.set_attribute("gen_ai.system", "groq")
                span.set_attribute("gen_ai.request.model", self.llm_model)
                
                # If enabled, record the prompt content
                if os.getenv("AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED", "false").lower() == "true":
                    span.set_attribute("gen_ai.content.prompt", context[:1000]) # Sample context
                
                prompt = self._build_prompt(query, context, user_role)
                
                response = self.llm_client.chat.completions.create(
                    model=self.llm_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a helpful assistant for FinSolve Technologies. "
                                "Answer questions based ONLY on the provided context. "
                                "If the context doesn't contain the answer, say so. "
                                "Always cite your sources with document name and page number."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=self.llm_temperature,
                    max_tokens=self.llm_max_tokens,
                )
                
                answer = response.choices[0].message.content
                
                if answer and os.getenv("AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED", "false").lower() == "true":
                    span.set_attribute("gen_ai.content.completion", answer)
                    
                return answer
        
        except Exception as e:
            logger.error(f"Error generating answer with Groq: {str(e)}")
            return None
    
    def _build_prompt(
        self,
        query: str,
        context: str,
        user_role: str,
    ) -> str:
        """
        Build prompt for LLM.
        
        Args:
            query: User's query
            context: Retrieved context
            user_role: User's role
            
        Returns:
            Prompt string for LLM
        """
        return f"""
You are answering a question from a FinSolve employee with role: {user_role}.

CONTEXT (from company documents):
{context}

QUESTION: {query}

ANSWER:
Please provide a clear, concise answer based ONLY on the provided context.
Always cite the source document and page number for your information.
If the context doesn't contain the answer, say "I don't have information about that in the available documents."
"""
    
    @staticmethod
    def _get_department(user_role: str) -> str:
        """Get department name for a user role."""
        departments = {
            "employee": "General",
            "finance": "Finance",
            "engineering": "Engineering",
            "marketing": "Marketing",
            "c_level": "Executive",
        }
        return departments.get(user_role, "Unknown")


# Global pipeline instance
_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """
    Get singleton RAG pipeline instance.
    
    Returns:
        RAGPipeline instance
    """
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline
