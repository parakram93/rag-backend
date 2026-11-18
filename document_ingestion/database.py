from collections.abc import Iterator

from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session, mapped_column

class Base(DeclarativeBase):
    pass

engine = create_engine("sqlite:///app.db", connect_args={"check_same_thread": False}) 

def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session