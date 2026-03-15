from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import pypdf
import io
import os
import json
import requests
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base, get_db
import models

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Peblo AI Backend Engine")

# Create the tables in the database
Base.metadata.create_all(bind=engine)

# Allow external connections (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Peblo Backend is running securely!"}

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    content = await file.read()
    pdf_reader = pypdf.PdfReader(io.BytesIO(content))
    
    extracted_text = ""
    for page in pdf_reader.pages:
        extracted_text += page.extract_text() + "\n"

    cleaned_text = " ".join(extracted_text.split())

    new_document = models.SourceDocument(filename=file.filename)
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    chunk_size = 500
    text_chunks = [cleaned_text[i:i + chunk_size] for i in range(0, len(cleaned_text), chunk_size)]
    
    for chunk in text_chunks:
        new_chunk = models.ContentChunk(
            source_id=new_document.id,
            grade=0,
            subject="Extracted",
            topic="General",
            text=chunk
        )
        db.add(new_chunk)
    
    db.commit()
    return {
        "message": f"Successfully ingested {file.filename}",
        "document_id": new_document.id,
        "total_chunks_saved": len(text_chunks)
    }

class QuizGenerationRequest(BaseModel):
    document_id: str

@app.post("/generate-quiz")
async def generate_quiz(request: QuizGenerationRequest, db: Session = Depends(get_db)):
    chunks = db.query(models.ContentChunk).filter(models.ContentChunk.source_id == request.document_id).all()
    
    if not chunks:
        raise HTTPException(status_code=404, detail="No content found for this document ID")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key is missing from .env")

    # REST API approach to bypass SDK environment conflicts
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    questions_created = 0

    for chunk in chunks:
        prompt = f"""
        You are an expert educational AI. Read the following text and generate 3 quiz questions based on it.
        You must generate at least one Multiple Choice Question (MCQ), one True/False, and one Fill in the blank.
        Assign a difficulty (easy, medium, hard) to each.

        Return the result strictly as a JSON array of objects with these exact keys:
        "question_text", "question_type", "options" (a list of strings, empty if not MCQ), "correct_answer", "difficulty".
        Do not include markdown blocks like ```json. Just return the raw JSON array.

        TEXT:
        {chunk.text}
        """

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
            
            if "error" in response_data:
                print(f"GOOGLE API ERROR for chunk {chunk.id}: {response_data['error']['message']}")
                continue

            ai_text = response_data['candidates'][0]['content']['parts'][0]['text']
            clean_json_string = ai_text.replace('```json', '').replace('```', '').strip()
            generated_questions = json.loads(clean_json_string)

            for q in generated_questions:
                new_question = models.QuizQuestion(
                    chunk_id=chunk.id,
                    question_text=q["question_text"],
                    question_type=q["question_type"],
                    options=json.dumps(q.get("options", [])), 
                    correct_answer=q["correct_answer"],
                    difficulty=q["difficulty"]
                )
                db.add(new_question)
                questions_created += 1
                
        except Exception as e:
            print(f"Failed to generate for chunk {chunk.id}. Error: {e}")
            continue

    db.commit()

    return {
        "message": "Quiz generation complete",
        "document_id": request.document_id,
        "total_questions_created": questions_created
    }

@app.get("/quiz")
def get_quiz(document_id: Optional[str] = None, difficulty: Optional[str] = None, limit: int = 5, db: Session = Depends(get_db)):
    query = db.query(models.QuizQuestion)
    
    # Filter by specific document to ensure topics do not mix
    if document_id:
        query = query.join(models.ContentChunk, models.QuizQuestion.chunk_id == models.ContentChunk.id)
        query = query.filter(models.ContentChunk.source_id == document_id)
    
    if difficulty:
        query = query.filter(models.QuizQuestion.difficulty == difficulty.lower())
    
    questions = query.order_by(models.QuizQuestion.id.desc()).limit(limit).all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found matching criteria")

    response = []
    for q in questions:
        response.append({
            "question_id": q.id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "options": json.loads(q.options) if q.options else [],
            "difficulty": q.difficulty
        })
        
    return response

class AnswerSubmission(BaseModel):
    student_id: str
    question_id: str
    selected_answer: str

@app.post("/submit-answer")
def submit_answer(submission: AnswerSubmission, db: Session = Depends(get_db)):
    question = db.query(models.QuizQuestion).filter(models.QuizQuestion.id == submission.question_id).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    is_correct = submission.selected_answer.strip().lower() == question.correct_answer.strip().lower()

    new_answer_record = models.StudentAnswer(
        student_id=submission.student_id,
        question_id=question.id,
        selected_answer=submission.selected_answer,
        is_correct=is_correct
    )
    db.add(new_answer_record)
    db.commit()

    # Adaptive Difficulty Logic
    current_difficulty = question.difficulty.lower()
    next_difficulty = current_difficulty 

    if is_correct:
        if current_difficulty == "easy":
            next_difficulty = "medium"
        elif current_difficulty == "medium":
            next_difficulty = "hard"
    else:
        if current_difficulty == "hard":
            next_difficulty = "medium"
        elif current_difficulty == "medium":
            next_difficulty = "easy"

    return {
        "student_id": submission.student_id,
        "question_id": question.id,
        "is_correct": is_correct,
        "current_question_difficulty": current_difficulty,
        "recommended_next_difficulty": next_difficulty,
        "message": "Answer recorded successfully."
    }