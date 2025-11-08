from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingService:
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        # 첫 실행 시 자동 다운로드 (약 2.27GB)
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        """텍스트를 임베딩 벡터로 변환"""
        return self.model.encode(
            texts,
            normalize_embeddings=True,  # 코사인 유사도용
            device="cpu",  # GPU 없어도 충분히 빠름
        )

    def encode_query(self, query: str) -> np.ndarray:
        """쿼리(채용공고) 임베딩"""
        return self.encode([query])[0]
