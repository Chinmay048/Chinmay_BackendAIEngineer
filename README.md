# Peblo AI Backend Engine

A robust, AI-driven backend pipeline designed to ingest raw educational PDFs, extract structured content, and dynamically generate adaptive quizzes using the Gemini 2.5 Flash LLM.

## Overview

This project demonstrates a complete AI-powered learning backend system that:
- **Ingests** educational content from PDF files
- **Extracts** and structures content into manageable chunks
- **Generates** quiz questions using Gemini LLM with multiple question types
- **Stores** everything in a relational SQLite database with traceability
- **Serves** quizzes through REST APIs
- **Adapts** difficulty levels based on student performance

---

## System Architecture & Data Flow

```
PDF Upload
    ↓
Content Extraction & Cleaning
    ↓
Chunk Creation (500 chars each)
    ↓
Gemini LLM Quiz Generation
    ↓
Database Storage (with traceability)
    ↓
API Endpoints (Retrieval & Submission)
    ↓
Adaptive Difficulty Calculation
```

### Key Components:

1. **Content Ingestion (`POST /ingest`)**: Uploaded PDFs are parsed using `pypdf`, cleaned, and broken into 500-character chunks.
2. **Structured Storage**: Data is persisted using **SQLite** and **SQLAlchemy ORM**. The schema utilizes UUID foreign keys to maintain strict relational mapping between Source Documents, Content Chunks, Quiz Questions, and Student Answers.
3. **AI Generation (`POST /generate-quiz`)**: Text chunks are passed to the Gemini REST API via customized system prompts to enforce strict JSON array outputs. The API bypasses standard SDKs to avoid Windows environment conflicts.
4. **Quiz Retrieval (`GET /quiz`)**: Questions are served via a GET endpoint. Uses SQL `JOIN` statements to isolate questions to specific `document_id`s, alongside optional difficulty filtering.
5. **Adaptive Logic (`POST /submit-answer`)**: Evaluates student submissions against the database and calculates the recommended next difficulty level based on performance.

---

##  Database Schema

### Tables:

**`source_documents`**
```
id (UUID, PK)
filename (String)
```

**`content_chunks`**
```
id (UUID, PK)
source_id (UUID, FK → source_documents)
grade (Integer)
subject (String)
topic (String)
text (Text)
```

**`quiz_questions`**
```
id (UUID, PK)
chunk_id (UUID, FK → content_chunks)
question_text (Text)
question_type (String) - 'MCQ', 'True/False', 'Fill_in_Blank'
options (JSON String) - ['option1', 'option2', ...]
correct_answer (String)
difficulty (String) - 'easy', 'medium', 'hard'
```

**`student_answers`**
```
id (UUID, PK)
student_id (String)
question_id (UUID, FK → quiz_questions)
selected_answer (String)
is_correct (Boolean)
```

---

##  Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone <your-repo-link>
cd peblo-backend-challenge
```

### Step 2: Create Virtual Environment (Recommended)

**On Windows:**
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Copy `.env.example` to `.env` and add your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env` and replace the placeholder:
```
GEMINI_API_KEY=your_actual_api_key_here
```

**To get a Gemini API Key:**
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Get API Key"
3. Create a new API key
4. Copy and paste it into `.env`

### Step 5: Run the Backend Server

```bash
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## 📡 API Endpoints

### 1. **Ingest PDF & Extract Content**

**Endpoint:** `POST /ingest`

**Request:**
- File upload (multipart/form-data)
- Only `.pdf` files accepted

**Example (using curl):**
```bash
curl -X POST "http://127.0.0.1:8000/ingest" \
  -F "file=@sample.pdf"
```

**Example (using Python requests):**
```python
import requests

with open('sample.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://127.0.0.1:8000/ingest', files=files)
    print(response.json())
```

**Response:**
```json
{
  "message": "Successfully ingested sample.pdf",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_chunks_saved": 12
}
```

---

### 2. **Generate Quiz Questions from Content**

**Endpoint:** `POST /generate-quiz`

**Request Body:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Example (using curl):**
```bash
curl -X POST "http://127.0.0.1:8000/generate-quiz" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

**Example (using Python):**
```python
import requests

payload = {
    "document_id": "550e8400-e29b-41d4-a716-446655440000"
}

response = requests.post(
    'http://127.0.0.1:8000/generate-quiz',
    json=payload
)
print(response.json())
```

**Response:**
```json
{
  "message": "Quiz generation complete",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_questions_created": 36
}
```

---

### 3. **Retrieve Quiz Questions**

**Endpoint:** `GET /quiz`

