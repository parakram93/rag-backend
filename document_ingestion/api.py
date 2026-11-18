import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from document_ingestion.chunking import ChunkStrategy, chunk_documents
from document_ingestion.database import get_session
from document_ingestion.ingest import (
    EmptyDocumentError, UnsupportedFileTypeError, extract_documents,
)
from document_ingestion.models import DocumentTable
from document_ingestion.qdrant import delete_document, store_chunks

router = APIRouter(prefix="/documents", tags=["ingestion"])


@router.post("/ingest", status_code=201)
def ingest(
    session: Annotated[Session, Depends(get_session)],
    file: Annotated[UploadFile, File()],
    strategy: Annotated[ChunkStrategy, Form()] = ChunkStrategy.RECURSIVE,
) -> dict[str, object]:
    
    data = file.file.read()
    try:
        docs = extract_documents(file.filename or "", data)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except EmptyDocumentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    chunks = chunk_documents(docs, strategy, size=500, overlap=50)
    doc_id = str(uuid.uuid4())

    num = store_chunks(doc_id, chunks)            
    try:
        
        record = DocumentTable(id=doc_id, filename = file.filename, chunk_strategy = strategy.value, num_chunks = num)
        session.add(record)
        session.commit()
            
    except Exception:
        session.rollback()
        delete_document(doc_id)                   
        raise

    return {"doc_id": doc_id, "filename": file.filename, "strategy": strategy.value, "chunks": num}