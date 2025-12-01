from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings

from .core.database import engine, Base
from .models import sql  # Import models to register them with Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Resume Screening API",
    version="1.0.0",
    description="HR 담당자를 위한 AI 이력서 스크리닝 시스템",
)

# CORS 설정 (Streamlit 연결용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .api.endpoints import candidates, screening, system

app.include_router(screening.router, prefix="/api/v1", tags=["screening"])
app.include_router(candidates.router, prefix="/api/v1", tags=["candidates"])
app.include_router(system.router, prefix="/api/v1", tags=["system"])


@app.get("/")
def root():
    return {
        "message": "AI Resume Screening API is running",
        "version": "1.0.0",
        "docs": "/docs",
    }
