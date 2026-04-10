"""
FastAPI application for FinBot RAG system.
Exposes HTTP endpoints for chat, user management, and system diagnostics.
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from typing import Optional
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import sys

# Initialize Azure Monitor Tracing FIRST (Before project imports)
def init_azure_monitor():
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
    from opentelemetry import trace
    
    # Check both standard and common variants
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING") or os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING")
    
    if connection_string:
        connection_string = connection_string.strip("'\"")
        try:
            # Create a Resource to identify the service
            resource = Resource.create({SERVICE_NAME: "finbot-backend"})
            
            # Set up the provider with the resource
            provider = TracerProvider(resource=resource)
            
            # Configure the Azure Monitor Exporter manually for better visibility
            exporter = AzureMonitorTraceExporter(connection_string=connection_string)
            span_processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(span_processor)
            
            # Register the provider globally
            trace.set_tracer_provider(provider)
            
            print("INFO: Azure Monitor tracing initialized successfully (Manual Setup).")
            return True, connection_string
        except Exception as e:
            print(f"ERROR: Failed to initialize Azure Monitor Tracing: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, str(e)
    return False, "CONNECTION_STRING_NOT_FOUND"

AZURE_MONITOR_OK, AZURE_MONITOR_STATUS = init_azure_monitor()

from pipeline.rag_pipeline import get_rag_pipeline
from retrieval.user_auth import get_user_manager
from vector_store import get_vector_store
from ingestion.document_ingester import DocumentIngester
from config import DocumentCollection

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Logging setup remains as is


# ====================
# REQUEST/RESPONSE MODELS
# ====================

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    user_role: str
    query: str
    user_id: str = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str
    sources: list
    route: str
    user_role: str
    accessible_collections: list
    guardrail_flags: list = []
    guardrail_warnings: list = []
    rbac_denied: bool = False
    rbac_reason: Optional[str] = None


class UserInfo(BaseModel):
    """User information model."""
    username: str
    name: str
    role: str
    department: str
    accessible_collections: list[str] = []


class CollectionInfo(BaseModel):
    """Collection information model."""
    name: str
    description: str
    accessible_roles: list


# ====================
# INITIALIZATION
# ====================

async def startup_event():
    """Initialize application on startup."""
    logger.info("="*60)
    logger.info("FinBot RAG System Starting Up")
    logger.info("="*60)
    
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        logger.warning("GROQ_API_KEY not set!  Chat functionality will fail.")
    
    # Initialize vector store and check collections
    vector_store = get_vector_store()
    collections = vector_store.list_collections()
    logger.info(f"Available collections: {collections if collections else 'None (ingestion pending)'}")
    
    logger.info("FinBot RAG System Ready")
    logger.info("="*60)


async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("FinBot RAG System Shutting Down")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    await startup_event()
    yield
    await shutdown_event()


# ====================
# CREATE FASTAPI APP
# ====================

app = FastAPI(
    title="FinBot RAG API",
    description="Advanced RAG system with RBAC, hierarchical chunking, and guardrails",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument FastAPI app
if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI application instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI app: {str(e)}")


# ====================
# DIAGNOSTIC ENDPOINT
# ====================

@app.get("/api/diag")
async def diagnostic():
    """Diagnostic endpoint to check environment and tracing status."""
    conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING") or os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING")
    
    # Mask connection string
    masked = None
    if conn_str:
        conn_str_clean = conn_str.strip("'\"")
        masked = f"{conn_str_clean[:20]}...{conn_str_clean[-5:]}" if len(conn_str_clean) > 25 else "Too short"
        
    # Execute a manual test span to verify connectivity
    test_span_ok = False
    test_error = None
    try:
        from opentelemetry import trace
        test_tracer = trace.get_tracer("diagnostic.tracer")
        with test_tracer.start_as_current_span("Diagnostic-Test-Span") as span:
            span.set_attribute("diag.timestamp", str(sys.version))
            span.add_event("Handshake test")
            logger.info("Manual diagnostic span created.")
        
        # Force flush to ensure it is sent immediately
        provider = trace.get_tracer_provider()
        if hasattr(provider, "force_flush"):
            provider.force_flush()
            test_span_ok = True
    except Exception as e:
        test_error = str(e)
        logger.error(f"Manual span test failed: {test_error}")

    return {
        "azure_monitor_status": AZURE_MONITOR_STATUS,
        "azure_monitor_ok": AZURE_MONITOR_OK,
        "connection_string_found": conn_str is not None,
        "connection_string_masked": masked,
        "env_vars_keys": list(os.environ.keys()),
        "python_version": sys.version,
        "otel_libs_loaded": "opentelemetry" in sys.modules,
        "manual_test_span_sent": test_span_ok,
        "manual_test_error": test_error,
    }


# ====================
# CHAT ENDPOINT
# ====================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a user query through the RAG pipeline.
    
    Args:
        request: ChatRequest with user_role, query, and optional user_id
        
    Returns:
        ChatResponse with answer, sources, and metadata
    """
    try:
        # Validate user role
        valid_roles = ["employee", "finance", "engineering", "marketing", "c_level"]
        if request.user_role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid user role. Must be one of: {valid_roles}"
            )
        
        # Get RAG pipeline
        pipeline = get_rag_pipeline()
        
        # Process query
        rag_response = pipeline.answer_query(
            user_role=request.user_role,
            query_text=request.query,
            user_id=request.user_id,
        )
        print(rag_response)
        # Convert to response model
        return ChatResponse(
            answer=rag_response.answer,
            sources=rag_response.sources,
            route=rag_response.route,
            user_role=rag_response.user_role,
            accessible_collections=rag_response.accessible_collections,
            guardrail_flags=rag_response.guardrail_flags,
            guardrail_warnings=rag_response.guardrail_warnings,
            rbac_denied=rag_response.rbac_denied,
            rbac_reason=rag_response.rbac_reason,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        # Return a proper ChatResponse with error info instead of a 500,
        # so the frontend always has something to display.
        return ChatResponse(
            answer="I'm sorry, I encountered an unexpected error while processing your question. Please try again in a moment.",
            sources=[],
            route="error",
            user_role=request.user_role,
            accessible_collections=[],
            guardrail_flags=["server_error"],
            guardrail_warnings=[f"Internal error: {str(e)}"],
        )
    finally:
        # Force flush traces after each request during debugging/diag
        try:
            from opentelemetry import trace
            provider = trace.get_tracer_provider()
            if hasattr(provider, "force_flush"):
                provider.force_flush()
                logger.debug("OpenTelemetry traces force-flushed.")
        except Exception as flush_error:
            logger.warning(f"Failed to flush traces: {str(flush_error)}")


# ====================
# USER MANAGEMENT ENDPOINTS
# ====================

@app.get("/api/users", response_model=list[UserInfo])
async def list_users():
    """Get list of demo users for login screen."""
    try:
        user_manager = get_user_manager()
        users = user_manager.list_users()
        return [
            UserInfo(
                username=u.username,
                name=u.name,
                role=u.role.value,  # Use .value to get "finance" not "UserRole.FINANCE"
                department=u.department,
                accessible_collections=user_manager.get_user_accessible_collections(
                    u.role.value
                ),
            )
            for u in users
        ]
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/users/{username}")
async def get_user(username: str):
    """Get specific user information."""
    try:
        user_manager = get_user_manager()
        user = user_manager.get_user(username)
        
        if not user:
            raise HTTPException(status_code=404, detail=f"User not found: {username}")
        
        return {
            "username": user.username,
            "name": user.name,
            "role": user.role,
            "department": user.department,
            "accessible_collections": user_manager.get_user_accessible_collections(user.role),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ====================
# COLLECTIONS ENDPOINTS
# ====================

@app.get("/api/collections", response_model=list[CollectionInfo])
async def list_collections():
    """Get list of document collections."""
    try:
        from config import COLLECTION_CONFIGS
        
        collections = []
        for coll_enum in DocumentCollection:
            config = COLLECTION_CONFIGS.get(coll_enum)
            if config:
                collections.append(
                    CollectionInfo(
                        name=coll_enum.value,
                        description=config.get("description", ""),
                        accessible_roles=config.get("access_roles", []),
                    )
                )
        
        return collections
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/collections/{collection_name}")
async def get_collection_info(collection_name: str):
    """Get information about a specific collection."""
    try:
        from config import COLLECTION_CONFIGS
        
        # Find collection
        coll = None
        for c in DocumentCollection:
            if c.value == collection_name:
                coll = c
                break
        
        if not coll:
            raise HTTPException(status_code=404, detail=f"Collection not found: {collection_name}")
        
        config = COLLECTION_CONFIGS.get(coll)
        
        # Get vector store stats
        vector_store = get_vector_store()
        stats = vector_store.get_collection_stats(collection_name)
        
        return {
            "name": collection_name,
            "description": config.get("description", ""),
            "accessible_roles": config.get("access_roles", []),
            "chunks_count": stats.get("points_count", 0) if stats else 0,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ====================
# INGESTION ENDPOINT (Admin)
# ====================

@app.post("/api/admin/ingest")
async def ingest_documents():
    """
    Ingest all document collections.
    WARNING: Only use for demo/testing!
    """
    try:
        logger.info("Starting document ingestion...")
        
        ingester = DocumentIngester()
        results = ingester.ingest_all_collections()
        
        stats = ingester.verify_ingestion()
        
        return {
            "status": "success",
            "ingestion_results": results,
            "collection_stats": stats,
        }
    except Exception as e:
        logger.error(f"Error ingesting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


# ====================
# SYSTEM ENDPOINTS
# ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        vector_store = get_vector_store()
        collections = vector_store.list_collections()
        
        return {
            "status": "healthy",
            "collections_available": len(collections) > 0,
            "collections": collections,
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
            },
        )


@app.get("/api/info")
async def system_info():
    """Get system information."""
    try:
        return {
            "name": "FinBot RAG System",
            "version": "1.0.0",
            "features": [
                "Role-Based Access Control (RBAC)",
                "Hierarchical Document Chunking",
                "Semantic Query Routing",
                "Input/Output Guardrails",
                "RAGAs Evaluation Support",
            ],
            "available_roles": ["employee", "finance", "engineering", "marketing", "c_level"],
        }
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ====================
# ERROR HANDLERS
# ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
        },
    )


# ====================
# ROOT ENDPOINT
# ====================

@app.get("/")
async def root():
    """Root endpoint with API documentation."""
    return {
        "name": "FinBot RAG API",
        "version": "1.0.0",
        "description": "Advanced RAG system with RBAC, hierarchical chunking, and guardrails",
        "endpoints": {
            "chat": "POST /api/chat - Process a user query",
            "users": "GET /api/users - List demo users",
            "collections": "GET /api/collections - List document collections",
            "health": "GET /api/health - Health check",
            "info": "GET /api/info - System information",
            "ingest": "POST /api/admin/ingest - Ingest documents (admin only)",
        },
        "documentation": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting FinBot RAG API server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
