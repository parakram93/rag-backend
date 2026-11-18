from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from .embeddings import embedding_model
import numpy as np
import pickle
import os
from pathlib import Path
import io
from document_ingestion.chunking import chunk_documents


class UnsupportedFileTypeError(Exception):
    pass

class EmptyDocumentError(Exception):
    pass

def extract_documents(filename: str, data: bytes) -> list[Document]:
    suffix = Path(filename).suffix.lower()
    docs: list[Document] = []

    if suffix == ".txt":
        text = data.decode("utf-8", errors="replace")
        if text.strip():
            docs.append(Document(page_content=text, metadata={"source": filename}))

    elif suffix == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                docs.append(
                    Document(page_content=text, metadata={"source": filename, "page": i + 1})
                )
    else:
        raise UnsupportedFileTypeError(f"Unsupported file type: {suffix or 'none'}")

    if not docs:
        raise EmptyDocumentError("No extractable text (scanned PDF or empty file?)")
    
    return docs


