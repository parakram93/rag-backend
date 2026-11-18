from datetime import datetime, timezone, date,time

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from document_ingestion.database import Base


class DocumentTable(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)   
    filename: Mapped[str] = mapped_column(String(255))
    chunk_strategy: Mapped[str] = mapped_column(String(20))
    num_chunks: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    
    
class BookingTable(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True) #mapped column  Indicates that the attribute is part of the ORM mapping.
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    interview_date: Mapped[date]
    interview_time: Mapped[time]
    