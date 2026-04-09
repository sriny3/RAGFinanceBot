# FinBot Backend Architecture - Complete Guide

## Overview

The FinBot RAG backend is organized around a **layered architecture** with clear separation of concerns. Each module handles a specific domain of the system, allowing for maintainability, testability, and scalability.

```
REQUEST
  ↓
[main.py] - FastAPI endpoints
  ↓
[pipeline/rag_pipeline.py] - Orchestration
  ├─ [guardrails/input_guards.py] - Validate queries
  ├─ [routing/router.py] - Route query to collection
  ├─ [retrieval/rbac_retriever.py] - RBAC-enforced retrieval
  ├─ [Groq API] - Generate answer
  ├─ [SentenceTransformer] - Generate embeddings
  └─ [guardrails/output_guards.py] - Validate response
  ↓
RESPONSE
```

---

## Directory Structure & File Organization

### 1. **Root Level Files**

#### `main.py` (FastAPI Application)
- **Purpose**: HTTP API entry point
- **Responsibility**: 
  - Define endpoints (routes)
  - Request/response validation
  - CORS setup
  - Lifecycle management
- **Key Endpoints**:
  - `POST /api/chat` - Main chat endpoint
  - `GET /api/health` - System health check
  - `GET /api/users/{username}` - Get user info
  - `POST /admin/create-user` - Admin user creation
  - `POST /admin/ingest` - Document ingestion trigger

**Key Pattern**: Controllers/Handlers that delegate to services

---

#### `config.py` (Configuration & Constants)
- **Purpose**: Centralize all configuration
- **Contains**:
  - User roles enum (EMPLOYEE, FINANCE, ENGINEERING, MARKETING, C_LEVEL)
  - Document collections enum (GENERAL, FINANCE, ENGINEERING, MARKETING, HR)
  - **CRITICAL**: `ROLE_COLLECTION_ACCESS` mapping (defines RBAC rules)
  - Demo users for testing
  - LLM config (model, temperature, tokens)
  - Retrieval config (top_k, score_threshold)

**Key Pattern**: Single source of truth for all constants

**Example RBAC Rule**:
```python
ROLE_COLLECTION_ACCESS = {
    "employee": ["general"],
    "finance": ["general", "finance"],
    "engineering": ["general", "engineering"],
    "c_level": ["general", "finance", "engineering", "marketing", "hr"],
}
```

---

#### `vector_store.py` (Qdrant Vector Database)
- **Purpose**: Interface to Qdrant vector database (Cloud or Local)
- **Responsibility**:
  - Connect to Qdrant Cloud for persistent, shared storage
  - Fallback to local persistent storage for disconnected development
  - Create/manage vector collections and enforce RBAC filters
- **Key Metadata Fields**:
  - `access_roles`: Which roles can access this chunk
  - `collection_name`: Which collection (finance, engineering, etc.)
  - `source_file`: Original document
  - `chunk_position`: Position in hierarchical structure

**Key Pattern**: Singleton pattern (single instance per app)

---

#### `metadata_schema.py` (Data Models)
- **Purpose**: Pydantic models for data validation
- **Key Classes**:
  - `Chunk` - Represents a searchable document chunk
  - `RAGResponse` - Full pipeline response
  - `QueryMetadata` - Metadata about the query
  - `RetrievalResult` - Retrieval layer output

**Key Pattern**: Schema validation & type safety

---

### 2. **Pipeline Module** (`pipeline/`)

#### `rag_pipeline.py` (Orchestration Engine)
- **Purpose**: Orchestrate the entire RAG flow
- **Thought Process**: 
  - A query goes through 5 distinct stages
  - Each stage has a specific responsibility
  - Each stage can fail independently and is logged

**5-Stage Pipeline**:

**Stage 1: Input Validation (Guardrails)**
```
Query → rate_limit check → injection detection → OffTopic check → PII check
        ↓ If fails, return error immediately
```

**Stage 2: Semantic Routing**
```
Query → Router (semantic-router) → Select collection
        "Show me sales data" → Route to FINANCE collection
        "How does the API work" → Route to ENGINEERING collection
```

**Stage 3: RBAC-Enforced Retrieval**
```
User Role + Selected Collection → Check access → Query vector store
        Employee wants FINANCE → DENIED
        Finance user wants FINANCE → ALLOWED → Retrieve chunks
```

**Stage 4: LLM Generation**
```
Question + Retrieved Chunks → Groq (Llama 3.3 70B) → Generate answer
        Uses retrieved chunks as context (RAG)
```

**Stage 5: Output Validation (Guardrails)**
```
Generated Answer → Check for hallucinations → Check for missing citations
        ↓ If issues detected, flag in response
```

**Return Complete Response**:
- `answer`: The generated response
- `sources`: Which chunks were used
- `route`: Which collection was queried
- `accessible_collections`: What user can access
- `guardrail_flags`: Any warnings/issues detected
- `rbac_denied`: Was access denied?

