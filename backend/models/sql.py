from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class ScreeningSession(Base):
    __tablename__ = "screening_sessions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    job_description = Column(Text, nullable=True)
    total_processed = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    processing_time = Column(Float, default=0.0)
    status = Column(String, default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED

    candidates = relationship("Candidate", back_populates="session", cascade="all, delete-orphan")

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("screening_sessions.id"))
    
    name = Column(String, index=True)
    email = Column(String, nullable=True)
    filename = Column(String, nullable=True)
    # resume_text removed for stateless architecture

    
    # Scores and Analysis
    jina_score = Column(Float, default=0.0)
    jina_reasoning = Column(Text, nullable=True)
    gemini_score = Column(Integer, default=0)
    gemini_analysis = Column(Text, nullable=True)
    thinking_process = Column(Text, nullable=True)

    session = relationship("ScreeningSession", back_populates="candidates")
