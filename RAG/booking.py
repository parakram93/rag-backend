import json
from datetime import date, time
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr, ValidationError
from document_ingestion.models import BookingTable
from sqlalchemy.orm import Session
from RAG.rag import MODEL, llm
from RAG.memory import r

load_dotenv()

co = llm
BOOKING_TTL = 1800
QUESTIONS = {
    "name": "What is your full name?",
    "email": "What is your email address?",
    "interview_date": "Which date would you like? (e.g. 2026-11-25)",
    "interview_time": "What time would you like? (e.g. 14:30)",
}
class BookingState(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    interview_date: date | None = None
    interview_time: time | None = None



def llm_json(system: str, user: str) -> dict[str, str | None]:
    resp = co.chat(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(resp.message.content[0].text)


def detect_intent(message: str) -> str:
    """Return 'booking' or 'question'."""
    system_message = (
        """You are a helpful assistant. Answer only the things that i write below. \n\n
        you will be given the message and you will have to tell if the intent of the user is for booking purpose or not that tells intent is booking or question",\n\n
        The message should be in the following format. {"intent" : "booking" } or {"intent" : "question"} """
      
    )
    result = llm_json(system_message, message)
    intent = result.get("intent", "question")
    return intent


def extract_fields(message: str) -> dict[str, str | None]:
    """Return keys name, email, interview_date (YYYY-MM-DD), interview_time (HH:MM); null if absent."""

    
    today = date.today().isoformat()

    system = f"""
    You are a booking information extraction assistant.

    Today's date is {today}.

    Extract the following fields from the user's message:
    - name
    - email
    - interview_date
    - interview_time

    Rules:
    1. Return only a JSON object.
    2. Use null for any field not explicitly provided.
    3. Never guess or invent information.
    4. Convert interview_date into YYYY-MM-DD format.
    5. Convert interview_time into 24-hour HH:MM format.
    6. Resolve relative dates such as "next Monday"
       using today's date.
    7. Do not assume a date or time if it is ambiguous.

    Required JSON format:
    {{
        "name": null,
        "email": null,
        "interview_date": null,
        "interview_time": null
    }}
    """

    return llm_json(system, message)


def merge(state: BookingState, extracted: dict[str, str | None]) -> tuple[BookingState, list[str]]:
    """Apply each non-null field ONE AT A TIME. Return new state + list of rejected field names."""
    
    rejected = []

    for key, value in extracted.items():

        # Ignore missing values
        if value is None:
            continue

        try:
            state = BookingState(
                **{
                    **state.model_dump(),
                    key: value
                }
            )

        except ValidationError:
            rejected.append(key)

    return state, rejected


def _key(session_id: str) -> str:
    return f"booking:{session_id}"


def booking_in_progress(session_id: str) -> bool:
    return bool(r.exists(_key(session_id)))


def _load(session_id: str) -> BookingState:
    raw = r.get(_key(session_id))
    return BookingState.model_validate_json(raw) if raw else BookingState()


def handle_booking(session_id: str, message: str, db: Session) -> str:
    state, rejected = merge(_load(session_id), extract_fields(message))

    if rejected:
        return f"That {rejected[0].replace('_', ' ')} isn't valid. {QUESTIONS[rejected[0]]}"

    for field, question in QUESTIONS.items():
        if getattr(state, field) is None:
            r.set(_key(session_id), state.model_dump_json(), ex=BOOKING_TTL)
            return question

    # all four fields present: save to SQL, clear the in-progress state
    assert state.name and state.email and state.interview_date and state.interview_time
    db.add(BookingTable(name=state.name, email=state.email,
                        interview_date=state.interview_date,
                        interview_time=state.interview_time))
    db.commit()
    r.delete(_key(session_id))
    return (f"Booked! {state.name}, {state.interview_date} at "
            f"{state.interview_time.strftime('%H:%M')}. Confirmation goes to {state.email}.")