# Smart PDF Assistant

A modern Retrieval-Augmented Generation (RAG) application that enables users to upload PDF documents, ask natural language questions, retrieve grounded answers with citations, and generate AI-powered study sheets.

Unlike traditional chatbots, Smart PDF Assistant combines semantic search with Large Language Models (LLMs) to produce responses based only on the uploaded documents, making the answers explainable, verifiable, and context-aware.

---

# Features

- Upload and index PDF documents
- Semantic document retrieval using vector embeddings
- Chat with uploaded documents using natural language
- Grounded AI responses with page-level citations
- Similarity scores for retrieved sources
- Suggested follow-up questions
- AI-generated study sheets
- Markdown rendering with KaTeX support
- Global and document-specific search
- Document management (view and delete indexed documents)
- Responsive React interface
- Secure document storage using Supabase Storage
- Light and dark themes

---

# Screenshots

## Workspace

Upload PDFs, browse indexed documents, ask questions globally or within a specific document, and receive AI-powered responses.



---

## AI Chat

Grounded responses generated from uploaded documents with inline source references.



---

## Source Citations

Every response includes supporting document chunks, page references, and similarity scores for transparency.



---

## Study Sheet Generation

Generate structured study notes directly from uploaded PDFs.

### Generation Progress



### Generated Study Sheet



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

```text
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
| PDF Extraction |                      | Query Embedding           |
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
                    |      Groq LLM        |
                    +----------+-----------+
                               |
                               ▼
                    AI Response + Citations
```

---

# Workflow

## Document Processing

1. Upload a PDF document.
2. Extract text using PyMuPDF.
3. Split the document into semantic chunks.
4. Generate vector embeddings.
5. Index document chunks for semantic retrieval.
6. Store the original PDF in Supabase Storage.

## Question Answering

1. User submits a question.
2. The question is embedded into vector space.
3. Relevant document chunks are retrieved.
4. Retrieved context is sent to the Groq LLM.
5. The model generates a grounded response.
6. Supporting citations and similarity scores are displayed.

## Study Sheet Generation

1. Analyze the uploaded document.
2. Identify key concepts and structure.
3. Generate organized notes in Markdown.
4. Render mathematical expressions using KaTeX.
5. Allow regeneration or copy-to-clipboard.

---

# Project Structure

```text
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

API Documentation:

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
| POST | `/chat/` | Ask questions about uploaded documents |
| POST | `/study-sheet/` | Generate AI study notes |
| GET | `/documents/` | List indexed documents |
| DELETE | `/documents/{filename}` | Delete an indexed document |

---

# Current Limitations

- Supports text-based PDFs only.
- OCR for scanned documents is not implemented.
- Authentication and multi-user support are not yet available.
- Optimized for educational and research documents.

---

# Future Improvements

- OCR support for scanned PDFs
- Hybrid retrieval (vector + keyword search)
- Conversation history across sessions
- Multi-document summarization
- User authentication
- Docker support
- Cloud deployment
- Streaming AI responses
- Inline PDF citation highlighting

---

# License

This project is intended for educational and portfolio purposes.
