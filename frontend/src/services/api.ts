import type { DocumentInfo, ChatRequest, ChatResponse, UploadResponse, Message } from "../types"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`
    
    const headers = {
      "Accept": "application/json",
      ...(options?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...options?.headers,
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      if (!response.ok) {
        let errorMessage = `HTTP error! Status: ${response.status}`
        try {
          const errData = await response.json()
          errorMessage = errData?.detail || errorMessage
        } catch {
          // Fallback if parsing fails
        }
        throw new Error(errorMessage)
      }

      return (await response.json()) as T
    } catch (error) {
      console.error(`API request failed on endpoint ${endpoint}:`, error)
      throw error
    }
  }

  private async requestText(endpoint: string, options?: RequestInit): Promise<string> {
    const url = `${API_BASE_URL}${endpoint}`
    
    const headers = {
      "Accept": "text/plain, text/markdown, */*",
      ...(options?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...options?.headers,
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      if (!response.ok) {
        let errorMessage = `HTTP error! Status: ${response.status}`
        try {
          const errData = await response.json()
          errorMessage = errData?.detail || errorMessage
        } catch {
          // Fallback if parsing fails
        }
        throw new Error(errorMessage)
      }

      return await response.text()
    } catch (error) {
      console.error(`API text request failed on endpoint ${endpoint}:`, error)
      throw error
    }
  }

  /**
   * Fetches all indexed documents in the database
   */
  async getDocuments(): Promise<DocumentInfo[]> {
    return this.request<DocumentInfo[]>("/documents/")
  }

  /**
   * Fetches persisted suggested questions for a given document
   */
  async getSuggestedQuestions(filename: string): Promise<string[]> {
    const encodedFilename = encodeURIComponent(filename)
    return this.request<string[]>(`/documents/${encodedFilename}/questions`)
  }

  /**
   * Uploads and indexes a PDF document in the backend pipeline
   */
  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append("file", file)

    return this.request<UploadResponse>("/upload/", {
      method: "POST",
      body: formData,
    })
  }

  /**
   * Queries the grounded chat RAG pipeline
   */
  async queryChat(payload: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>("/chat/", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  }

  /**
   * Fetches the persisted chat history for a document
   */
  async getChatHistory(filename: string | null): Promise<Message[]> {
    const scope = filename ? encodeURIComponent(filename) : "global"
    return this.request<Message[]>(`/chat/${scope}/history`)
  }

  /**
   * Saves the chat history for a document
   */
  async saveChatHistory(filename: string | null, messages: Message[]): Promise<void> {
    const scope = filename ? encodeURIComponent(filename) : "global"
    return this.request<void>(`/chat/${scope}/history`, {
      method: "PUT",
      body: JSON.stringify(messages),
    })
  }

  /**
   * Clears the chat history for a document
   */
  async clearChatHistory(filename: string | null): Promise<void> {
    const scope = filename ? encodeURIComponent(filename) : "global"
    return this.request<void>(`/chat/${scope}/history`, {
      method: "DELETE",
    })
  }

  /**
   * Deletes an indexed document and its associated vectors from the store
   */
  async deleteDocument(filename: string): Promise<{ message: string }> {
    const encodedFilename = encodeURIComponent(filename)
    return this.request<{ message: string }>(`/documents/${encodedFilename}`, {
      method: "DELETE",
    })
  }

  /**
   * Fetches the study sheet for a document if it exists
   */
  async getStudySheet(filename: string): Promise<string> {
    const encodedFilename = encodeURIComponent(filename)
    return this.requestText(`/documents/${encodedFilename}/study_sheet`)
  }

  /**
   * Generates or regenerates a study sheet for a document
   */
  async generateStudySheet(filename: string, forceRegenerate: boolean = false): Promise<string> {
    const encodedFilename = encodeURIComponent(filename)
    const url = forceRegenerate 
      ? `/documents/${encodedFilename}/study_sheet?force_regenerate=true`
      : `/documents/${encodedFilename}/study_sheet`
    return this.requestText(url, { method: "POST" })
  }
}

export const apiService = new ApiService()
