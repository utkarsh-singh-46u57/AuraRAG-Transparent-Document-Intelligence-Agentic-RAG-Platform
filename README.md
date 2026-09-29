# AuraRAG — Production-Grade Transparent Document Intelligence & Agentic RAG Platform

AuraRAG is a transparent, full-stack Document Intelligence and Agentic RAG platform designed to treat document context as verifiable evidence and tool execution as an authoritative runtime capability.

Unlike opaque chat-with-PDF prototypes, AuraRAG features **coordinate-aware text extraction**, **hybrid retrieval (BM25 + ChromaDB with Reciprocal Rank Fusion)**, **strict untrusted prompt isolation**, **native Google Gemini function calling**, and a **Glassmorphism Deep Purple/Black** UI that exposes retrieved chunks, confidence scores, and real-time tool execution logs.

---

## 1. System Architecture & Data Flow

```
                          ┌────────────────────────────────────────────────────────┐
                          │                 REACT FRONTEND (Vite)                  │
                          │  Glassmorphism UI | PDF Viewer | Live Clock | Stream   │
                          └───────────────────────────┬────────────────────────────┘
                                                      │ SSE / REST
                                                      ▼
                          ┌────────────────────────────────────────────────────────┐
                          │                  FASTAPI BACKEND API                   │
                          │   Session Middleware | Route Guards | Security Layer   │
                          └──────┬────────────────────┬────────────────────┬───────┘
                                 │                    │                    │
                 ┌───────────────┘                    │                    └────────────────┐
                 ▼                                    ▼                                     ▼
   ┌───────────────────────────┐        ┌───────────────────────────┐        ┌────────────────────────────┐
   │    DOCUMENT PIPELINE      │        │    AGENT & TOOL ENGINE    │        │      RAG RETRIEVAL HUB     │
   │  PyMuPDF Text & BBox      │        │  Tool Registry & Schemas  │        │  Hybrid Search (BM25 +     │
   │  Layout & Table Detection │        │  Native Gemini Functions: │        │  ChromaDB Dense Vectors)   │
   │  OCR Fallback Hook        │        │   - get_relative_date     │        │  Reciprocal Rank Fusion    │
   │  Recursive Chunking Engine│        │   - get_current_datetime  │        │  Context Deduplication &   │
   │  Embedding Generator      │        │   - search_document       │        │  Untrusted XML Sanitization│
   └─────────────┬─────────────┘        └─────────────┬─────────────┘        └──────────────┬─────────────┘
                 │                                    │                                     │
                 ▼                                    ▼                                     ▼
   ┌───────────────────────────┐        ┌───────────────────────────┐        ┌────────────────────────────┐
   │   PERSISTENT STORAGE      │        │   LLM PROVIDER GATEWAY    │        │     LOCAL VECTOR STORE     │
   │  Session PDF Storage      │        │  google-genai Modern SDK  │        │  ChromaDB / Qdrant Store   │
   │  In-Memory Session Meta   │        │  OpenAI / Fallback Client │        │  Metadata Filter Isolation │
   └───────────────────────────┘        └───────────────────────────┘        └────────────────────────────┘
```

---

## 2. Key Capabilities & Architectural Innovations

### 1. Modern Google GenAI SDK (`google-genai`) Function Calling
- Built on the modern Google GenAI library:
  ```python
  from google import genai
  from google.genai import types
  ```
- Tools defined via declarative Pydantic schemas with type enforcement.
- Server-intercepted function calling loop with streaming SSE events (`tool_start`, `tool_end`, `delta`, `done`).

### 2. Deterministic Timezone-Aware Tools
- `get_relative_date(days_offset: int, timezone: str)`: Deterministically calculates today, tomorrow, yesterday, or future/past offset dates without hallucination.
- `get_current_datetime(timezone: str)`: Live clock query across all standard IANA timezones (e.g. `Asia/Kolkata`, `America/New_York`, `UTC`).
- `search_document(query: str, document_id: str, top_k: int)`: Formalized retrieval tool callable directly by the model.

### 3. Layout-Aware PDF Ingestion & Coordinate Highlighting
- PyMuPDF (`fitz`) extracts text blocks along with normalized coordinate bounding boxes `[x0, y0, x1, y1]`.
- Low-density detection (<50 chars/page) flags potential scanned PDFs for OCR fallback.
- The frontend canvas PDF viewer automatically jumps to the cited page and overlays a glowing highlight bounding box on the referenced text passage.

### 4. Hybrid Retrieval & Reciprocal Rank Fusion (RRF)
- Dense semantic vector search via ChromaDB (`1 - cosine_distance`).
- Sparse lexical search via `rank-bm25` (BM25Okapi).
- Merged via Reciprocal Rank Fusion:
  $$RRF\_Score(d) = \frac{1}{60 + Rank_{dense}(d)} + \frac{1}{60 + Rank_{bm25}(d)}$$
- Deduplication and token budgeting to protect context windows.

