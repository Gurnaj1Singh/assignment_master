from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID

def run_plagiarism_check(db: Session, submission_id: UUID, task_id: UUID):
    """
    Compares a new submission's vectors against all previous submissions 
    in the same task to find matches.
    """
    
    # 1. THE CORE AI QUERY
    # We use (1 - distance) to get a Similarity Score between 0 and 1.
    # 0.85 is a good threshold for "Semantic Plagiarism."
    query = text("""
        SELECT 
            v1.content_chunk AS student_sentence,
            v2.content_chunk AS matched_sentence,
            u.name AS matched_student_name,
            1 - (v1.embedding <=> v2.embedding) AS similarity_score
        FROM text_vectors v1
        JOIN text_vectors v2 ON v1.submission_id != v2.submission_id
        JOIN submissions s ON v2.submission_id = s.id
        JOIN users u ON s.student_id = u.id
        WHERE v1.submission_id = :sub_id
          AND s.task_id = :task_id
          AND v1.type = 'sentence'
          AND (1 - (v1.embedding <=> v2.embedding)) > 0.85
    """)

    results = db.execute(query, {
        "sub_id": submission_id, 
        "task_id": task_id
    }).all()

    # 2. CALCULATE OVERALL SCORE
    # Get total count of sentences in the current submission
    total_sentences_query = text("""
        SELECT count(*) FROM text_vectors 
        WHERE submission_id = :sub_id AND type = 'sentence'
    """)
    total_sentences = db.execute(total_sentences_query, {"sub_id": submission_id}).scalar()

    if total_sentences == 0:
        return 0.0, []

    # Number of unique sentences that were flagged as plagiarized
    flagged_sentences = len(set([r.student_sentence for r in results]))
    
    overall_score = (flagged_sentences / total_sentences) * 100

    return round(overall_score, 2), results