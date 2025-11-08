from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os


def create_resume(filename, name, email, education, experience, skills, projects):
    """DOCX 이력서 생성"""
    doc = Document()

    # 이름 (제목)
    title = doc.add_heading(name, 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 연락처
    contact = doc.add_paragraph(f"Email: {email}")
    contact.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    # 학력
    doc.add_heading("학력", level=1)
    doc.add_paragraph(education)

    # 경력
    doc.add_heading("경력", level=1)
    for exp in experience:
        doc.add_paragraph(exp, style="List Bullet")

    # 기술 스택
    doc.add_heading("기술 스택", level=1)
    doc.add_paragraph(skills)

    # 프로젝트
    doc.add_heading("주요 프로젝트", level=1)
    for project in projects:
        doc.add_paragraph(project, style="List Bullet")

    # 저장
    doc.save(filename)
    print(f"Created: {filename}")


# 이력서 데이터
resumes = [
    {
        "filename": "data/resumes/김철수_이력서.docx",
        "name": "김철수",
        "email": "chulsoo.kim@email.com",
        "education": "서울대학교 컴퓨터공학과 학사 (2015-2019)",
        "experience": [
            "네이버 AI Lab - ML Engineer (2021-2024, 3년)",
            "카카오 - Backend Developer (2019-2021, 2년)",
        ],
        "skills": "Python, FastAPI, Django, PostgreSQL, MongoDB, Docker, Kubernetes, AWS, Sentence Transformers, ChromaDB, LangChain, OpenAI API",
        "projects": [
            "AI 챗봇 시스템 구축 - FastAPI + LangChain + ChromaDB를 활용한 RAG 기반 챗봇 개발",
            "추천 시스템 API - Sentence Transformers를 활용한 의미 기반 상품 추천 시스템",
            "대용량 로그 처리 파이프라인 - Kafka + Spark를 활용한 실시간 로그 분석 시스템",
        ],
    },
    {
        "filename": "data/resumes/이영희_이력서.docx",
        "name": "이영희",
        "email": "younghee.lee@email.com",
        "education": "KAIST 전산학부 석사 (2018-2020), 고려대 컴퓨터학과 학사 (2014-2018)",
        "experience": [
            "쿠팡 - Senior Backend Engineer (2020-2024, 4년)",
        ],
        "skills": "Python, FastAPI, Flask, PostgreSQL, Redis, Docker, AWS, GCP, Vector DB (Pinecone), Hugging Face Transformers",
        "projects": [
            "상품 검색 시스템 개선 - Vector DB를 활용한 의미 기반 검색 시스템 구축",
            "ML 모델 서빙 플랫폼 - FastAPI 기반 모델 서빙 인프라 구축, 일 1억건 이상 처리",
            "실시간 추천 엔진 - Redis + ML 모델을 활용한 실시간 개인화 추천 시스템",
        ],
    },
    {
        "filename": "data/resumes/박민수_이력서.docx",
        "name": "박민수",
        "email": "minsu.park@email.com",
        "education": "연세대학교 소프트웨어학과 학사 (2017-2021)",
        "experience": [
            "스타트업 A - Backend Developer (2021-2024, 3년)",
        ],
        "skills": "Python, FastAPI, Django, MySQL, MongoDB, Git, Docker",
        "projects": [
            "RESTful API 개발 - FastAPI를 활용한 B2B SaaS 플랫폼 백엔드 개발",
            "데이터베이스 최적화 - 쿼리 최적화를 통한 API 응답속도 50% 개선",
            "사용자 인증 시스템 - JWT 기반 인증/인가 시스템 구축",
        ],
    },
    {
        "filename": "data/resumes/정수진_이력서.docx",
        "name": "정수진",
        "email": "soojin.jung@email.com",
        "education": "부산대학교 컴퓨터공학과 학사 (2019-2023)",
        "experience": [
            "IT 스타트업 - Junior Backend Developer (2023-2024, 1년 6개월)",
        ],
        "skills": "Python, Flask, Django, MySQL, Git",
        "projects": [
            "사내 관리 시스템 개발 - Django를 활용한 사내 업무 관리 시스템",
            "간단한 REST API 구현 - Flask 기반 CRUD API 개발",
        ],
    },
    {
        "filename": "data/resumes/최준영_이력서.docx",
        "name": "최준영",
        "email": "junyoung.choi@email.com",
        "education": "한양대학교 전자공학과 학사 (2016-2020)",
        "experience": [
            "삼성전자 - Embedded Software Engineer (2020-2024, 4년)",
        ],
        "skills": "C, C++, Python, Linux, Embedded Systems, RTOS",
        "projects": [
            "IoT 디바이스 펌웨어 개발 - C/C++를 활용한 임베디드 시스템 개발",
            "센서 데이터 수집 시스템 - Python 스크립트를 활용한 데이터 수집",
            "실시간 모니터링 시스템 - RTOS 기반 실시간 시스템 개발",
        ],
    },
]

# 디렉토리 생성
os.makedirs("data/resumes", exist_ok=True)

# 이력서 생성
for resume in resumes:
    create_resume(
        resume["filename"],
        resume["name"],
        resume["email"],
        resume["education"],
        resume["experience"],
        resume["skills"],
        resume["projects"],
    )

print("\n✅ 5개의 테스트 이력서가 생성되었습니다!")
