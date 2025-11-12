from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import time
import os
import asyncio
from ..core.config import get_settings
from ..services.embedding import EmbeddingService
from ..services.parser import ResumeParser
from ..services.reranker import JinaRerankerService
from ..services.llm import GeminiService
from ..models.database import ChromaDBClient
from ..schemas.response import (
    ScreeningResponse,
    CandidateScore,
    ComparisonRequest,
    ComparisonResponse,
)

router = APIRouter()

# 서비스 초기화 (싱글톤 패턴)
settings = get_settings()
embedding_service = EmbeddingService(settings.embedding_model)
parser = ResumeParser()
reranker = JinaRerankerService(settings.jina_api_key)
llm = GeminiService(settings.gemini_api_key)
db = ChromaDBClient(settings.chroma_db_path)


# 헬퍼 함수
def get_latest_jd_path() -> str:
    """채용공고 파일 경로 반환"""
    return os.path.join(settings.job_description_dir, "latest_jd.txt")


def get_latest_screening_path() -> str:
    """최신 스크리닝 결과 파일 경로 반환"""
    return os.path.join(settings.screening_results_dir, "latest_screening.json")


def save_screening_result(screening_data: dict):
    """스크리닝 결과를 JSON 파일로 저장"""
    import json

    os.makedirs(settings.screening_results_dir, exist_ok=True)
    result_path = get_latest_screening_path()

    # Pydantic 모델을 dict로 변환
    serializable_data = {
        "candidates": [
            {
                "name": c.name,
                "email": c.email,
                "score": c.score,
                "jina_score": c.jina_score,
                "jina_reasoning": c.jina_reasoning,
                "gemini_score": c.gemini_score,
                "gemini_analysis": c.gemini_analysis,
                "thinking_process": c.thinking_process,
                "resume_text": c.resume_text,
            }
            for c in screening_data["candidates"]
        ],
        "job_description": screening_data["job_description"],
        "total_processed": screening_data["total_processed"],
        "processing_time": screening_data["processing_time"],
    }

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(serializable_data, f, ensure_ascii=False, indent=2)


