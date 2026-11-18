import re
from enum import Enum
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class ChunkStrategy(str, Enum):
    RECURSIVE = "recursive"
    SENTENCE = "sentence"


def recursive_chunks(docs: list[Document], size: int, overlap: int) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap)
    return splitter.split_documents(docs)


def sentence_chunks(docs: list[Document], size: int) -> list[Document]:
    result: list[Document] = []
    for doc in docs:
        text = re.sub(r"\s+", " ", doc.page_content).strip()
        sentences = re.split(r"(?<=[.!?]) ", text)
        current = ""
        for s in sentences:
            if current and len(current) + 1 + len(s) > size:
                result.append(Document(page_content=current, metadata=doc.metadata))
                current = s
            else:
                current = f"{current} {s}".strip()
        if current:
            result.append(Document(page_content=current, metadata=doc.metadata))
    return result


def chunk_documents(
    docs: list[Document], strategy: ChunkStrategy, size: int, overlap: int
) -> list[Document]:
    if strategy is ChunkStrategy.RECURSIVE:
        return recursive_chunks(docs, size, overlap)
    return sentence_chunks(docs, size)