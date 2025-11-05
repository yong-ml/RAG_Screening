from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
import time
import os
from ..core.config import get_settings
from ..services.embedding import EmbeddingService
from ..services.parser import ResumeParser
from ..services.reranker import JinaRerankerService
from ..services.llm import GeminiService
from ..models.database import ChromaDBClient
from ..schemas.response import ScreeningResponse, CandidateScore, ComparisonRequest, ComparisonResponse

router = APIRouter()

# 서비스 초기화 (싱글톤 패턴)
settings = get_settings()
embedding_service = EmbeddingService(settings.embedding_model)
parser = ResumeParser()
reranker = JinaRerankerService(settings.jina_api_key)
llm = GeminiService(settings.gemini_api_key)
db = ChromaDBClient(settings.chroma_db_path)

# 서버 상태 저장 (재시작 전까지 유지)
server_state = {
    "job_description": "",  # 채용공고 텍스트
    "resume_files": [],  # 업로드된 이력서 정보 [{"filename": str, "text": str, "filepath": str}]
    "last_screening_result": {
        "candidates": [],
        "job_description": "",
        "total_processed": 0,
        "processing_time": 0
    }
}


@router.post("/screen", response_model=ScreeningResponse)
async def screen_resumes(
    job_description: Optional[str] = Form(None),
    job_description_file: Optional[UploadFile] = File(None),
    top_n: int = Form(10),
    resumes: Optional[List[UploadFile]] = File(None)
):
    """
    3단계 AI 파이프라인:
    1. BGE-M3 임베딩 → ChromaDB 저장 및 1차 필터링
    2. Jina Reranker → 정밀 재정렬
    3. Gemini → 상세 분석

    채용공고는 텍스트 또는 파일(txt, pdf, docx)로 제공 가능
    이전에 입력한 데이터가 있으면 누적되어 함께 스크리닝됩니다.
    """
    global server_state
    start_time = time.time()

    # 채용공고 처리 - 새로 입력되면 갱신, 없으면 기존 것 사용
    if job_description_file:
        # 파일에서 채용공고 읽기
        file_path = os.path.join(settings.upload_dir, job_description_file.filename)
        with open(file_path, "wb") as f:
            content = await job_description_file.read()
            f.write(content)

        # 파일 확장자에 따라 텍스트 추출
        if file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                job_description = f.read()
        else:
            job_description = parser.parse_resume(file_path)
        server_state["job_description"] = job_description
    elif job_description:
        # 텍스트로 입력된 경우
        server_state["job_description"] = job_description
    elif server_state["job_description"]:
        # 기존 저장된 채용공고 사용
        job_description = server_state["job_description"]
    else:
        raise HTTPException(status_code=400, detail="채용공고 텍스트 또는 파일이 필요합니다.")

    # 업로드 디렉토리가 없으면 생성
    os.makedirs(settings.upload_dir, exist_ok=True)

    # 새로운 이력서 처리 및 저장
    if resumes:
        for resume_file in resumes:
            # 중복 체크 (파일명으로)
            if any(r["filename"] == resume_file.filename for r in server_state["resume_files"]):
                continue  # 이미 있는 파일은 스킵

            # 파일 저장
            file_path = os.path.join(settings.upload_dir, resume_file.filename)
            with open(file_path, "wb") as f:
                content = await resume_file.read()
                f.write(content)

            # 텍스트 추출
            text = parser.parse_resume(file_path)

            # server_state에 추가
            server_state["resume_files"].append({
                "filename": resume_file.filename,
                "text": text,
                "filepath": file_path
            })

    # 이력서가 하나도 없으면 에러
    if not server_state["resume_files"]:
        raise HTTPException(status_code=400, detail="이력서 파일이 필요합니다.")

    # ChromaDB 초기화 (이전 데이터 제거)
    try:
        db.clear()
    except:
        pass

    # Stage 1: 전체 이력서로 임베딩 및 저장
    resume_texts = []
    resume_ids = []
    resume_filenames = []

    for i, resume_data in enumerate(server_state["resume_files"]):
        resume_texts.append(resume_data["text"])
        resume_ids.append(f"resume_{i}_{int(time.time())}")
        resume_filenames.append(resume_data["filename"])

    # 임베딩 생성
    embeddings = embedding_service.encode(resume_texts)
    jd_embedding = embedding_service.encode_query(job_description)

    # ChromaDB 저장
    db.add_resumes(
        ids=resume_ids,
        embeddings=embeddings.tolist(),
        documents=resume_texts,
        metadatas=[{"index": i, "filename": resume_filenames[i]} for i in range(len(resume_texts))]
    )

    # 1차 필터링 (Top 50)
    search_results = db.query(jd_embedding.tolist(), n_results=min(50, len(resume_texts)))

    # Stage 2: Jina Reranker
    top_50_texts = search_results['documents'][0]
    top_50_metadatas = search_results['metadatas'][0]
    reranked = reranker.rerank(job_description, top_50_texts, top_n=top_n)

    # Stage 3: Gemini 분석 (Top N만)
    candidates = []
    for i, result in enumerate(reranked):
        # Jina reranker 결과 파싱
        # result는 {'index': int, 'relevance_score': float, 'document': {'text': str}}
        doc_index = result.get('index', i)
        score = result.get('relevance_score', 0.0)

        # 문서 텍스트 가져오기
        if isinstance(result.get('document'), dict):
            doc_text = result.get('document', {}).get('text', '')
        else:
            doc_text = top_50_texts[doc_index]

        # 메타데이터에서 파일명 가져오기
        try:
            metadata = top_50_metadatas[doc_index]
            filename = metadata.get('filename', f'Candidate {i+1}')
            name = filename.rsplit('.', 1)[0]  # 확장자 제거
        except (IndexError, KeyError, AttributeError) as e:
            # 인덱스 오류 시 텍스트로 매칭 시도
            try:
                # 텍스트 매칭으로 원본 찾기
                for idx, text in enumerate(top_50_texts):
                    if text == doc_text:
                        filename = top_50_metadatas[idx].get('filename', f'Candidate {i+1}')
                        name = filename.rsplit('.', 1)[0]
                        break
                else:
                    name = f"Candidate {i+1}"
            except:
                name = f"Candidate {i+1}"

        analysis = llm.analyze_candidate(
            doc_text,
            job_description
        )

        candidates.append(CandidateScore(
            name=name,
            email=None,
            score=score,
            jina_score=score,
            gemini_score=analysis.get('gemini_score', 0),
            gemini_analysis=analysis['analysis'],
            thinking_process=analysis['thinking_process'],
            resume_text=doc_text
        ))

    processing_time = time.time() - start_time

    # 결과 저장 (비교 API 및 상태 유지를 위해)
    server_state["last_screening_result"] = {
        "candidates": candidates,
        "job_description": job_description,
        "total_processed": len(server_state["resume_files"]),
        "processing_time": processing_time
    }

    return ScreeningResponse(
        top_candidates=candidates,
        total_processed=len(server_state["resume_files"]),
        processing_time=processing_time,
        job_description=job_description
    )


