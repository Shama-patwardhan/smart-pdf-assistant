export interface DocumentInfo {
  filename: string
  page_count: number
  chunk_count: number
}

export interface SourceCitation {
  filename: string
  page_number: number
  chunk_text: string
  similarity_score: number
}

export interface ChatHistoryItem {
  role: "user" | "assistant"
  content: string
}

export interface ChatRequest {
  question: string
  filename?: string | null
  history?: ChatHistoryItem[]
}

export interface ChatResponse {
  answer: string
  confidence: number
  sources: SourceCitation[]
}

export interface UploadResponse {
  filename: string
  page_count: number
  chunk_count: number
  message: string
  suggested_questions?: string[]
}

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  confidence?: number
  sources?: SourceCitation[]
  timestamp: string
}
