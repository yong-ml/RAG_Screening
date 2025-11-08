from pydantic import BaseModel
from typing import Optional


class CandidateScore(BaseModel):
    name: str
    email: Optional[str]
    score: float
    jina_score: float
    gemini_score: int  # 0-100점
    gemini_analysis: str
    thinking_process: Optional[str]
    resume_text: Optional[str] = None  # 비교를 위해 저장


class ScreeningResponse(BaseModel):
    top_candidates: list[CandidateScore]
    total_processed: int
    processing_time: float
    job_description: str  # 비교를 위해 저장


class ComparisonRequest(BaseModel):
    candidate1_index: int
    candidate2_index: int


class ComparisonResponse(BaseModel):
    candidate1_name: str
    candidate2_name: str
    comparison: str
