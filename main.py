from fastapi import FastAPI
from RAG.api import chat_router
from document_ingestion.api import router
from document_ingestion.database import Base, engine
from document_ingestion import models  

Base.metadata.create_all(engine)
app = FastAPI(title="RAG Backend")
app.include_router(router)
app.include_router(chat_router)