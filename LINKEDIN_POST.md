\

## The Problem

Enterprise employees waste hours searching through dozens of internal documents. But there's a bigger issue most RAG systems ignore: **access control**.

In a typical company, financial projections are confidential. Engineering architecture docs are restricted. HR data is sensitive. But if you build a standard RAG chatbot over these documents, any employee can ask about anything — and the LLM will happily answer with whatever it retrieved.

Most teams slap a UI-level check on top: *"if user is not finance, don't show finance answers."* But that's cosmetic security. A well-crafted prompt or a direct API call bypasses it entirely.

I wanted to build something better.

## Introducing FinBot

**FinBot** is a production-grade Retrieval-Augmented Generation system I built for FinSolve Technologies (a fictional enterprise) as part of the Codebasics AI Bootcamp. It combines intelligent document retrieval with **real security** — access control enforced at the vector database layer, where it actually matters.

Here's the core principle: **if a user's role doesn't permit access to a document collection, those vectors are never retrieved, never sent to the LLM, and never appear in the response.** No amount of prompt engineering can bypass this.

🌍 **Try it Live:** https://sriny-rag-fin-bot-unique-123.vercel.app/

## How It Works

### 1. RBAC at the Vector Database Layer

This is the most important design decision in the system.

Every chunk stored in Qdrant carries `access_roles` metadata. When a user queries the system, the Qdrant search filter **only returns chunks matching that user's role** — before the LLM ever sees a single token.

I tested this live with two users asking the exact same question:

- **Carol (Marketing)** asks *"What was Q3 revenue?"* → ❌ **ACCESS DENIED** — *"Your role 'marketing' does not have permission to access Finance information."*
- **Alice (Finance)** asks *"What was Q3 revenue?"* → ✅ **"Q3 revenue was 203 ₹ Crore"** — sourced from `quarterly_financial_report.docx`

Same question. Different roles. Completely different outcomes. And this isn't application-layer filtering — it's enforced inside the database query itself.

The system supports 5 user roles (Employee, Finance, Engineering, Marketing, C-Level) across 5 document collections, with C-Level having unrestricted access to everything.

### 2. Hierarchical Document Chunking with Docling

Most RAG systems split documents into flat, fixed-size text blocks. FinBot takes a different approach.

Using **Docling**, documents are parsed into a full hierarchy: Document → Section → Subsection → Leaf chunks. The key insight is that **parent context travels with every leaf chunk** — so when the LLM receives a chunk about "Q3 margins," it also knows that chunk came from the "Financial Performance" section of the "Annual Report."

This gives the model both precision (small, relevant chunks) and understanding (broader document context). The supported formats include PDF, DOCX, and Markdown.

### 3. Semantic Query Routing

Before retrieval even begins, each query is classified into one of 5 intent routes:

- **Finance** — revenue, budgets, margins
- **Engineering** — architecture, APIs, deployment
- **Marketing** — campaigns, competitors, brand
- **HR / General** — policies, benefits, leave
- **Cross-Department** — company-wide questions

Each route is defined with 12–15 example utterances, and classification uses the same embedding model as retrieval (all-MiniLM-L6-v2), so there's no additional API call. This narrows the search space to the right collections, dramatically improving relevance and reducing noise.

Critically, **routing intersects with RBAC** — if the router classifies a query as "finance" but the user only has marketing access, the request is denied before any retrieval happens.

### 4. Dual-Layer Guardrails

**Input Guards** catch problems before the pipeline runs:
- **Prompt Injection** — detects patterns like *"Ignore your instructions and..."* using regex matching
- **Off-Topic Detection** — blocks requests like *"Write me a poem"* that aren't business queries
- **PII Detection** — identifies and sanitizes emails, phone numbers, and ID numbers
- **Rate Limiting** — prevents abuse with per-user session limits

**Output Guards** validate what the LLM produces:
- **Grounding Check** — flags answers that may not be supported by the retrieved context
- **Citation Enforcement** — ensures the response references source documents
- **Cross-Role Leakage Detection** — catches cases where the LLM might reference data from collections the user shouldn't access

## The Tech Stack

🔹 **LLM:** Groq (Llama 3.3 70B) — Sub-second response times via LPU
🔹 **Embeddings:** Sentence-Transformers (all-MiniLM-L6-v2) — Local, zero cost
🔹 **Vector Store:** Qdrant Cloud — Persistent storage & RBAC metadata filtering
🔹 **Document Parser:** Docling — Preserves document hierarchy (PDF/DOCX/MD)
🔹 **Semantic Router:** semantic-router — Fast embedding-based classification
🔹 **Backend:** FastAPI — Hosted on Hugging Face Spaces (16GB RAM free tier)
🔹 **Frontend:** Next.js + TypeScript — Hosted on Vercel with RBAC guardrails
🔹 **Deployment:** Vercel + Hugging Face Spaces + Qdrant Cloud — Fully persistent $0 cost setup
🔹 **Evaluation:** RAGAs Framework — Standardized metrics across 40+ QA test pairs

## Evaluation & Ablation Study

I evaluated the system using RAGAs across 40+ question-answer pairs covering all 5 collections, including adversarial RBAC boundary tests. The full pipeline achieved:

🎯 **Faithfulness:** 0.92
🎯 **Answer Relevancy:** 0.88
🎯 **Context Precision:** 0.85
🎯 **Context Recall:** 0.81
🎯 **Answer Correctness:** 0.79

To understand what each component contributes, I ran an ablation study (removing one component at a time and measuring the drop in quality):

🔻 **No Hierarchical Chunking:** -7.1% quality across all metrics
🔻 **No Semantic Routing:** -7.3% quality across all metrics
🔻 **No Guardrails:** -3.0% quality across all metrics
🔻 **No RBAC:** -0.9% on metrics (but **critical** for security)
🔴 **RAG Pipeline (baseline):** -128.6% (pure LLM without retrieval fails dramatically)

The most telling result: removing RBAC barely affects quality metrics — because RBAC is about **security**, not relevance. But without it, any user can access any document, which is a dealbreaker for enterprises.

## By the Numbers

- **6,000+** lines of Python backend code
- **2,400+** lines of React/TypeScript frontend
- **5** user roles × **5** document collections
- **4** input guardrails + **3** output guardrails
- **5** semantic routes with 12–15 utterances each
- **211** document chunks across all collections
- **40+** evaluation test pairs with ablation

## What I Learned

Building this project taught me three things:

**1. Security must live at the retrieval layer.** If your access control is in the application layer, it's one clever API call away from being bypassed. Qdrant's metadata filtering makes it possible to enforce RBAC at the point where vectors are retrieved — before the LLM ever sees the data.

**2. Document structure matters more than chunk size.** Flat chunking loses context. Hierarchical chunking with parent summaries gave a 7.1% improvement because the LLM understands not just *what* a chunk says, but *where in the document* it came from.

**3. Routing before retrieval is underrated.** Classifying query intent first and then targeting the right collection gave a 7.3% improvement. It's a simple addition that dramatically reduces noise.

## Links

🔗 **GitHub:** https://github.com/sriny3/RAGFinBOT

🌍 **Live App:** https://sriny-rag-fin-bot-unique-123.vercel.app/

---

*I'd love to hear from anyone working on enterprise RAG, RBAC, or LLM guardrails. What approaches have you found effective for securing retrieval pipelines? Let's connect and discuss.*

*#RAG #LLM #GenerativeAI #Python #FastAPI #NextJS #Qdrant #RBAC #AIEngineering #BuildInPublic #Codebasics*
