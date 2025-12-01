import os
from ..core.services import chroma_client, parser
from ..core.config import get_settings

settings = get_settings()

def get_resume_text(filename: str) -> str:
    """
    Fetches resume text from ChromaDB or File System.
    Prioritizes ChromaDB for speed, falls back to File System if not found.
    """
    if not filename:
        return ""

    # 1. Try ChromaDB
    try:
        # ChromaDB collection.get supports filtering by metadata
        results = chroma_client.collection.get(
            where={"filename": filename},
            limit=1,
            include=["documents"]
        )
        if results["documents"] and len(results["documents"]) > 0:
            doc = results["documents"][0]
            if doc: # Ensure it's not None or empty
                return doc
    except Exception as e:
        print(f"Error fetching from ChromaDB for {filename}: {e}")

    # 2. Try File System
    try:
        file_path = os.path.join(settings.upload_dir, filename)
        if os.path.exists(file_path):
            return parser.parse_resume(file_path) or ""
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
    
    return ""