**Query Parameters:**
- `document_id` (optional): Filter by document
- `difficulty` (optional): `easy`, `medium`, or `hard`
- `limit` (optional, default=5): Number of questions to return

**Example (using curl):**
```bash
# Get 5 easy questions from a specific document
curl "http://127.0.0.1:8000/quiz?document_id=550e8400-e29b-41d4-a716-446655440000&difficulty=easy&limit=5"

# Get any 10 questions
curl "http://127.0.0.1:8000/quiz?limit=10"
```

**Example (using Python):**
```python
import requests

params = {
    'document_id': '550e8400-e29b-41d4-a716-446655440000',
    'difficulty': 'easy',
    'limit': 5
}

response = requests.get('http://127.0.0.1:8000/quiz', params=params)
print(response.json())
```

**Response:**
```json
[
  {
    "question_id": "660e8400-e29b-41d4-a716-446655440000",
    "question_text": "What is the capital of France?",
    "question_type": "MCQ",
    "options": ["Paris", "London", "Berlin", "Madrid"],
    "difficulty": "easy"
  },
  {
    "question_id": "770e8400-e29b-41d4-a716-446655440000",
    "question_text": "True or False: The Earth is flat.",
    "question_type": "True/False",
    "options": ["True", "False"],
    "difficulty": "easy"
  }
]
```

---

### 4. **Submit Student Answer (with Adaptive Logic)**

**Endpoint:** `POST /submit-answer`

**Request Body:**
```json
{
  "student_id": "S001",
  "question_id": "660e8400-e29b-41d4-a716-446655440000",
  "selected_answer": "Paris"
}
```

**Example (using curl):**
```bash
curl -X POST "http://127.0.0.1:8000/submit-answer" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "S001",
    "question_id": "660e8400-e29b-41d4-a716-446655440000",
    "selected_answer": "Paris"
  }'
```

**Example (using Python):**
```python
import requests

payload = {
    "student_id": "S001",
    "question_id": "660e8400-e29b-41d4-a716-446655440000",
    "selected_answer": "Paris"
}

response = requests.post(
    'http://127.0.0.1:8000/submit-answer',
    json=payload
)
print(response.json())
```

**Response (Correct Answer):**
```json
{
  "student_id": "S001",
  "question_id": "660e8400-e29b-41d4-a716-446655440000",
  "is_correct": true,
  "current_question_difficulty": "easy",
  "recommended_next_difficulty": "medium",
  "message": "Answer recorded successfully."
}
```

**Response (Incorrect Answer):**
```json
{
  "student_id": "S001",
  "question_id": "660e8400-e29b-41d4-a716-446655440000",
  "is_correct": false,
  "current_question_difficulty": "hard",
  "recommended_next_difficulty": "medium",
  "message": "Answer recorded successfully."
}
```

---

### 5. **Health Check**

**Endpoint:** `GET /`

**Example:**
```bash
curl http://127.0.0.1:8000/
```

**Response:**
```json
{
  "status": "Peblo Backend is running securely!"
}
```

---

## 🧪 Complete Testing Workflow

This example demonstrates the complete pipeline:

**Step 1: Upload a PDF**
```bash
curl -X POST "http://127.0.0.1:8000/ingest" \
  -F "file=@example.pdf"
```
Save the `document_id` from response (e.g., `550e8400-e29b-41d4-a716-446655440000`)

**Step 2: Generate Quiz from the Document**
```bash
curl -X POST "http://127.0.0.1:8000/generate-quiz" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

**Step 3: Retrieve Quiz Questions (Easy Level)**
```bash
curl "http://127.0.0.1:8000/quiz?document_id=550e8400-e29b-41d4-a716-446655440000&difficulty=easy&limit=3"
```
Save the `question_id` from response

**Step 4: Submit an Answer**
```bash
curl -X POST "http://127.0.0.1:8000/submit-answer" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "S001",
    "question_id": "QUESTION_ID_FROM_STEP_3",
    "selected_answer": "YOUR_ANSWER"
  }'