**Key Pattern**: Pipeline Pattern (chain of processors)

---

### 3. **Routing Module** (`routing/`)

#### `router.py` (Semantic Query Routing)
- **Purpose**: Determine which collection a query should search
- **Technology**: SemanticRouter (ML-based routing)
- **Examples**:
  ```
  "What are Q4 financials?" → FINANCE
  "How do I set up the API?" → ENGINEERING
  "What's our market strategy?" → MARKETING
  "What are company policies?" → GENERAL
  ```

#### `semantic_router_config.py` (Router Training Data)
- **Purpose**: Define routes and training examples
- **Contents**: Route definitions with example queries for each route
- **How It Works**: Semantic router learns from examples to categorize new queries

**Key Pattern**: Configuration-driven machine learning

---

### 4. **Retrieval Module** (`retrieval/`)

#### `rbac_retriever.py` (RBAC-Enforced Vector Search)
- **Purpose**: Retrieve chunks while enforcing access control
- **Critical Logic**:
  ```
  1. Get user's accessible collections (from config)
  2. Validate requested collections against user's access
  3. Search vector store ONLY in allowed collections
  4. Return chunks user is authorized to see
  ```

**Key Principle**: RBAC filter is applied at vector store level, not post-processing

**Examples**:
- Employee asks for FINANCE data → Denied, no chunks returned
- Finance user asks for FINANCE data → Allowed, chunks returned with access roles verified

**Key Pattern**: Authorization layer (middleware pattern)

---

#### `user_auth.py` (User Management)
- **Purpose**: User authentication & authorization
- **Responsibility**:
  - Store user profiles (role, department, etc.)
  - Map roles to accessible collections (using config.py)
  - Validate user roles
- **Demo Users**: Pre-defined users for testing

**Key Pattern**: Identity & Permissions service

---

### 5. **Guardrails Module** (`guardrails/`)

#### `input_guards.py` (Input Validation)
- **Purpose**: Validate and sanitize user input BEFORE processing
- **Checks**:
  - **Rate Limiting**: Max queries per user per time period
  - **Injection Detection**: SQL/prompt injection attempts
  - **Off-Topic Detection**: Is query relevant to knowledge base?
  - **PII Detection**: Does query ask for sensitive data?

**Examples**:
```
Query: "; DROP TABLE users; --" 
→ Detected as injection → Rejected

Query: "What's my credit card number?"
→ Detected as PII request → Rejected

Query: "Tell me a joke"
→ Detected as off-topic → Rejected

Query: "Show me Q4 sales"
→ Passes all checks → Continue to routing
```

**Key Pattern**: Defense-in-depth (multiple checks)

---

#### `output_guards.py` (Output Validation)
- **Purpose**: Validate LLM response BEFORE returning to user
- **Checks**:
  - **Hallucination Detection**: Is answer grounded in source documents?
  - **Citation Quality**: Are sources properly cited?
  - **Completeness**: Does answer address the query?

**Examples**:
```
Answer contains facts not in source docs
→ Flag as potential hallucination → Warn user

Answer references sources that weren't used
→ Flag as citation error → Warn user
```

**Key Pattern**: Quality assurance layer

---

### 6. **Ingestion Module** (`ingestion/`)

#### `docling_parser.py` (Document Parsing)
- **Purpose**: Parse complex documents (PDF, DOCX, Markdown)
- **Responsibility**:
  - Convert documents to structured text
  - Preserve document hierarchy (sections, subsections, etc.)
  - Extract metadata (titles, headings, structure)
- **Output**: Parsed document with hierarchical structure

**Key Pattern**: Standard parser pattern

---

#### `hierarchical_chunker.py` (Smart Chunking)
- **Purpose**: Break documents into optimal chunks
- **Thought Process Behind Chunking**:
  ```
  Raw Document (10+ pages)
    ↓
  Split by sections (respects hierarchy)
    ↓
  Split by semantic meaning (paragraphs, lists)
    ↓
  Create recursive chunks (overlap for context)
    ↓
  Tag chunks with metadata (section, source, role access)
    ↓
  Final Chunks (good context, minimal overlap)
  ```

**Why Hierarchical?** 
- Maintains document structure
- Preserves context (related info together)
- Enables collection-level access control
- Improves retrieval relevance

**Key Pattern**: Recursive chunking

---

#### `document_ingester.py` (Orchestration of Ingestion)
- **Purpose**: Coordinate parsing → chunking → embedding → storage
- **Pipeline**:
  ```
  Document → Parse (docling_parser)
           → Chunk (hierarchical_chunker)
           → Generate embeddings (SentenceTransformer locally)
           → Tag with access roles (from config)
           → Store in vector DB (Qdrant)
  ```