def load_screening_result() -> dict | None:
    """저장된 스크리닝 결과 로드"""
    import json

    result_path = get_latest_screening_path()
    if not os.path.exists(result_path):
        return None

    try:
        with open(result_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# 서버 상태 저장 (재시작 전까지 유지)
server_state = {
    "job_description": "",  # 채용공고 텍스트
    "resume_files": [],  # 업로드된 이력서 정보 [{"filename": str, "text": str, "filepath": str}]
    "last_screening_result": {
        "candidates": [],
        "job_description": "",
        "total_processed": 0,
        "processing_time": 0,
    },
    "initialized": False,  # 초기화 여부 플래그
}


def restore_server_state():
    """
    서버 재시작 후 ChromaDB와 파일시스템에서 기존 데이터 복원

    ChromaDB를 single source of truth로 사용:
    - ChromaDB에 저장된 이력서 데이터를 기반으로 server_state 복원
    - 파일시스템의 uploads 폴더는 실제 업로드된 파일 보관용
    """
    global server_state

    if server_state["initialized"]:
        return

    # 채용공고 복원
    latest_jd_path = get_latest_jd_path()
    if os.path.exists(latest_jd_path):
        try:
            with open(latest_jd_path, "r", encoding="utf-8") as f:
                server_state["job_description"] = f.read()
        except Exception:
            pass

    # ChromaDB에서 이력서 데이터 복원
    try:
        # ChromaDB에 저장된 모든 이력서 가져오기
        db_results = db.collection.get()

        if db_results and db_results["ids"]:
            for doc_id, document, metadata in zip(
                db_results["ids"], db_results["documents"], db_results["metadatas"]
            ):
                filename = (
                    metadata.get("filename", "unknown.pdf")
                    if metadata
                    else "unknown.pdf"
                )
                filepath = os.path.join(settings.upload_dir, filename)

                # server_state에 추가
                server_state["resume_files"].append(
                    {"filename": filename, "text": document, "filepath": filepath}
                )
    except Exception as e:
        # ChromaDB 복원 실패 시 로그만 남기고 계속 진행
        print(f"Warning: Failed to restore from ChromaDB: {e}")

    # 저장된 스크리닝 결과 복원
    try:
        saved_result = load_screening_result()
        if saved_result:
            # JSON에서 로드한 데이터를 CandidateScore 객체로 변환
            candidates = [
                CandidateScore(
                    name=c["name"],
                    email=c.get("email"),
                    score=c["score"],
                    jina_score=c["jina_score"],
                    jina_reasoning=c.get("jina_reasoning"),
                    gemini_score=c["gemini_score"],
                    gemini_analysis=c["gemini_analysis"],
                    thinking_process=c.get("thinking_process"),
                    resume_text=c.get("resume_text"),
                )
                for c in saved_result["candidates"]
            ]

            server_state["last_screening_result"] = {
                "candidates": candidates,
                "job_description": saved_result["job_description"],
                "total_processed": saved_result["total_processed"],
                "processing_time": saved_result["processing_time"],
            }
    except Exception as e:
        print(f"Warning: Failed to restore screening result: {e}")

    server_state["initialized"] = True


@router.post("/screen", response_model=ScreeningResponse)
async def screen_resumes(
    job_description: Optional[str] = Form(None),
    job_description_file: Optional[UploadFile] = File(None),
    top_n: int = Form(10),
    resumes: Optional[list[UploadFile]] = File(None),
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

    # 서버 재시작 후 첫 호출 시 기존 데이터 복원
    restore_server_state()

    start_time = time.time()

    # 채용공고 디렉토리가 없으면 생성
    os.makedirs(settings.job_description_dir, exist_ok=True)
    latest_jd_path = get_latest_jd_path()

    # 채용공고 처리 - 새로 입력되면 갱신, 없으면 기존 것 사용
    if job_description_file:
        # 파일에서 채용공고 읽기
        file_path = os.path.join(
            settings.job_description_dir, job_description_file.filename
        )
        with open(file_path, "wb") as f:
            content = await job_description_file.read()
            f.write(content)

        # 파서로 텍스트 추출
        job_description = parser.parse_resume(file_path)

        # 최신 채용공고로 저장
        with open(latest_jd_path, "w", encoding="utf-8") as f:
            f.write(job_description)
        server_state["job_description"] = job_description
    elif job_description:
        # 텍스트로 입력된 경우 - 파일로 저장
        with open(latest_jd_path, "w", encoding="utf-8") as f:
            f.write(job_description)
        server_state["job_description"] = job_description
    else:
        # 기존 채용공고 사용 - 파일에서 읽기
        if os.path.exists(latest_jd_path):
            with open(latest_jd_path, "r", encoding="utf-8") as f:
                job_description = f.read()
            server_state["job_description"] = job_description
        elif server_state.get("job_description"):
            # 파일은 없지만 메모리에 있는 경우 (백업)
            job_description = server_state["job_description"]
        else:
            raise HTTPException(
                status_code=400,
                detail="저장된 채용공고가 없습니다. 채용공고를 먼저 입력해주세요.",
            )

    # 업로드 디렉토리가 없으면 생성
    os.makedirs(settings.upload_dir, exist_ok=True)

    # 새로운 이력서 처리 및 저장
    if resumes:
        for resume_file in resumes:
            # 중복 체크 (파일명으로)
            if any(
                r["filename"] == resume_file.filename
                for r in server_state["resume_files"]
            ):
                continue  # 이미 있는 파일은 스킵

            # 파일 저장
            file_path = os.path.join(settings.upload_dir, resume_file.filename)
            with open(file_path, "wb") as f:
                content = await resume_file.read()
                f.write(content)

            # 텍스트 추출
            text = parser.parse_resume(file_path)

            # server_state에 추가
            server_state["resume_files"].append(
                {"filename": resume_file.filename, "text": text, "filepath": file_path}
            )

    # 이력서가 하나도 없으면 에러
    if not server_state["resume_files"]:
        raise HTTPException(status_code=400, detail="이력서 파일이 필요합니다.")

    # Stage 1: 새로운 이력서만 임베딩 및 저장
    new_resume_texts = []
    new_resume_ids = []
    new_resume_filenames = []

    for i, resume_data in enumerate(server_state["resume_files"]):
        # 파일명 기반으로 일관된 ID 생성
        resume_id = f"resume_{resume_data['filename']}"

        # ChromaDB에 이미 존재하는지 확인
        try:
            existing = db.collection.get(ids=[resume_id])
            if existing["ids"]:  # 이미 존재하면 스킵
                continue
        except Exception:
            pass  # DB 조회 실패 시 새로운 이력서로 간주

        # 새로운 이력서만 리스트에 추가
        new_resume_texts.append(resume_data["text"])
        new_resume_ids.append(resume_id)
        new_resume_filenames.append(resume_data["filename"])

    # 새로운 이력서가 있으면 임베딩 및 저장
    if new_resume_texts:
        embeddings = embedding_service.encode(new_resume_texts)
        db.add_resumes(
            ids=new_resume_ids,
            embeddings=embeddings.tolist(),
            documents=new_resume_texts,
            metadatas=[{"filename": fn} for fn in new_resume_filenames],
        )

    # 채용공고 임베딩 생성 (매번 새로 생성)
    jd_embedding = embedding_service.encode_query(job_description)

    # 1차 필터링 (Top 50) - ChromaDB에 저장된 전체 이력서 대상
    total_resumes = len(server_state["resume_files"])
    search_results = db.query(jd_embedding.tolist(), n_results=min(50, total_resumes))

    # Stage 2: Jina Reranker
    top_50_texts = search_results["documents"][0]
    top_50_metadatas = search_results["metadatas"][0]
    reranked = reranker.rerank(job_description, top_50_texts, top_n=top_n)

    # Stage 3: Gemini 분석 (Top N만) - 병렬 처리
    async def analyze_single_candidate(i: int, result: dict):
        """단일 지원자 분석 (비동기)"""
        # Jina reranker 결과 파싱
        doc_index = result.get("index", i)
        score = result.get("relevance_score", 0.0)

        # 문서 텍스트 가져오기
        if isinstance(result.get("document"), dict):
            doc_text = result.get("document", {}).get("text", "")
        else:
            doc_text = top_50_texts[doc_index]

        # 메타데이터에서 파일명 가져오기
        name = f"Candidate {i + 1}"  # 기본값
        try:
            metadata = top_50_metadatas[doc_index]
            filename = metadata.get("filename", "")
            if filename:
                name = filename.rsplit(".", 1)[0]  # 확장자 제거
        except (IndexError, KeyError, AttributeError, TypeError):
            pass  # 기본값 사용

        # Jina 점수 기반 매칭 요약 생성 (동기 함수를 스레드에서 실행)
        jina_reasoning = await asyncio.to_thread(
            llm.generate_jina_reasoning, doc_text, job_description, score
        )

        # Gemini 분석 (동기 함수를 스레드에서 실행)
        analysis = await asyncio.to_thread(
            llm.analyze_candidate, doc_text, job_description
        )

        return CandidateScore(
            name=name,
            email=None,
            score=score,
            jina_score=score,
            jina_reasoning=jina_reasoning,
            gemini_score=analysis.get("gemini_score", 0),
            gemini_analysis=analysis["analysis"],
            thinking_process=analysis["thinking_process"],
            resume_text=doc_text,
        )

    # 모든 지원자를 병렬로 분석
    candidates = await asyncio.gather(
        *[analyze_single_candidate(i, result) for i, result in enumerate(reranked)]
    )

    processing_time = time.time() - start_time

    # 결과 저장 (비교 API 및 상태 유지를 위해)
    server_state["last_screening_result"] = {
        "candidates": candidates,
        "job_description": job_description,
        "total_processed": len(server_state["resume_files"]),
        "processing_time": processing_time,
    }

    # JSON 파일로 저장 (서버 재시작 후에도 유지)
    try:
        save_screening_result(server_state["last_screening_result"])
    except Exception as e:
        print(f"Warning: Failed to save screening result: {e}")

    return ScreeningResponse(
        top_candidates=candidates,
        total_processed=len(server_state["resume_files"]),
        processing_time=processing_time,
        job_description=job_description,
    )


@router.post("/compare", response_model=ComparisonResponse)
async def compare_candidates(request: ComparisonRequest):
    """두 지원자 비교"""
    global server_state

    # 서버 재시작 후 첫 호출 시 기존 데이터 복원
    restore_server_state()

    candidates = server_state["last_screening_result"].get("candidates", [])
    job_description = server_state["last_screening_result"].get("job_description", "")

    if not candidates:
        raise HTTPException(status_code=400, detail="먼저 스크리닝을 수행해주세요.")

    # 이름으로 지원자 찾기
    candidate1 = None
    candidate2 = None

    for candidate in candidates:
        if candidate.name == request.candidate1_name:
            candidate1 = candidate
        if candidate.name == request.candidate2_name:
            candidate2 = candidate

    if not candidate1 or not candidate2:
        raise HTTPException(status_code=400, detail="유효하지 않은 지원자 이름입니다.")

    # 두 지원자 비교
    comparison_result = llm.compare_candidates(
        candidate1.name,
        candidate1.resume_text,
        candidate1.jina_score,
        candidate2.name,
        candidate2.resume_text,
        candidate2.jina_score,
        job_description,
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


@router.get("/state")
def get_state():
    """
    현재 서버 상태 조회
    - 저장된 채용공고 여부 (파일 확인)
    - 저장된 이력서 개수 및 파일명 목록
    - 최근 스크리닝 결과 여부
    """
    global server_state

    # 서버 재시작 후 첫 호출 시 기존 데이터 복원
    restore_server_state()

    # 채용공고 파일 확인
    latest_jd_path = get_latest_jd_path()
    has_jd = os.path.exists(latest_jd_path) or bool(server_state.get("job_description"))

    # 파일에서 미리보기 로드
    jd_preview = ""
    if os.path.exists(latest_jd_path):
        try:
            with open(latest_jd_path, "r", encoding="utf-8") as f:
                jd_preview = f.read()[:100]
        except Exception:
            pass
    elif server_state.get("job_description"):
        jd_preview = server_state["job_description"][:100]

    return {
        "has_job_description": has_jd,
        "job_description_preview": jd_preview,
        "resume_count": len(server_state["resume_files"]),
        "resume_filenames": [r["filename"] for r in server_state["resume_files"]],
        "has_screening_result": bool(
            server_state["last_screening_result"]["candidates"]
        ),
        "screening_result": (
            server_state["last_screening_result"]
            if server_state["last_screening_result"]["candidates"]
            else None
        ),
    }


@router.get("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "message": "AI Resume Screening API is running"}


@router.get("/db-status")
def get_db_status():
    """ChromaDB 상태 확인"""
    try:
        # ChromaDB에서 전체 데이터 조회
        results = db.collection.get()

        total_count = len(results["ids"])

        # 파일명별 카운트
        filenames = [
            m.get("filename", "Unknown") if m else "Unknown"
            for m in results["metadatas"]
        ]
        filename_counts = {}
        for fn in filenames:
            filename_counts[fn] = filename_counts.get(fn, 0) + 1

        # 중복 파일 찾기
        duplicates = {k: v for k, v in filename_counts.items() if v > 1}

        # 상세 정보
        items = []
        for id_, metadata, doc in zip(
            results["ids"], results["metadatas"], results["documents"]
        ):
            items.append(
                {
                    "id": id_,
                    "filename": metadata.get("filename", "N/A") if metadata else "N/A",
                    "doc_length": len(doc) if doc else 0,
                }
            )

        return {
            "total_count": total_count,
            "items": items,
            "duplicates": duplicates,
            "has_duplicates": len(duplicates) > 0,
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
def clear_database():
    """
    ChromaDB와 server_state 초기화
    경고: 모든 이력서 데이터가 삭제됩니다!
    """
    global server_state

    try:
        # ChromaDB 초기화
        db.clear()

        # 저장된 스크리닝 결과 파일 삭제
        screening_path = get_latest_screening_path()
        if os.path.exists(screening_path):
            os.remove(screening_path)

        # server_state 초기화
        server_state["resume_files"] = []
        server_state["last_screening_result"] = {
            "candidates": [],
            "job_description": "",
            "total_processed": 0,
            "processing_time": 0,
        }
        server_state["initialized"] = False  # 재초기화 허용

        return {
            "status": "success",
            "message": "데이터베이스가 초기화되었습니다.",
            "deleted_count": 0,  # clear() 후에는 카운트를 알 수 없음
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"데이터베이스 초기화 실패: {str(e)}"
        )
