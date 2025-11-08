import chromadb
from chromadb.config import Settings


class ChromaDBClient:
    def __init__(self, db_path: str):
        self.client = chromadb.PersistentClient(
            path=db_path, settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="resumes", metadata={"hnsw:space": "cosine"}  # 코사인 유사도
        )

    def add_resumes(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ):
        """이력서 임베딩과 메타데이터 저장"""
        self.collection.add(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    def query(self, query_embedding: list[float], n_results: int = 50) -> dict:
        """유사한 이력서 검색"""
        return self.collection.query(
            query_embeddings=[query_embedding], n_results=n_results
        )

    def clear(self):
        """컬렉션 초기화 (테스트용)"""
        self.client.delete_collection("resumes")
        self.collection = self.client.create_collection(
            name="resumes", metadata={"hnsw:space": "cosine"}  # 코사인 유사도
        )
