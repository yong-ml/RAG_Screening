import httpx
from typing import List, Dict


class JinaRerankerService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.jina.ai/v1/rerank"

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 10
    ) -> List[Dict]:
        """Jina Reranker로 재정렬"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "jina-reranker-v2-base-multilingual",
            "query": query,
            "documents": documents,
            "top_n": top_n
        }

        response = httpx.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=60.0
        )

        if response.status_code == 200:
            result = response.json()
            return result.get('results', [])
        else:
            raise Exception(f"Jina Reranker API error: {response.status_code} - {response.text}")
