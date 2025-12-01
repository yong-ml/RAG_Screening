from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import os

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.core.services import chroma_client
from backend.models import sql as models
from backend.schemas.response import CandidateScore

router = APIRouter()
settings = get_settings()

def get_latest_jd_path() -> str:
    """Return path to latest JD file"""
    return os.path.join(settings.job_description_dir, "latest_jd.txt")

from backend.services.data import get_resume_text

@router.get("/state")
def get_state(db: Session = Depends(get_db)):
    """
    현재 서버 상태 조회
    """
    # 최신 세션 가져오기
    latest_session = db.query(models.ScreeningSession).order_by(models.ScreeningSession.created_at.desc()).first()
    
    # 채용공고 확인
    latest_jd_path = get_latest_jd_path()
    has_jd = os.path.exists(latest_jd_path) or (latest_session is not None)
    
    jd_preview = ""
    if os.path.exists(latest_jd_path):
        try:
            with open(latest_jd_path, "r", encoding="utf-8") as f:
                jd_preview = f.read()[:100]
        except Exception:
            pass
    elif latest_session:
        jd_preview = latest_session.job_description[:100]

    # 이력서 개수 및 목록 (ChromaDB 기준)
    chroma_results = chroma_client.collection.get()
    resume_count = len(chroma_results["ids"]) if chroma_results else 0
    resume_filenames = [
        m.get("filename", "Unknown") if m else "Unknown"
        for m in (chroma_results["metadatas"] if chroma_results else [])
    ]

    # 스크리닝 결과 구성
    screening_result = None
    if latest_session:
        candidates = db.query(models.Candidate).filter(models.Candidate.session_id == latest_session.id).all()
        screening_result = {
            "candidates": [
                CandidateScore(
                    name=c.name,
                    email=c.email,
                    score=c.jina_score,
                    jina_score=c.jina_score,
                    jina_reasoning=c.jina_reasoning,
                    gemini_score=c.gemini_score,
                    gemini_analysis=c.gemini_analysis,
                    thinking_process=c.thinking_process,
                    resume_text=get_resume_text(c.filename),
                    filename=c.filename
                ) for c in candidates
            ],
            "job_description": latest_session.job_description,
            "total_processed": latest_session.total_processed,
            "processing_time": latest_session.processing_time
        }

    return {
        "has_job_description": has_jd,
        "job_description_preview": jd_preview,
        "resume_count": resume_count,
        "resume_filenames": resume_filenames,
        "has_screening_result": bool(screening_result),
        "screening_result": screening_result,
    }


@router.get("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "message": "AI Resume Screening API is running"}


@router.get("/db-status")
def get_db_status(db: Session = Depends(get_db)):
    """ChromaDB 및 SQLite 상태 확인"""
    try:
        # ChromaDB 상태
        chroma_results = chroma_client.collection.get()
        total_count = len(chroma_results["ids"]) if chroma_results else 0
        
        # 파일명별 카운트
        filenames = [
            m.get("filename", "Unknown") if m else "Unknown"
            for m in (chroma_results["metadatas"] if chroma_results else [])
        ]
        filename_counts = {}
        for fn in filenames:
            filename_counts[fn] = filename_counts.get(fn, 0) + 1
        
        duplicates = {k: v for k, v in filename_counts.items() if v > 1}

        # 상세 정보
        items = []
        if chroma_results:
            for id_, metadata, doc in zip(
                chroma_results["ids"], chroma_results["metadatas"], chroma_results["documents"]
            ):
                items.append({
                    "id": id_,
                    "filename": metadata.get("filename", "N/A") if metadata else "N/A",
                    "doc_length": len(doc) if doc else 0,
                })

        # SQLite 상태
        session_count = db.query(models.ScreeningSession).count()
        candidate_count = db.query(models.Candidate).count()

        return {
            "total_count": total_count,
            "items": items,
            "duplicates": duplicates,
            "has_duplicates": len(duplicates) > 0,
            "sqlite_stats": {
                "sessions": session_count,
                "candidates": candidate_count
            }
        }
    except Exception as e:
        return {
            "total_count": 0,
            "items": [],
            "duplicates": {},
            "has_duplicates": False,
            "error": str(e),
        }


@router.post("/clear-db")
def clear_database(db: Session = Depends(get_db)):
    """
    ChromaDB와 SQLite 초기화
    경고: 모든 데이터가 삭제됩니다!
    """
    try:
        # ChromaDB 초기화
        chroma_client.clear()

        # SQLite 초기화
        db.query(models.Candidate).delete()
        db.query(models.ScreeningSession).delete()
        db.commit()

        # 저장된 파일 삭제 (선택적)
        latest_jd_path = get_latest_jd_path()
        if os.path.exists(latest_jd_path):
            os.remove(latest_jd_path)

        return {
            "status": "success",
            "message": "데이터베이스가 초기화되었습니다.",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"데이터베이스 초기화 실패: {str(e)}"
        )
