import asyncio
import time
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..core.services import embedding_service, reranker, llm, chroma_client
from ..models import sql as models
from ..schemas.response import CandidateScore

async def process_screening_task(session_id: int, job_description: str, top_n: int):
    """
    Background task for screening resumes.
    Updates the database with progress and results.
    """
    db: Session = SessionLocal()
    try:
        # Update status to PROCESSING
        session = db.query(models.ScreeningSession).filter(models.ScreeningSession.id == session_id).first()
        if not session:
            return
        
        session.status = "PROCESSING"
        db.commit()

        start_time = time.time()

        # 1. Get all resumes from ChromaDB
        total_resumes_count = chroma_client.collection.count()
        if total_resumes_count == 0:
            session.status = "FAILED"
            session.processing_time = 0
            db.commit()
            return

        # Update total count
        session.total_processed = total_resumes_count
        db.commit()

        # 2. Embedding & Filtering
        jd_embedding = embedding_service.encode_query(job_description)
        search_results = chroma_client.query(jd_embedding.tolist(), n_results=min(50, total_resumes_count))

        top_50_texts = search_results["documents"][0]
        top_50_metadatas = search_results["metadatas"][0]

        # 3. Reranking
        reranked = reranker.rerank(job_description, top_50_texts, top_n=top_n)

        # 3.5 Extract Criteria (Agentic Step 1)
        # Run in thread to avoid blocking
        criteria = await asyncio.to_thread(llm.extract_criteria, job_description)

        # 4. Gemini Analysis
        async def analyze_and_save(i: int, result: dict):
            try:
                doc_index = result.get("index", i)
                score = result.get("relevance_score", 0.0)

                if isinstance(result.get("document"), dict):
                    doc_text = result.get("document", {}).get("text", "")
                else:
                    doc_text = top_50_texts[doc_index]

                name = f"Candidate {i + 1}"
                filename = ""
                try:
                    metadata = top_50_metadatas[doc_index]
                    filename = metadata.get("filename", "")
                    if filename:
                        name = filename.rsplit(".", 1)[0]
                except (IndexError, KeyError, AttributeError, TypeError):
                    pass

                # Run LLM tasks
                jina_reasoning = await asyncio.to_thread(
                    llm.generate_candidate_summary, doc_text, job_description
                )

                analysis = await asyncio.to_thread(
                    llm.analyze_candidate, doc_text, job_description, criteria
                )

                # Save Candidate to DB immediately (or you could batch, but immediate is better for progress)
                # Note: We need a new DB session for thread safety if using threads, 
                # but here we are in async loop, so we can use the main db session if we are careful.
                # However, SQLAlchemy session is not thread-safe. 
                # Since we are using asyncio, we are in a single thread.
                
                candidate = models.Candidate(
                    session_id=session_id,
                    name=name,
                    email=None,
                    filename=filename,
                    # resume_text=doc_text, # Removed for stateless architecture

                    jina_score=score,
                    jina_reasoning=jina_reasoning,
                    gemini_score=analysis.get("gemini_score", 0),
                    gemini_analysis=analysis["analysis"],
                    thinking_process=analysis["thinking_process"],
                )
                db.add(candidate)
                
                # Update progress
                # We need to refresh session to update processed_count
                # But we can't easily increment safely without locking or atomic update.
                # Simple way:
                session.processed_count += 1
                db.commit()
                
            except Exception as e:
                print(f"Error analyzing candidate {i}: {e}")

        # Run analysis concurrently
        await asyncio.gather(
            *[analyze_and_save(i, result) for i, result in enumerate(reranked)]
        )

        # Finish
        processing_time = time.time() - start_time
        session.processing_time = processing_time
        session.status = "COMPLETED"
        db.commit()

    except Exception as e:
        print(f"Task failed: {e}")
        session = db.query(models.ScreeningSession).filter(models.ScreeningSession.id == session_id).first()
        if session:
            session.status = "FAILED"
            db.commit()
    finally:
        db.close()
