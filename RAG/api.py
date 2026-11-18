from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from document_ingestion.database import get_session
from RAG.booking import booking_in_progress, detect_intent, handle_booking
from RAG.memory import add_message, get_history
from RAG.rag import answer
from RAG.schema import ChatRequest, ChatResponse

chat_router = APIRouter(prefix="/chat", tags=["chat"])


@chat_router.post("", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Annotated[Session, Depends(get_session)],
) -> ChatResponse:
    if booking_in_progress(req.session_id) or detect_intent(req.message) == "booking":
        text = handle_booking(req.session_id, req.message, db)
        pages: list[int] = []
    else:
        text, pages = answer(req.message, get_history(req.session_id), req.doc_id)

    add_message(req.session_id, "user", req.message)
    add_message(req.session_id, "assistant", text)
    return ChatResponse(session_id=req.session_id, answer=text, pages=pages)