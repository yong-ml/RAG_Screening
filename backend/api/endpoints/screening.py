from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from typing import Optional
import os
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.core.services import embedding_service, parser, chroma_client
from backend.models import sql as models
from backend.services.workflow import process_screening_task
from backend.schemas.response import (
    ScreeningResponse,
    CandidateScore,
    ScreeningInitResponse,
    ScreeningStatusResponse,
)

router = APIRouter()
settings = get_settings()

def get_latest_jd_path() -> str:
    """Return path to latest JD file"""
    return os.path.join(settings.job_description_dir, "latest_jd.txt")

@router.post("/screen", response_model=ScreeningInitResponse)
async def screen_resumes(
    background_tasks: BackgroundTasks,
    job_description: Optional[str] = Form(None),
    job_description_file: Optional[UploadFile] = File(None),
    top_n: int = Form(10),
    resumes: Optional[list[UploadFile]] = File(None),
    db: Session = Depends(get_db),
):
    """
    3단계 AI 파이프라인 (비동기 처리):
    1. 요청 접수 및 세션 생성
    2. 백그라운드에서 스크리닝 수행
    3. 상태 조회 API로 진행상황 확인
    """
    # 채용공고 디렉토리가 없으면 생성
    os.makedirs(settings.job_description_dir, exist_ok=True)
    latest_jd_path = get_latest_jd_path()

    # 채용공고 처리
    final_jd_text = ""
    if job_description_file:
        file_path = os.path.join(
            settings.job_description_dir, job_description_file.filename
        )
        with open(file_path, "wb") as f:
            content = await job_description_file.read()
            f.write(content)
        final_jd_text = parser.parse_resume(file_path)
        with open(latest_jd_path, "w", encoding="utf-8") as f:
            f.write(final_jd_text)
    elif job_description:
        final_jd_text = job_description
        with open(latest_jd_path, "w", encoding="utf-8") as f:
            f.write(final_jd_text)
    else:
        if os.path.exists(latest_jd_path):
            with open(latest_jd_path, "r", encoding="utf-8") as f:
                final_jd_text = f.read()
        else:
            raise HTTPException(
                status_code=400,
                detail="저장된 채용공고가 없습니다. 채용공고를 먼저 입력해주세요.",
            )

    # 업로드 디렉토리가 없으면 생성
    os.makedirs(settings.upload_dir, exist_ok=True)

    # 새로운 이력서 처리 및 ChromaDB 저장 (동기적으로 수행하여 즉시 반영)
    if resumes:
        new_resume_texts = []
        new_resume_ids = []
        new_resume_filenames = []

        for resume_file in resumes:
            file_path = os.path.join(settings.upload_dir, resume_file.filename)
            with open(file_path, "wb") as f:
                content = await resume_file.read()
                f.write(content)

            text = parser.parse_resume(file_path)
            resume_id = f"resume_{resume_file.filename}"

            existing = chroma_client.collection.get(ids=[resume_id])
            if not existing["ids"]:
                new_resume_texts.append(text)
                new_resume_ids.append(resume_id)
                new_resume_filenames.append(resume_file.filename)

        if new_resume_texts:
            embeddings = embedding_service.encode(new_resume_texts)
            chroma_client.add_resumes(
                ids=new_resume_ids,
                embeddings=embeddings.tolist(),
                documents=new_resume_texts,
                metadatas=[{"filename": fn} for fn in new_resume_filenames],
            )

    # 세션 생성 (PENDING)
    session = models.ScreeningSession(
        job_description=final_jd_text,
        total_processed=0,
        processed_count=0,
        status="PENDING"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # 백그라운드 작업 시작
    background_tasks.add_task(process_screening_task, session.id, final_jd_text, top_n)

    return ScreeningInitResponse(
        session_id=session.id,
        message="스크리닝 작업이 시작되었습니다. 상태 API를 통해 진행 상황을 확인하세요."
    )


from backend.services.data import get_resume_text

@router.get("/screen/{session_id}/status", response_model=ScreeningStatusResponse)
def get_screening_status(session_id: int, db: Session = Depends(get_db)):
    """스크리닝 세션 상태 조회"""
    session = db.query(models.ScreeningSession).filter(models.ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    result = None
    if session.status == "COMPLETED":
        candidates = db.query(models.Candidate).filter(models.Candidate.session_id == session.id).all()
        result = ScreeningResponse(
            top_candidates=[
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
            total_processed=session.total_processed,
            processing_time=session.processing_time,
            job_description=session.job_description
        )

    return ScreeningStatusResponse(
        session_id=session.id,
        status=session.status,
        total_processed=session.total_processed,
        processed_count=session.processed_count,
        result=result
    )


@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    """스크리닝 히스토리 목록 조회"""
    sessions = db.query(models.ScreeningSession).order_by(models.ScreeningSession.created_at.desc()).all()
    
    return [
        {
            "id": s.id,
            "created_at": s.created_at,
            "job_description_preview": s.job_description[:50] + "..." if s.job_description else "",
            "total_processed": s.total_processed,
            "status": s.status,
            "processing_time": s.processing_time
        }
        for s in sessions
    ]


@router.get("/export/{session_id}")
def export_session(session_id: int, db: Session = Depends(get_db)):
    """세션 결과를 Excel로 내보내기"""

    session = db.query(models.ScreeningSession).filter(models.ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    candidates = db.query(models.Candidate).filter(models.Candidate.session_id == session.id).all()
    
    if not candidates:
        raise HTTPException(status_code=400, detail="내보낼 데이터가 없습니다.")

    # DataFrame 생성
    data = []
    for c in candidates:
        data.append({
            "Rank": 0, # 나중에 정렬 후 채움
            "Name": c.name,
            "Email": c.email or "",
            "Filename": c.filename or "",
            "Jina Score": c.jina_score,
            "Gemini Score": c.gemini_score,
            "Summary": c.jina_reasoning or "",
            "Analysis": c.gemini_analysis or "",
        })

    df = pd.DataFrame(data)
    
    # Gemini 점수 내림차순 정렬
    df = df.sort_values(by="Gemini Score", ascending=False)
    df["Rank"] = range(1, len(df) + 1)

    # Excel 파일 생성
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Screening Results')
    
    output.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="screening_results_{session_id}.xlsx"'
    }
    
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
