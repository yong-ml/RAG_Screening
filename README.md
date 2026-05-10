# AI Agentic Resume Screening System
> 멀티 에이전트(Multi-Agent) 기반의 지능형 이력서 분석 및 어뷰징 탐지 채용 솔루션

<p align="left">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=Python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=FastAPI&logoColor=white"/>
  <img src="https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=React&logoColor=black"/>
  <img src="https://img.shields.io/badge/Gemini_2.5_Pro-8E75B2?style=flat-square&logo=Google%20Gemini&logoColor=white"/>
  <img src="https://img.shields.io/badge/ChromaDB-FF6F00?style=flat-square&logo=Chroma&logoColor=white"/>
</p>

## 프로젝트 개요
기존의 수동적인 채용 프로세스는 한 공고당 수백 개의 이력서를 검토하는 데 막대한 시간(평균 50시간 이상)이 소모되며, 담당자의 피로도에 따라 주관적인 평가가 개입될 수밖에 없습니다.

본 프로젝트는 3단계 AI 파이프라인과 3개의 전문 AI 에이전트가 협력하는 '멀티 에이전트 아키텍처'를 도입하여, 인사 담당자의 이력서 검토 시간을 90% 이상 단축하고 평가의 공정성을 극대화한 로컬 기반의 채용 보조 시스템입니다.

## 핵심 기술 및 구현 포인트

### 1. Multi-Agent Workflow (역할 분담형 AI 협업)
단순한 프롬프팅을 넘어, 3개의 특화된 AI 에이전트가 협력하여 인간 채용관찰자처럼 심층적으로 분석합니다.
* Job Analysis Agent: 채용 공고를 분석해 필수/우대 조건을 평가 기준으로 자동 도출.
* Screening Agent: 이력서 내 기술 스택과 경험을 교차 검증하고, 유사 기술도 유연하게 평가.
* Audit Agent: 시스템을 속이려는 지원자의 과적합 및 어뷰징 시도를 감지하여 신뢰성 보장.

### 2. 지능형 어뷰징 방어 시스템 (Suspicious Resume Detection)
AI 스크리닝을 속이기 위한 백색 폰트(White Text), 1pt 크기 숨김 글씨 등 Hidden Text 기법을 문서 파싱 단계에서 원천 차단하고 식별하기 쉽게 붉은색 텍스트로 시각화하여 담당자에게 경고합니다. 더불어 문맥 없이 나열된 키워드 스터핑 또한 LLM의 문맥 분석을 통해 식별해냅니다.

## 시스템 아키텍처

![System Architecture](./플로우차트.svg)

## 기술 스택
* Backend: Python 3.10+, FastAPI, LangChain
* AI & NLP: Google Gemini 2.5 Pro (LLM), Jina AI Reranker v2, BAAI/BGE-M3 (Embedding)
* Vector DB: ChromaDB (Local Persistent)
* Frontend: React, TailwindCSS, Framer Motion
* Tools/Infra: uv, python-docx, pypdf

## 프로젝트 실행 방법

### 1. Backend 환경 설정 및 실행
```bash
cd backend
uv sync

# 환경변수 설정 (.env)
# GEMINI_API_KEY=your_api_key_here
# JINA_API_KEY=your_api_key_here

# 서버 실행 (http://localhost:8000)
uv run uvicorn main:app --reload
```

### 2. Frontend 실행
```bash
cd frontend-react
npm install
# 개발 서버 실행 (http://localhost:5173)
npm run dev
```

### 3. 테스트 데이터 및 어뷰징 시연용 데이터 생성
발표 및 시연을 위해 어뷰징(Hidden text)이 포함된 테스트 이력서를 생성할 수 있습니다.
```bash
# 숨겨진 텍스트가 포함된 이력서 생성 스크립트 실행
python backend/generate_subtle_resume.py

# 생성 결과:
# 1. subtle_suspicious_candidate.docx (원본)
# 2. subtle_suspicious_candidate_REVEALED.docx (발표용 시각화 버전)
```
