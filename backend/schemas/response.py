from pydantic import BaseModel
from typing import Optional


class CandidateScore(BaseModel):
    name: str
    email: Optional[str]
    score: float
    jina_score: float
    jina_reasoning: Optional[str] = None  # Jina 점수 기반 매칭 요약
    gemini_score: int  # 0-100점
    gemini_analysis: str
    thinking_process: Optional[str]
    resume_text: Optional[str] = None  # 비교를 위해 저장
    filename: Optional[str] = None  # 이력서 파일명


class ScreeningResponse(BaseModel):
    top_candidates: list[CandidateScore]
    total_processed: int
    processing_time: float
    job_description: str  # 비교를 위해 저장


class ComparisonRequest(BaseModel):
    candidate1_name: str
    candidate2_name: str


class ComparisonResponse(BaseModel):
    candidate1_name: str
    candidate2_name: str
    candidate1_jina_score: float
    candidate2_jina_score: float
    candidate1_gemini_score: int
    candidate2_gemini_score: int
    comparison: str


class ScreeningInitResponse(BaseModel):
    session_id: int
    message: str


class ScreeningStatusResponse(BaseModel):
    session_id: int
    status: str
    total_processed: int
    processed_count: int
    result: Optional[ScreeningResponse] = None
