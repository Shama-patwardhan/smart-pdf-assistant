# Smart PDF Assistant

## Overview

Smart PDF Assistant is a Retrieval-Augmented Generation (RAG) application that enables users to upload PDF documents and ask natural language questions about their contents. Instead of relying on the language model's general knowledge, the system retrieves the most relevant sections from the uploaded documents using semantic search and generates responses grounded in those retrieved passages.

Each answer includes the supporting document chunks, page references, and a confidence score to help users verify the response.

## Features

- Upload and index PDF documents
- Extract text from PDFs using PyMuPDF
- Split documents into semantic text chunks
- Generate embeddings using Sentence Transformers
- Store and search embeddings using FAISS
- Ask natural language questions about uploaded documents
- Generate grounded responses using the Groq API
- Display supporting source chunks and page numbers
- View and manage indexed documents
- Search within a specific document or across all uploaded documents

---

## Technology Stack

### Backend
- FastAPI
- FAISS
- Sentence Transformers
- PyMuPDF
- Groq API
- Pydantic

### Frontend
- Streamlit
- HTML/CSS

---

## System Architecture

```
User
   │
   ▼
Streamlit Frontend
   │
   ▼
FastAPI Backend
   │
   ├── PDF Processing
   ├── Text Chunking
   ├── Embedding Generation
   ├── FAISS Vector Search
   └── Groq LLM
```

---

## Workflow

1. A user uploads a PDF document.
2. The document text is extracted page by page.
3. The extracted text is divided into overlapping chunks.
4. Embeddings are generated for every chunk.
5. The embeddings and metadata are stored in a FAISS vector index.
6. When the user asks a question, an embedding is generated for the query.
7. The system retrieves the most relevant chunks from the vector database.
8. The retrieved context is provided to the Groq language model.
9. The generated answer, supporting sources, and confidence score are returned to the user.

---

## Project Structure

```
backend/
    app/
        routers/
        services/
        models/
        utils/

frontend/
    assets/
    app.py

data/
    faiss/
    uploads/

requirements.txt
README.md
```

---

## Installation

Clone the repository.

```bash
git clone https://github.com/Shama-patwardhan/smart-pdf-assistant.git
cd smart-pdf-assistant
```

Install the required dependencies.

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_api_key
```

---

## Running the Application

Start the backend.

```bash
uvicorn backend.app.main:app --reload
```

The API will be available at:

```
http://127.0.0.1:8000
```

Swagger documentation:

```
http://127.0.0.1:8000/docs
```

Start the frontend.

```bash
streamlit run frontend/app.py
```

---

## API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/upload/` | Upload and index a PDF document |
| POST | `/chat/` | Ask a question about indexed documents |
| GET | `/documents/` | List indexed documents |
| DELETE | `/documents/{filename}` | Delete an indexed document |

---

## Limitations

- Only text-based PDFs are currently supported.
- Scanned PDFs requiring OCR are not supported.
- Responses are limited to the information contained in the uploaded documents.
- Authentication and multi-user support are not implemented.

---

## Future Improvements

- OCR support for scanned PDFs
- Hybrid retrieval combining keyword and vector search
- Conversation memory
- Multi-document summarization
- Docker deployment
- Cloud deployment
- Frontend migration to React or Next.js
- User authentication
