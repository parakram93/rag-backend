import os
from document_ingestion.embeddings import embedding_model

import cohere
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import MatchValue, FieldCondition, Filter
from pydantic import BaseModel
from document_ingestion.qdrant import COLL, client

load_dotenv()
MODEL = "command-a-03-2025"         
Message = dict[str, str]

class Hit(BaseModel):         
    text: str
    page: int | None = None


model = embedding_model
llm = cohere.ClientV2(api_key=os.environ["COHERE_API_KEY"])


#retrieving top 4 chunks from qdrant
def retrieve(query: str,doc_id: str | None = None, top_k: int = 4) -> list[Hit]:

    vector = model.encode(query).tolist()
    flt = (
        Filter(must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))])
        if doc_id
        else None
    )   
    results = client.query_points(
        collection_name=COLL,
        query=vector,
        query_filter=flt,
        limit=top_k,
        with_payload=True
    ).points
    
    return [
        Hit(text=str(p.payload["text"]), page=p.payload.get("page"))
        for p in results
        if p.payload
    ]

#system message
def build_messages(question: str, chunks: list[str], history: list[Message]) -> list[Message]:


    context = "\n".join(f"- {c}" for c in chunks)
    system_prompt = (
        "You are a helpful assistant. Answer ONLY using the context below. "
        "If the context does not contain the answer, reply exactly: "
        "\"I don't know based on the provided documents.\" "
        "Never use outside knowledge.\n\n"
        f"Context:\n{context}"
    )
    return [
        {"role": "system", "content": system_prompt},
        *history,                                   
        {"role": "user", "content": question},       
    ]

def answer(question: str, history: list[Message], doc_id : str | None = None) -> tuple[str, list[int]]:
    search_query = f"{history[-2]['content']} {question}" if len(history) >= 2 else question

    hits = retrieve(search_query, doc_id)  
    messages = build_messages(question, [h.text for h in hits], history) 
    response = llm.chat(model=MODEL, messages = messages)
    text = response.message.content[0].text
    pages = sorted({h.page for h in hits if h.page is not None})
    return text, pages