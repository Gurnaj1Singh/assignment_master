import os
from pathlib import Path

# Get the absolute path to the project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "assignments")
os.makedirs(UPLOAD_DIR, exist_ok=True)

import uuid
from uuid import UUID 
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy import text  
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Submission, TextVector, User
from .auth import get_current_user
from ..core.utils import extract_text_from_pdf
from ..core.brain import NLPProcessor
from ..core.analysis import run_plagiarism_check

router = APIRouter()
nlp = NLPProcessor() 


@router.post("/submit/{task_id}")
async def submit_assignment(
    task_id: UUID, # Changed from str to UUID
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # 0. Safety Check: Only Students can submit
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can submit assignments")

    # 1. Save the file locally
    file_ext = file.filename.split(".")[-1]
    if file_ext.lower() != "pdf":
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    file_name = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # 2. Extract Text
    text_content = extract_text_from_pdf(file_path)
    if not text_content:
        raise HTTPException(status_code=400, detail="Could not read PDF content or PDF is empty")

    # 3. Create the Submission record
    new_submission = Submission(
        task_id=task_id,
        student_id=current_user.id,
        file_path=file_path
    )
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    # 4. Process with "The Brain" (SBERT)
    # Hint: get_chunks also returns paragraphs, but here we prioritize sentences for granular detection
    _, sentences = nlp.get_chunks(text_content)
    
    if not sentences:
         raise HTTPException(status_code=400, detail="No readable sentences found in assignment")

    # Vectorize and Store
    sentence_vectors = nlp.generate_embeddings(sentences)
    for i, (text, vector) in enumerate(zip(sentences, sentence_vectors)):
        v_record = TextVector(
            submission_id=new_submission.id,
            content_chunk=text,
            embedding=vector,
            type="sentence",
            seq_order=i
        )
        db.add(v_record)

    db.commit() # Push all vectors to DB before running analysis

    # 5. TRIGGER ANALYSIS
    # This calls your core/analysis.py logic
    score, details = run_plagiarism_check(db, new_submission.id, task_id)

    # 6. UPDATE SUBMISSION WITH SCORE
    new_submission.overall_similarity_score = score
    db.commit()

    return {
        "message": "Assignment submitted and analyzed successfully",
        "plagiarism_score": f"{score}%",
        "submission_id": str(new_submission.id),
        "matches_found": len(details),
        "sentences_processed": len(sentences)
    }

@router.get("/report/{task_id}")
async def get_assignment_report(
    task_id: UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only professors can see reports
    if current_user.role != "professor":
        raise HTTPException(status_code=403, detail="Unauthorized")

    results = db.query(User.name, Submission.overall_similarity_score, Submission.submitted_at)\
        .join(Submission, User.id == Submission.student_id)\
        .filter(Submission.task_id == task_id)\
        .order_by(Submission.overall_similarity_score.desc())\
        .all()
    
    return [{"student": r[0], "score": r[1], "time": r[2]} for r in results]

@router.get("/matrix/{task_id}")
async def get_similarity_matrix(
    task_id: UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "professor":
        raise HTTPException(status_code=403, detail="Unauthorized")

    # SQL logic to find pairs of students with high matches
    query = text("""
        SELECT 
            u1.name AS student_a, 
            u2.name AS student_b, 
            COUNT(*) AS matching_sentences
        FROM text_vectors v1
        JOIN text_vectors v2 ON v1.content_chunk = v2.content_chunk 
        JOIN submissions s1 ON v1.submission_id = s1.id
        JOIN submissions s2 ON v2.submission_id = s2.id
        JOIN users u1 ON s1.student_id = u1.id
        JOIN users u2 ON s2.student_id = u2.id
        WHERE s1.task_id = :task_id 
          AND s1.id < s2.id
        GROUP BY u1.name, u2.name
        HAVING COUNT(*) > 5
    """)
    
    matrix = db.execute(query, {"task_id": task_id}).all()
    return [{"pair": f"{m[0]} & {m[1]}", "shared_sentences": m[2]} for m in matrix]

@router.get("/submission-detail/{submission_id}")
async def get_submission_detail(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "professor":
        raise HTTPException(status_code=403, detail="Unauthorized")

    # This query finds the matches for THIS specific submission
    query = text("""
        SELECT 
            v1.content_chunk AS student_text,
            v2.content_chunk AS matched_text,
            u_source.name AS copied_from,
            1 - (v1.embedding <=> v2.embedding) AS similarity
        FROM text_vectors v1
        JOIN text_vectors v2 ON v1.submission_id != v2.submission_id
        JOIN submissions s_source ON v2.submission_id = s_source.id
        JOIN users u_source ON s_source.student_id = u_source.id
        WHERE v1.submission_id = :sub_id
          AND (1 - (v1.embedding <=> v2.embedding)) > 0.85
        ORDER BY v1.seq_order ASC
    """)
    
    matches = db.execute(query, {"sub_id": submission_id}).all()
    
    return [
        {
            "original": m.student_text,
            "matched": m.matched_text,
            "source_student": m.copied_from,
            "similarity": round(m.similarity * 100, 2)
        } for m in matches
    ]

import networkx as nx # You'll need to run: pip install networkx

@router.get("/collusion-groups/{task_id}")
async def get_collusion_groups(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "professor":
        raise HTTPException(status_code=403, detail="Unauthorized")

    # 1. Fetch all pairs with high similarity (> 70% overall)
    query = text("""
        SELECT u1.name, u2.name
        FROM submissions s1
        JOIN submissions s2 ON s1.task_id = s2.task_id AND s1.id < s2.id
        JOIN users u1 ON s1.student_id = u1.id
        JOIN users u2 ON s2.student_id = u2.id
        WHERE s1.task_id = :task_id 
          AND (s1.overall_similarity_score > 30 OR s2.overall_similarity_score > 30)
    """)
    pairs = db.execute(query, {"task_id": task_id}).all()

    # 2. Use NetworkX to find "Connected Components"
    if not pairs:
        return {"total_groups": 0, "groups": []} # Always return the key 'groups'

    G = nx.Graph()
    for p1, p2 in pairs:
        G.add_edge(p1, p2)

    clusters = [list(c) for c in nx.connected_components(G)]
    return {"total_groups": len(clusters), "groups": clusters}



