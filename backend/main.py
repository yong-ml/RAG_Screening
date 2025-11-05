from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import routes

app = FastAPI(
    title="AI Resume Screening API",
    version="1.0.0",
    description="HR 담당자를 위한 AI 이력서 스크리닝 시스템"
)

# CORS 설정 (Streamlit 연결용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api/v1", tags=["screening"])


@app.get("/")
def root():
    return {
        "message": "AI Resume Screening API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }
