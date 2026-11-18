# RAG Backend (FastAPI)

Backend with two REST APIs: document ingestion (PDF/TXT) and a conversational RAG
API with Redis chat memory and LLM-driven interview booking.

## Stack
- FastAPI, Pydantic
- Qdrant: vector store for chunk embeddings
- SQLite via SQLAlchemy: document metadata and booking records
- Redis: chat history and in-progress booking state
- Cohere (`command-a-03-2025`): LLM
- sentence-transformers (`all-MiniLM-L6-v2`): embeddings
- pypdf: PDF text extraction
- LangChain text splitters (only `RecursiveCharacterTextSplitter`)

## Setup
1. Start Qdrant and Redis: `docker compose up -d`
2. Create a virtual environment and install dependencies:
   `python -m venv venv`, activate it, then `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set `COHERE_API_KEY`
4. Run: `uvicorn main:app --reload`
5. Open http://127.0.0.1:8000/docs

## APIs

### POST /documents/ingest
Takes .pdf or .txt files only. uses `recursive` or `sentence` chunking strategy.
Extracts text, chunks it, embeds the chunks, stores vectors in Qdrant and
metadata in SQL. Returns `doc_id`, filename, strategy and chunk count.
Errors: 415 for unsupported types, 422 for files with no extractable text.

### POST /chat
JSON body: `session_id`, `message`, optional `doc_id`.
Returns the answer and the page numbers of the chunks used.
The same endpoint handles interview booking: it detects the intent, collects
name, email, date and time across turns, validates them, and saves the booking.

## Design
- **Chunking:** `recursive` uses LangChain's RecursiveCharacterTextSplitter
  (paragraph, line, then word boundaries, with overlap). `sentence` is a custom
  packer that keeps whole sentences together up to a size limit.
- **Custom RAG:** embed the query, retrieve top-k chunks
  from Qdrant, build a prompt with the context and chat history, call the LLM.
  The prompt tells the model to answer only from the context.
- **Memory:** the last 10 messages per `session_id` are kept in Redis with a TTL.
  Follow-up questions work because history is passed back to the LLM.
- **Booking:** the LLM extracts fields as JSON, Pydantic validates them
  (email format, real calendar dates), and in-progress state is stored in
  Redis per session. Completed bookings are saved to SQL.
- **Write order:** vectors are written to Qdrant first, then the SQL row. If the
  SQL write fails, the chunks are deleted from Qdrant to avoid orphans.
- **Typing and structure:** Pydantic models for requests and responses, type hints
  throughout, and settings loaded from environment variables.

## Limitations
- A normal question asked in the middle of a booking is treated as booking input.
- Sentence splitting uses a regex and can split on abbreviations.
- Scanned PDFs are rejected because there is no OCR.
- Some values (chunk size, overlap) are still defined in code rather than settings.
