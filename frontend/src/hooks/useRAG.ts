import * as React from "react"
import type { DocumentInfo, Message, ChatHistoryItem } from "../types"
import { apiService } from "../services/api"
import { useToast } from "../components/ui/Toast"

export const useRAG = () => {
  const { toast } = useToast()
  const [documents, setDocuments] = React.useState<DocumentInfo[]>([])
  const [selectedDocument, setSelectedDocument] = React.useState<string | null>(null)
  
  // Conversations stored separately for each file key (or "global" for All Documents mode)
  const [conversations, setConversations] = React.useState<Record<string, Message[]>>({})
  
  // Suggested questions mapped by filename (including global default queries)
  const [suggestedQuestions, setSuggestedQuestions] = React.useState<Record<string, string[]>>({
    global: [
      "Compare the main findings across all uploaded documents.",
      "What are the common methodologies used in these documents?",
      "Summarize the key conclusions from the indexed files."
    ]
  })
  
  // Study Sheets cached by filename
  const [studySheets, setStudySheets] = React.useState<Record<string, string>>({})
  const [isStudySheetLoading, setIsStudySheetLoading] = React.useState(false)

  const [isUploading, setIsUploading] = React.useState(false)
  const [isDeleting, setIsDeleting] = React.useState<string | null>(null)
  const [isChatLoading, setIsChatLoading] = React.useState(false)

  const activeKey = selectedDocument || "global"
  const messages = conversations[activeKey] || []

  const fetchDocs = React.useCallback(async () => {
    try {
      const docs = await apiService.getDocuments()
      setDocuments(docs)
    } catch (err: any) {
      toast({ title: "Error", description: err?.message || "Failed to load indexed documents.", type: "error" })
    }
  }, [toast])

  const uploadFile = React.useCallback(async (file: File) => {
    setIsUploading(true)
    try {
      const response = await apiService.uploadDocument(file)
      
      // Store suggested questions generated for the newly uploaded PDF in state
      if (response.suggested_questions) {
        setSuggestedQuestions(prev => ({
          ...prev,
          [response.filename]: response.suggested_questions || []
        }))
      }
      
      await fetchDocs() // refresh list
      return response
    } catch (err: any) {
      toast({ title: "Upload Failed", description: err?.message || "Document ingestion failed.", type: "error" })
      throw err
    } finally {
      setIsUploading(false)
    }
  }, [fetchDocs, toast])

  const deleteDoc = React.useCallback(async (filename: string) => {
    setIsDeleting(filename)
    try {
      await apiService.deleteDocument(filename)
      if (selectedDocument === filename) {
        setSelectedDocument(null)
      }
      // Remove suggested questions cache for deleted document
      setSuggestedQuestions(prev => {
        const copy = { ...prev }
        delete copy[filename]
        return copy
      })
      // Clear conversation history cache for deleted document
      setConversations(prev => {
        const copy = { ...prev }
        delete copy[filename]
        return copy
      })
      // Clear study sheet cache for deleted document
      setStudySheets(prev => {
        const copy = { ...prev }
        delete copy[filename]
        return copy
      })
      await fetchDocs()
      toast({ title: "Deleted", description: `Document '${filename}' deleted successfully.`, type: "success" })
    } catch (err: any) {
      toast({ title: "Deletion Failed", description: err?.message || "Failed to delete document.", type: "error" })
      throw err
    } finally {
      setIsDeleting(null)
    }
  }, [selectedDocument, fetchDocs, toast])

  const askQuestion = React.useCallback(async (question: string) => {
    if (!question.trim()) return

    setIsChatLoading(true)

    // Slice recent history to the last 6 exchanges (12 items) to limit tokens
    const currentHistory = conversations[activeKey] || []
    const historyPayload: ChatHistoryItem[] = currentHistory.slice(-12).map(msg => ({
      role: msg.role,
      content: msg.content
    }))

    const userMessage: Message = {
      id: Math.random().toString(36).substring(7),
      role: "user",
      content: question.trim(),
      timestamp: new Date().toLocaleTimeString(),
    }

    setConversations(prev => ({
      ...prev,
      [activeKey]: [...(prev[activeKey] || []), userMessage]
    }))

    try {
      const response = await apiService.queryChat({
        question: question.trim(),
        filename: selectedDocument,
        history: historyPayload,
      })

      const assistantMessage: Message = {
        id: Math.random().toString(36).substring(7),
        role: "assistant",
        content: response.answer,
        confidence: response.confidence,
        sources: response.sources,
        timestamp: new Date().toLocaleTimeString(),
      }
      
      const updatedMessages = [...(currentHistory || []), userMessage, assistantMessage]

      setConversations(prev => ({
        ...prev,
        [activeKey]: updatedMessages
      }))

      // Persist to backend after a successful exchange
      await apiService.saveChatHistory(selectedDocument, updatedMessages)
      
    } catch (err: any) {
      const errorMessage: Message = {
        id: Math.random().toString(36).substring(7),
        role: "assistant",
        content: `Error responding to query: ${err?.message || "Server unreachable."}`,
        timestamp: new Date().toLocaleTimeString(),
      }
      setConversations(prev => ({
        ...prev,
        [activeKey]: [...(prev[activeKey] || []), errorMessage]
      }))
      toast({ title: "Chat Error", description: err?.message || "Failed to complete chat query.", type: "error" })
    } finally {
      setIsChatLoading(false)
    }
  }, [activeKey, conversations, selectedDocument, toast])

  const clearChat = React.useCallback(async () => {
    try {
      await apiService.clearChatHistory(selectedDocument)
      setConversations(prev => ({
        ...prev,
        [activeKey]: []
      }))
      toast({ title: "Chat Cleared", description: "Conversation history has been cleared.", type: "success" })
    } catch (err: any) {
      console.error(`Failed to clear chat for ${activeKey}:`, err)
      toast({ title: "Error", description: err?.message || "Failed to clear chat history.", type: "error" })
    }
  }, [activeKey, selectedDocument, toast])

  const fetchQuestionsForDoc = React.useCallback(async (filename: string) => {
    // Avoid double fetching if questions are already present in state cache map
    if (filename in suggestedQuestions) return
    try {
      const qs = await apiService.getSuggestedQuestions(filename)
      setSuggestedQuestions(prev => ({
        ...prev,
        [filename]: qs || []
      }))
    } catch (err) {
      console.error(`Failed to fetch suggested questions for ${filename}:`, err)
      // Cache empty list to prevent infinite loop of query failures
      setSuggestedQuestions(prev => ({
        ...prev,
        [filename]: []
      }))
    }
  }, [suggestedQuestions])

  const fetchHistoryForDoc = React.useCallback(async (scope: string, filename: string | null) => {
    // Avoid double fetching if history is already loaded for this scope
    if (scope in conversations) return
    try {
      const history = await apiService.getChatHistory(filename)
      setConversations(prev => ({
        ...prev,
        [scope]: history || []
      }))
    } catch (err) {
      console.error(`Failed to fetch chat history for ${scope}:`, err)
      // Cache empty array to avoid looping
      setConversations(prev => ({
        ...prev,
        [scope]: []
      }))
    }
  }, [conversations])

  const fetchStudySheet = React.useCallback(async (filename: string, force: boolean = false) => {
    if (!force && filename in studySheets) return
    setIsStudySheetLoading(true)
    try {
      const content = await (force 
        ? apiService.generateStudySheet(filename, true) 
        : apiService.getStudySheet(filename))
      setStudySheets(prev => ({
        ...prev,
        [filename]: content
      }))
      if (force) {
        toast({ title: "Success", description: "Study sheet generated.", type: "success" })
      }
    } catch (err: any) {
      // If 404 on initial get, it just means not generated yet. Don't show error banner.
      if (!force && err.message?.includes("404")) {
        setStudySheets(prev => ({ ...prev, [filename]: "" })) // Cache empty to avoid retries
      } else {
        console.error(`Failed to fetch/generate study sheet for ${filename}:`, err)
        toast({ title: "Error", description: err?.message || "Failed to process study sheet.", type: "error" })
      }
    } finally {
      setIsStudySheetLoading(false)
    }
  }, [studySheets, toast])
  
  const generateStudySheet = React.useCallback(async (filename: string) => {
    return fetchStudySheet(filename, true)
  }, [fetchStudySheet])

  // Automatically fetch suggested questions and study sheet when selected document changes
  React.useEffect(() => {
    if (selectedDocument) {
      fetchQuestionsForDoc(selectedDocument)
      fetchStudySheet(selectedDocument)
    }
  }, [selectedDocument, fetchQuestionsForDoc, fetchStudySheet])
  
  // Automatically fetch chat history when scope changes
  React.useEffect(() => {
    fetchHistoryForDoc(activeKey, selectedDocument)
  }, [activeKey, selectedDocument, fetchHistoryForDoc])

  // Initial fetch on mount
  React.useEffect(() => {
    fetchDocs()
  }, [fetchDocs])

  return {
    documents,
    selectedDocument,
    messages,
    isUploading,
    isDeleting,
    isChatLoading,
    suggestedQuestions,
    studySheets,
    isStudySheetLoading,
    setSelectedDocument,
    fetchDocs,
    uploadFile,
    deleteDoc,
    askQuestion,
    clearChat,
    generateStudySheet,
  }
}
