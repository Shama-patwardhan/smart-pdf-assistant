# Smart PDF Assistant

A modern Retrieval-Augmented Generation (RAG) application that allows users to upload PDF documents, chat with their contents, and generate structured study sheets using Large Language Models.

The application combines semantic search with LLM-powered reasoning to provide accurate, source-grounded answers instead of relying solely on the model's general knowledge.

---

## Features

- Upload and process PDF documents
- Semantic document search using vector embeddings
- Ask natural language questions about uploaded PDFs
- AI-generated answers with supporting citations
- Page-level source references
- Suggested follow-up questions
- AI-powered study sheet generation
- Markdown and mathematical equation rendering (KaTeX)
- Document management (view and delete indexed documents)
- Modern responsive React interface
- Secure document storage using Supabase Storage

---

# Technology Stack

## Backend

- FastAPI
- Python
- Sentence Transformers
- PyMuPDF
- Groq API
- Pydantic

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS

## Storage

- Supabase Storage

---

# System Architecture

```
                    +----------------------+
                    |    React Frontend    |
                    +----------+-----------+
                               |
                               |
                    REST API (FastAPI)
                               |
        +----------------------+----------------------+
        |                                             |
        |                                             |
 PDF Upload                                   Chat Requests
        |                                             |
        ▼                                             ▼
+----------------+                      +---------------------------+
| PDF Extraction |                      |  Query Embedding          |
|   (PyMuPDF)    |                      +-------------+-------------+
+-------+--------+                                    |
        |                                             |
        ▼                                             ▼
+----------------+                      +---------------------------+
| Text Chunking  |                      | Semantic Retrieval        |
+-------+--------+                      +-------------+-------------+
        |                                             |
        ▼                                             ▼
+----------------+                      +---------------------------+
| Embedding      |                      | Relevant Context          |
| Generation     |                      +-------------+-------------+
+-------+--------+                                    |
        |                                             |
        +--------------------+------------------------+
                             |
                             ▼
                    +----------------------+
                    |     Groq LLM         |
                    +----------+-----------+
                               |
                               ▼
                    AI Response + Sources
```

---

# Workflow

### Document Processing

1. Upload a PDF document.
2. Extract text using PyMuPDF.
3. Split the document into semantic chunks.
4. Generate embeddings for each chunk.
5. Index the document for semantic retrieval.
6. Store the original PDF securely in Supabase Storage.

### Question Answering

1. User submits a question.
2. The query is converted into an embedding.
3. The system retrieves the most relevant document chunks.
4. Retrieved context is sent to the Groq language model.
5. The assistant generates a grounded answer with citations.
6. Supporting document excerpts and page numbers are displayed.

---

# Project Structure

```
Smart PDF Assistant
│
├── backend/
│   └── app/
│       ├── models/
│       ├── routers/
│       ├── services/
│       ├── utils/
│       └── main.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── services/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
│
├── data/
├── .env.example
├── requirements.txt
└── README.md
```

---

# Installation

Clone the repository.

```bash
git clone https://github.com/Shama-patwardhan/smart-pdf-assistant.git
cd smart-pdf-assistant
```

---

## Backend Setup

Create a virtual environment.

```bash
python -m venv venv
```

Activate it.

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install backend dependencies.

```bash
pip install -r requirements.txt
```

---

## Frontend Setup

```bash
cd frontend
npm install
```

---

# Environment Variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key

SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_BUCKET=your_bucket_name
```

---

# Running the Application

## Start the Backend

```bash
uvicorn backend.app.main:app --reload
```

Backend:

```
http://127.0.0.1:8000
```

Swagger Documentation:

```
http://127.0.0.1:8000/docs
```

---

## Start the Frontend

```bash
cd frontend
npm run dev
```

Frontend:

```
http://localhost:5173
```

---

# API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/upload/` | Upload and index a PDF |
| POST | `/chat/` | Ask questions about indexed documents |
| POST | `/study-sheet/` | Generate study notes |
| GET | `/documents/` | List uploaded documents |
| DELETE | `/documents/{filename}` | Delete a document |

---

# Current Limitations

- Supports text-based PDFs only
- OCR for scanned documents is not implemented
- Authentication is not available
- Designed for single-user usage

---

# Future Improvements

- OCR support for scanned PDFs
- Hybrid retrieval (vector + keyword search)
- Conversation history across sessions
- Multi-document summarization
- Authentication and user accounts
- Docker support
- Cloud deployment
- Streaming responses
- Citation highlighting inside the PDF

---

# License

This project is intended for educational and portfolio purposes.