### 5. Strict Anti-Injection XML Context Isolation
- Document text is isolated inside `<untrusted_document_context>` XML wrappers.
- All chunk content is sanitized: XML delimiter breakers (e.g. `</untrusted_document_context>`) are filtered to prevent model prompt breakouts.
- Strict system prompt instructs the model to treat document content purely as inert evidence.

### 6. Glassmorphism Purple & Black Design
- Bespoke cosmic dark palette (`#07060a` to `#0f0c1b`), frosted glass surfaces (`backdrop-blur-xl`), neon purple glow borders (`#a855f7`), and glowing cyan citation badges (`#06b6d4`).
- Real-time client synchronized timezone clock in the header.
- Slide-in Chunk Inspection Drawer displaying confidence match percentages and exact chunk IDs.

---

## 3. Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI** with **Uvicorn**
- **google-genai** (Google GenAI Official Modern SDK)
- **chromadb** (Local persistent vector database)
- **pymupdf** (High-speed coordinate extraction)
- **rank-bm25** (BM25 lexical search)
- **sse-starlette** (Server-Sent Events streaming)
- **pydantic v2** & **pydantic-settings**
- **pytz** (Timezone computation)
- **pytest** & **pytest-asyncio**

### Frontend
- **React 18** with **TypeScript** & **Vite**
- **Tailwind CSS** (Custom glassmorphism utilities)
- **Lucide Icons**
- **pdfjs-dist** (Canvas PDF rendering with coordinate highlight overlays)
- **react-markdown** & **remark-gfm**

---

## 4. Project Directory Structure

```
aurarag/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI entrypoint & middleware
│   │   ├── config.py                   # Environment settings & defaults
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes_llm.py           # Key validation & model listing
│   │   │   ├── routes_documents.py     # Upload, status, chunks, file serving
│   │   │   ├── routes_chat.py          # Chat streaming, RAG routing, SSE
│   │   │   └── routes_tools.py         # Direct tool endpoints (health/time)
│   │   ├── core/
│   │   │   ├── security.py             # Prompt sanitization, input scrubbers
│   │   │   ├── session.py              # Ephemeral session manager
│   │   │   └── exceptions.py           # Custom API exceptions
│   │   ├── services/
│   │   │   ├── document_parser.py      # PyMuPDF parser + coordinate extractor
│   │   │   ├── chunking.py             # Semantic recursive chunking logic
│   │   │   ├── embeddings.py           # EmbeddingProvider abstraction
│   │   │   ├── vector_store.py         # ChromaDB interface + hybrid search
│   │   │   └── rag_engine.py           # Context assembly & untrusted wrappers
│   │   ├── tools/
│   │   │   ├── registry.py             # Central tool registry & dispatcher
│   │   │   ├── date_time_tools.py      # get_relative_date & get_current_datetime
│   │   │   └── search_tool.py          # search_document tool
│   │   ├── providers/
│   │   │   ├── base.py                 # Abstract LLMProvider base class
│   │   │   ├── gemini_provider.py      # Native Gemini function calling implementation
│   │   │   └── openai_provider.py      # OpenAI function calling fallback
│   │   └── models/
│   │       ├── schemas.py              # Pydantic request/response schemas
│   │       └── domain.py               # Document, Chunk, and Citation models
│   ├── tests/
│   │   ├── conftest.py                 # Synthetic Apollo and Injection PDF fixtures
│   │   ├── test_ingestion.py           # PyMuPDF, chunking, and session tests
│   │   ├── test_tools.py               # Relative date and clock unit tests
│   │   ├── test_rag.py                 # Hybrid search, RRF, and isolation tests
│   │   ├── test_security.py            # Key masking and sanitizer tests
│   │   └── test_acceptance.py          # Full acceptance test suite (A–G and 1–5)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx          # Live clock, model badge, connection status
│   │   │   │   └── Sidebar.tsx         # LLM Config, Document Upload, Mode toggles
│   │   │   ├── chat/
│   │   │   │   ├── ChatContainer.tsx   # Message list & auto-scroll
│   │   │   │   ├── MessageItem.tsx     # Markdown, citations, tool badges
│   │   │   │   ├── ChatInput.tsx       # Prompt textarea & quick suggestion pills
│   │   │   │   └── ToolActivity.tsx    # Live tool execution banners
│   │   │   ├── inspection/
│   │   │   │   ├── ChunkDrawer.tsx     # Retrieved chunk inspection drawer
│   │   │   │   └── ScoreBadge.tsx      # Relevance confidence visualizer
│   │   │   ├── pdf/
│   │   │   │   └── PDFViewerModal.tsx  # Canvas PDF rendering with coordinate highlights
│   │   │   └── ui/
│   │   │       ├── GlassCard.tsx       # Reusable frosted glass component
│   │   │       └── LiveClock.tsx       # Header live timezone clock
│   │   ├── context/
│   │   │   └── AppContext.tsx          # Global session, doc, and config state
│   │   ├── services/
│   │   │   ├── api.ts                  # REST API client
│   │   │   └── sse.ts                  # SSE event stream consumer
│   │   ├── types/
│   │   │   └── index.ts                # TypeScript interfaces
│   │   ├── App.tsx
│   │   ├── index.css                   # Tailwind theme & glass styles
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 5. API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/llm/verify` | Validates API key, tests connection, returns model availability. |
| `POST` | `/api/documents/upload` | Multipart form upload. Returns `document_id`, pages, and chunks. |
| `GET` | `/api/documents/status/{doc_id}` | Returns indexing status (`ready`, `processing`, `error`). |
| `GET` | `/api/documents/{doc_id}/chunks` | Returns paginated list of extracted chunks with coordinates. |
| `DELETE` | `/api/documents/{doc_id}` | Cascading delete: removes raw PDF, chunks, and vector embeddings. |
| `GET` | `/api/documents/{doc_id}/file` | Serves the PDF file bytes for in-browser canvas rendering. |
| `POST` | `/api/chat/stream` | Primary SSE endpoint. Streams tokens, tool call events, and citations. |
| `GET` | `/api/tools/time` | Direct health check for timezone date/time calculations. |
| `POST` | `/api/tools/relative-date` | Direct calculation of relative dates. |
| `GET` | `/api/tools/list` | Returns registered tool declarations and parameter schemas. |

