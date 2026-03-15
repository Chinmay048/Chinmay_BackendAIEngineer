from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class SourceDocument(Base):
    __tablename__ = "source_documents"
    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)

class ContentChunk(Base):
    __tablename__ = "content_chunks"
    id = Column(String, primary_key=True, default=generate_uuid)
    source_id = Column(String, ForeignKey("source_documents.id"))
    grade = Column(Integer)
    subject = Column(String)
    topic = Column(String)
    text = Column(Text, nullable=False)

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id = Column(String, primary_key=True, default=generate_uuid)
    chunk_id = Column(String, ForeignKey("content_chunks.id"))
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False)
    options = Column(Text) # Stored as JSON string
    correct_answer = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)

class StudentAnswer(Base):
    __tablename__ = "student_answers"
    id = Column(String, primary_key=True, default=generate_uuid)
    student_id = Column(String, nullable=False)
    question_id = Column(String, ForeignKey("quiz_questions.id"))
    selected_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)