@router.post("/compare", response_model=ComparisonResponse)
async def compare_candidates(request: ComparisonRequest):
    """두 지원자 비교"""
    global server_state

    candidates = server_state["last_screening_result"].get("candidates", [])
    job_description = server_state["last_screening_result"].get("job_description", "")

    if not candidates:
        raise HTTPException(status_code=400, detail="먼저 스크리닝을 수행해주세요.")

    if request.candidate1_index >= len(candidates) or request.candidate2_index >= len(candidates):
        raise HTTPException(status_code=400, detail="유효하지 않은 지원자 인덱스입니다.")

    candidate1 = candidates[request.candidate1_index]
    candidate2 = candidates[request.candidate2_index]

    # 두 지원자 비교
    comparison_result = llm.compare_candidates(
        candidate1.name,
        candidate1.resume_text,
        candidate2.name,
        candidate2.resume_text,
        job_description
    )

    return ComparisonResponse(
        candidate1_name=candidate1.name,
        candidate2_name=candidate2.name,
        comparison=comparison_result['comparison']
    )


@router.get("/state")
def get_state():
    """
    현재 서버 상태 조회
    - 저장된 채용공고 여부
    - 저장된 이력서 개수 및 파일명 목록
    - 최근 스크리닝 결과 여부
    """
    global server_state

    return {
        "has_job_description": bool(server_state["job_description"]),
        "job_description_preview": server_state["job_description"][:100] if server_state["job_description"] else "",
        "resume_count": len(server_state["resume_files"]),
        "resume_filenames": [r["filename"] for r in server_state["resume_files"]],
        "has_screening_result": bool(server_state["last_screening_result"]["candidates"]),
        "screening_result": server_state["last_screening_result"] if server_state["last_screening_result"]["candidates"] else None
    }


@router.get("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "message": "AI Resume Screening API is running"}
