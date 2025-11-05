import pytest
from backend.services.embedding import EmbeddingService


def test_embedding_service():
    service = EmbeddingService()

    texts = ["Python developer with 5 years experience", "Frontend engineer"]
    embeddings = service.encode(texts)

    assert embeddings.shape[0] == 2  # 2개의 텍스트
    assert embeddings.shape[1] == 1024  # BGE-M3는 1024차원
    assert embeddings[0][0] != 0  # 임베딩이 생성되었는지 확인


def test_encode_query():
    service = EmbeddingService()

    query = "Backend developer with FastAPI experience"
    embedding = service.encode_query(query)

    assert embedding.shape == (1024,)  # 1024차원 벡터
    assert embedding[0] != 0
