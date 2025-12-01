import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.core.database import SessionLocal
from backend.models import sql as models
from backend.core.services import chroma_client

def check_counts():
    db = SessionLocal()
    try:
        # SQLite counts
        session_count = db.query(models.ScreeningSession).count()
        candidate_count = db.query(models.Candidate).count()
        
        # ChromaDB count
        chroma_count = chroma_client.collection.count()
        
        # Latest Session
        latest_session = db.query(models.ScreeningSession).order_by(models.ScreeningSession.created_at.desc()).first()
        latest_candidates = 0
        if latest_session:
            latest_candidates = db.query(models.Candidate).filter(models.Candidate.session_id == latest_session.id).count()

        print(f"SQLite Sessions: {session_count}")
        print(f"SQLite Candidates: {candidate_count}")
        print(f"Latest Session Candidates: {latest_candidates}")
        print(f"ChromaDB Documents: {chroma_count}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_counts()
