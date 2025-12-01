from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
import os
from urllib.parse import quote

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.core.services import llm
from backend.models import sql as models
from backend.schemas.response import ComparisonRequest, ComparisonResponse

router = APIRouter()
settings = get_settings()

from backend.services.data import get_resume_text

@router.post("/compare", response_model=ComparisonResponse)
async def compare_candidates(
    request: ComparisonRequest,
    db: Session = Depends(get_db)
):
    """두 지원자 비교"""
    # 최신 세션 가져오기
    latest_session = db.query(models.ScreeningSession).order_by(models.ScreeningSession.created_at.desc()).first()
    
    if not latest_session:
        raise HTTPException(status_code=400, detail="먼저 스크리닝을 수행해주세요.")

    # 세션 내에서 지원자 찾기
    candidate1 = db.query(models.Candidate).filter(
        models.Candidate.session_id == latest_session.id,
        models.Candidate.name == request.candidate1_name
    ).first()

    candidate2 = db.query(models.Candidate).filter(
        models.Candidate.session_id == latest_session.id,
        models.Candidate.name == request.candidate2_name
    ).first()

    if not candidate1 or not candidate2:
        raise HTTPException(status_code=400, detail="유효하지 않은 지원자 이름입니다.")

    # 두 지원자 비교
    comparison_result = llm.compare_candidates(
        candidate1.name,
        get_resume_text(candidate1.filename),
        candidate1.gemini_score,
        candidate1.gemini_analysis,
        candidate2.name,
        get_resume_text(candidate2.filename),
        candidate2.gemini_score,
        candidate2.gemini_analysis,
        latest_session.job_description,
    )

    return ComparisonResponse(
        candidate1_name=candidate1.name,
        candidate2_name=candidate2.name,
        candidate1_jina_score=candidate1.jina_score,
        candidate2_jina_score=candidate2.jina_score,
        candidate1_gemini_score=candidate1.gemini_score,
        candidate2_gemini_score=candidate2.gemini_score,
        comparison=comparison_result["comparison"],
    )

@router.get("/resumes/{filename}")
def get_resume(filename: str):
    """이력서 파일 제공"""
    
    # 디버깅 로그
    print(f"Requested filename: {filename}")
    
    # 보안: 파일명에 경로 탐색 문자열이 포함되어 있는지 확인
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="유효하지 않은 파일명입니다.")
    
    file_path = os.path.join(settings.upload_dir, filename)
    print(f"Looking for file at: {file_path}")
    print(f"File exists: {os.path.exists(file_path)}")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
    media_type = "application/pdf"
    if filename.lower().endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif filename.lower().endswith(".doc"):
        media_type = "application/msword"
    
    # 브라우저에서 인라인으로 표시하도록 Content-Disposition 설정
    # RFC 2231 표준을 사용하여 한글 파일명 지원
    encoded_filename = quote(filename)
    headers = {
        "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
    }
        
    return FileResponse(file_path, media_type=media_type, headers=headers)
