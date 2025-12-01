import sys
import os
import asyncio
from pprint import pprint

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import get_settings
from backend.services.llm import GeminiService

async def main():
    print("[START] Agentic Workflow Test Start...\n")
    
    settings = get_settings()
    if not settings.gemini_api_key:
        print("[ERROR] Error: GEMINI_API_KEY not found in .env")
        return

    gemini_service = GeminiService(api_key=settings.gemini_api_key)

    # 1. Sample Job Description
    job_description = """
    [채용 공고] 백엔드 개발자 (Python)
    
    주요 업무:
    - 대규모 트래픽 처리를 위한 백엔드 API 설계 및 개발
    - AWS 클라우드 인프라 구축 및 운영
    - 데이터베이스 설계 및 최적화 (PostgreSQL, Redis)
    
    자격 요건:
    - Python (Django/FastAPI) 개발 경력 3년 이상
    - RESTful API 설계 및 구현 경험
    - AWS (EC2, RDS, S3 등) 활용 경험
    - RDBMS 및 NoSQL에 대한 이해
    
    우대 사항:
    - MSA(Microservices Architecture) 경험
    - Docker/Kubernetes 기반 컨테이너 환경 경험
    - 대용량 트래픽 처리 경험
    """
    print(f"[INFO] Job Description:\n{job_description[:100]}...\n")

    # 2. Sample Resume (Mixed: Good skills but some missing, potential over-optimization)
    resume_text = """
    이름: 홍길동
    이메일: hong@example.com
    
    [기술 스택]
    Python, Django, FastAPI, PyTorch, MySQL, Redis, Docker, AWS
    
    [경력 기술서]
    1. 이커머스 백엔드 개발 (2021.01 ~ 현재)
    - Python FastAPI를 활용하여 마이크로서비스 아키텍처(MSA) 기반의 API 서버 구축
    - PyTorch를 활용한 상품 추천 시스템 모델 서빙 API 개발 (TensorFlow 대체 가능)
    - Redis를 활용한 캐싱 전략 도입으로 응답 속도 50% 개선
    - Docker 컨테이너 기반 배포 파이프라인 구축
    
    2. 사내 메신저 개발 (2019.01 ~ 2020.12)
    - Django 프레임워크를 이용한 REST API 개발
    - MySQL 데이터베이스 설계 및 쿼리 최적화
    
    [자기소개]
    대규모 트래픽 처리를 위한 백엔드 API 설계 및 개발 경험이 풍부합니다.
    AWS 클라우드 인프라 구축 및 운영 경험은 부족하지만 학습 의지가 강합니다.
    """
    print(f"[INFO] Resume:\n{resume_text[:100]}...\n")

    # 3. Test: Extract Criteria (JobAnalysisAgent)
    print("[STEP 1] JobAnalysisAgent: Extracting Criteria...")
    criteria = gemini_service.extract_criteria(job_description)
    print("[SUCCESS] Extracted Criteria:")
    for c in criteria:
        print(f"  - {c}")
    print("\n")

    # 4. Test: Evaluate Criteria (ScreeningAgent)
    print("[STEP 2] ScreeningAgent: Evaluating Candidate...")
    evaluations = []
    for criterion in criteria:
        print(f"  > Evaluating against: {criterion}...")
        result = gemini_service.evaluate_candidate_criteria(resume_text, criterion)
        evaluations.append(result)
        print(f"    Score: {result.get('score')}/10")
        print(f"    Reasoning: {result.get('reasoning')}")
        print(f"    Evidence: {result.get('evidence')}")
    print("\n")

    # 5. Test: Detect Over-optimization (AuditAgent)
    print("[STEP 3] AuditAgent: Checking for Over-optimization...")
    # Let's try to trick it with a copy-paste resume snippet
    fake_resume_text = resume_text + "\n" + job_description # Appending JD to resume to trigger detection
    audit_result = gemini_service.detect_over_optimization(fake_resume_text, job_description)
    print(f"  > Suspicion Score: {audit_result.get('suspicion_score')}")
    print(f"  > Analysis: {audit_result.get('analysis')}")
    print("\n")

    # 6. Test: Full Analysis (Coordinator)
    print("[STEP 4] Coordinator: Generating Final Report...")
    final_report = gemini_service.analyze_candidate(resume_text, job_description, criteria)
    print(f"  > Final Gemini Score: {final_report.get('gemini_score')}")
    print(f"  > Thinking Process: {final_report.get('thinking_process')}")
    # print(f"  > Report:\n{final_report.get('analysis')}") # Too long to print all

    print("\n[SUCCESS] Test Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(main())
