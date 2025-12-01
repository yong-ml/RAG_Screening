from .config import get_settings
from ..services.embedding import EmbeddingService
from ..services.parser import ResumeParser
from ..services.reranker import JinaRerankerService
from ..services.llm import GeminiService
from ..models.database import ChromaDBClient

settings = get_settings()

# Initialize Services (Singleton)
embedding_service = EmbeddingService(settings.embedding_model)
parser = ResumeParser()
reranker = JinaRerankerService(settings.jina_api_key)
llm = GeminiService(settings.gemini_api_key)
chroma_client = ChromaDBClient(settings.chroma_db_path)