```
Observe the adaptive difficulty recommendation

---

##  Adaptive Difficulty Algorithm

The system adjusts quiz difficulty based on student performance:

| Current Difficulty | Answer | Next Difficulty |
|---|---|---|
| Easy |  Correct | Medium |
| Easy |  Incorrect | Easy (stays) |
| Medium |  Correct | Hard |
| Medium |  Incorrect | Easy |
| Hard | Correct | Hard (stays) |
| Hard |  Incorrect | Medium |

---

##  Project Structure

```
peblo-backend-challenge/
├── main.py                 # FastAPI app & endpoints
├── database.py            # SQLAlchemy setup & session management
├── models.py              # Database models (ORM)
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template (no secrets)
├── .env                  # Environment config (NOT committed)
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── peblo.db              # SQLite database (auto-created)
```

---

## 🔧 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'fastapi'"
```bash
# Ensure virtual environment is activated and dependencies are installed
pip install -r requirements.txt
```

### Error: "GEMINI_API_KEY is missing from .env"
```bash
# Make sure .env file exists and contains your API key
# cp .env.example .env
# Edit .env and add your key
```

### Error: "Address already in use" (Port 8000)
```bash
# Kill the existing process and restart
# On Windows:
taskkill /PID <process_id> /F

# Or use a different port:
uvicorn main:app --port 8001
```

### Error: "No content found for this document ID"
```bash
# Document ID doesn't exist, generate quizzes for a valid doc:
# First ensure you've uploaded a PDF and have the correct document_id
```

### Gemini API Quota Exceeded
```bash
# Wait a moment and retry
# Consider implementing rate limiting for production
```

---

##  Dependencies

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | 0.104.1 | Web framework |
| `uvicorn` | 0.24.0 | ASGI server |
| `sqlalchemy` | 2.0.23 | ORM database |
| `pypdf` | 3.17.1 | PDF extraction |
| `python-dotenv` | 1.0.0 | Environment variables |
| `requests` | 2.31.0 | HTTP calls to Gemini API |
| `pydantic` | 2.5.0 | Data validation |

---
## LLM Integration

**Model Used:** Gemini 2.5 Flash

**Approach:** REST API (not SDK) for better Windows compatibility

**Question Types Generated:**
1. Multiple Choice (MCQ) - 4 options
2. True/False
3. Fill in the Blank

**Difficulty Levels:** easy, medium, hard

**Prompt Strategy:** Custom system prompts enforce valid JSON output with no markdown blocks.

---

##  Security

- API keys are NOT committed (see `.gitignore`)
- Use `.env` for local development only
- In production, use environment variable injection
- `.env` file is listed in `.gitignore`
- CORS is enabled for development (configure for production)

---

##  Production Deployment Notes

For a production deployment, consider:

1. **Database**: Switch from SQLite to PostgreSQL
2. **API Key Management**: Use secrets management (AWS Secrets Manager, HashiCorp Vault)
3. **CORS Configuration**: Restrict origins instead of `allow_origins=["*"]`
4. **Rate Limiting**: Implement rate limits on endpoints
5. **Logging**: Add structured logging with timestamps
6. **Caching**: Implement Redis caching for frequently accessed quizzes
7. **Error Handling**: Implement custom error handlers
8. **Authentication**: Add JWT or OAuth2 authentication
9. **Monitoring**: Integrate with monitoring tools (Prometheus, DataDog)

---

##  Example Output

### Sample generated questions from a PDF about "Shapes":

**Question 1 (MCQ):**
```json
{
  "question_id": "abc123",
  "question_text": "How many sides does a triangle have?",
  "question_type": "MCQ",
  "options": ["2", "3", "4", "5"],
  "difficulty": "easy"
}
```

**Question 2 (True/False):**
```json
{
  "question_id": "def456",
  "question_text": "A square has 5 sides.",
  "question_type": "True/False",
  "options": ["True", "False"],
  "difficulty": "easy"
}
```

**Question 3 (Fill in the Blank):**
```json
{
  "question_id": "ghi789",
  "question_text": "A circle has ___ sides.",
  "question_type": "Fill_in_Blank",
  "options": [],
  "difficulty": "medium"
}
```

---

##  Key Features

✅ **PDF Content Ingestion** - Parser handles various PDF formats  
✅ **Intelligent Chunking** - 500-character chunks for optimal LLM processing  
✅ **Multi-type Questions** - MCQ, True/False, Fill in the Blank  
✅ **Adaptive Difficulty** - 3-level algorithm based on performance  
✅ **Full Traceability** - Questions link back to source content  
✅ **Clean REST API** - Follows REST conventions  
✅ **SQLite Database** - ACID transactions with proper foreign keys  
✅ **Environment Management** - Secure .env configuration  

---

##  Support

For issues or questions:
1. Check the **Troubleshooting** section above
2. Verify environment variables in `.env`
3. Ensure Python version is 3.8+
4. Check that the Gemini API key is valid and has quota

---

##  License

This is a challenge submission for Peblo AI Backend Engineer role.

---

**Last Updated:** March 16, 2026