**Key Pattern**: Pipeline pattern applied to ingestion

---

## Design Patterns Used

### 1. **Layered Architecture**
Each layer has a specific responsibility and depends on layers below, but not above:
```
API Layer (main.py)
    ↓
Business Logic Layer (pipeline/)
    ↓
Data Access Layer (retrieval/, vector_store/)
    ↓
External Services (Groq, Qdrant)
```

### 2. **Singleton Pattern**
Single instances of expensive resources:
- Vector store (`get_vector_store()`)
- RAG pipeline (`get_rag_pipeline()`)
- User manager (`get_user_manager()`)

### 3. **Pipeline Pattern**
Processes flow through stages:
- RAG pipeline (input → routing → retrieval → LLM → output)
- Ingestion pipeline (parse → chunk → embed → store)

### 4. **Factory Pattern**
Create instances via factory functions:
```python
pipeline = get_rag_pipeline()
retriever = get_rbac_retriever()
router = get_router()
```

### 5. **Configuration-Driven Design**
Behavior controlled by `config.py`:
- Collection access rules
- User roles
- LLM settings
- No hardcoded values

### 6. **Authorization Layer**
RBAC enforced at retrieval layer:
- Not post-filtering
- Vetted at vector store level
- Cannot bypass

---

## Data Flow Example: User Query

```
User: "Show me the Q4 sales report"
Role: finance

1. REQUEST
   POST /api/chat
   { "query": "Show me the Q4 sales report", "user_role": "finance" }

2. MAIN.PY (FastAPI)
   Validates request format, calls pipeline.answer_query()

3. PIPELINE - STAGE 1: INPUT GUARDS
   ✓ Not a rate limit violation
   ✓ Not an injection attack
   ✓ Not off-topic
   ✓ No PII request

4. PIPELINE - STAGE 2: ROUTING
   Query → Router → "This is about SALES/FINANCE"
   Route: FINANCE collection

5. PIPELINE - STAGE 3: RBAC RETRIEVAL
   User role: finance
   Requested collection: FINANCE
   ✓ finance role CAN access FINANCE collection
   Query Qdrant ONLY in FINANCE collection
   Returns: [chunk1, chunk2, chunk3] (Q4 sales data)

6. PIPELINE - STAGE 4: LLM GENERATION
   Prompt: context + query + instructions
   "Based on the Q4 sales data below, answer: Show me the Q4 sales report"
   Groq generates comprehensive answer

7. PIPELINE - STAGE 5: OUTPUT GUARDS
   ✓ Answer is grounded in source documents
   ✓ Sources are properly cited
   ✓ No hallucinations detected

8. RESPONSE
   {
     "answer": "Q4 sales totaled $4.2M...",
     "sources": [chunk1, chunk2, chunk3],
     "route": "finance",
     "user_role": "finance",
     "accessible_collections": ["general", "finance"],
     "guardrail_flags": [],
     "rbac_denied": false
   }
```

---

## RBAC Enforcement Example

### Scenario 1: Authorized Access
```
User: emp_john
Role: employee
Query: "Company policies"

RBAC Check:
- Employee can access: [general]
- Query routed to: general ✓
- Allowed collections: general ✓
→ Retrieval succeeds
```

### Scenario 2: Unauthorized Access
```
User: emp_john
Role: employee
Query: "What are company financials?"

RBAC Check:
- Employee can access: [general]
- Query routed to: finance ✗
- Allowed collections: general ✗
→ RBAC DENIED
→ No chunks retrieved
→ Response: "You don't have access to financial data"
```

---

## Key Design Decisions

### 1. **Why Semantic Routing?**
- Automatically routes queries to right collection
- No manual labeling needed
- Scales with new collections

### 2. **Why Hierarchical Chunking?**
- Preserves document context
- Enables collection-level access control
- Improves relevance

### 3. **Why RBAC at Vector Store Level?**
- Cannot be bypassed
- Single source of truth
- Efficient (filters at query time)

### 4. **Why Separate Input/Output Guards?**
- Defense in depth
- Prevents malicious input
- Ensures answer quality
- Auditable (logged)

### 5. **Why Singleton Pattern?**
- Vector store connections are expensive
- LLM client setup is expensive
- Router models take time to load
- Reuse same instance across requests

---

## Summary

The backend is architected as a **layered pipeline** where:

1. **Configuration** (`config.py`) is the single source of truth for RBAC rules
2. **API** (`main.py`) is the thin HTTP layer
3. **Pipeline** (`pipeline/`) orchestrates the flow
4. **Guardrails** protect against bad input and bad output
5. **Routing** directs to correct collection
6. **Retrieval** enforces access control
7. **Ingestion** prepares documents for search

Each component is **focused**, **testable**, and **replaceable**. This design enables building a robust, secure RAG system that demonstrates enterprise-grade RBAC and quality assurance patterns.