### SSE Stream Protocol Format (`/api/chat/stream`)
```
event: citation
data: {"citations": [{"chunk_id": "chk_p01_b01_001", "page": 1, "score": 0.89, "text": "...", "bbox": [...]}]}

event: tool_start
data: {"tool": "get_relative_date", "args": {"days_offset": 4, "timezone": "Asia/Kolkata"}}

event: tool_end
data: {"tool": "get_relative_date", "result": {"success": true, "calculated_date": "2026-10-02", "day_of_week": "Friday"}}

event: delta
data: {"text": "According to the calculations..."}

event: done
data: {"finish_reason": "stop"}
```

---

## 6. Running the Automated Test Suite

AuraRAG includes 25 automated unit and acceptance tests covering:
- **Test A:** Document-grounded QA with factual verification & citation scoring (> 0.65).
- **Test B:** General knowledge fallback without hallucinated document citations.
- **Tests 1–4:** Relative date calculations (today, tomorrow, yesterday, +4 days).
- **Test 5:** Authoritative timezone datetime query (`Asia/Kolkata`).
- **Test E:** Chunk inspection with normalized bounding boxes and page numbers.
- **Test F:** Prompt injection defense against malicious PDF instructions.
- **Test G:** Cascading document deletion from filesystem and ChromaDB.

Run tests using pytest:
```bash
cd backend
pytest tests/ -v
```

Expected output:
```
============================= test session starts =============================
collected 25 items

tests/test_acceptance.py::test_acceptance_document_grounded_qa PASSED    [  4%]
tests/test_acceptance.py::test_acceptance_general_knowledge PASSED       [  8%]
tests/test_acceptance.py::test_acceptance_relative_date_tool PASSED      [ 12%]
tests/test_acceptance.py::test_acceptance_timezone_datetime_tool PASSED  [ 16%]
tests/test_acceptance.py::test_acceptance_chunk_inspection PASSED        [ 20%]
tests/test_acceptance.py::test_acceptance_prompt_injection_defense PASSED [ 24%]
tests/test_acceptance.py::test_acceptance_document_deletion PASSED       [ 28%]
tests/test_ingestion.py::test_document_parser_coordinates PASSED         [ 32%]
tests/test_ingestion.py::test_chunking_structural_integrity PASSED       [ 36%]
tests/test_ingestion.py::test_session_manager_registration PASSED        [ 40%]
tests/test_rag.py::test_hybrid_search_and_rrf PASSED                     [ 44%]
tests/test_rag.py::test_rag_engine_untrusted_xml_isolation PASSED        [ 48%]
tests/test_security.py::test_api_key_masking PASSED                      [ 52%]
tests/test_security.py::test_scrub_sensitive_logs PASSED                 [ 56%]
tests/test_security.py::test_sanitize_user_input PASSED                  [ 60%]
tests/test_security.py::test_sanitize_chunk_for_xml PASSED               [ 64%]
tests/test_security.py::test_validate_session_id PASSED                  [ 68%]
tests/test_security.py::test_injection_detection PASSED                  [ 72%]
tests/test_tools.py::test_relative_date_today PASSED                     [ 76%]
tests/test_tools.py::test_relative_date_tomorrow PASSED                  [ 80%]
tests/test_tools.py::test_relative_date_yesterday PASSED                 [ 84%]
tests/test_tools.py::test_relative_date_future_offset PASSED             [ 88%]
tests/test_tools.py::test_current_datetime_timezone PASSED               [ 92%]
tests/test_tools.py::test_tool_registry_execution PASSED                 [ 96%]
tests/test_tools.py::test_tool_registry_validation_error PASSED          [100%]

============================= 25 passed in 6.27s ==============================
```

---

## 7. Local Development Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 1. Start the Backend
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The API documentation is accessible at `http://localhost:8000/docs`.

### 2. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 8. Launching with Docker Compose

To launch the full stack with a single command:
```bash
docker-compose up --build
```
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
