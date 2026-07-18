import * as React from "react"
import { useRAG } from "../hooks/useRAG"
import { Sidebar } from "../components/layout/Sidebar"
import { UploadArea } from "../components/upload/UploadArea"
import { ChatMessage } from "../components/chat/ChatMessage"
import { Button } from "../components/ui/Button"
import { Send, BookOpen, Menu, Sun, Moon, AlertTriangle } from "lucide-react"
import { cn } from "../lib/utils"
import { StudySheetModal } from "../components/study/StudySheetModal"

export const Workspace: React.FC = () => {
  const {
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
    uploadFile,
    deleteDoc,
    askQuestion,
    clearChat,
    generateStudySheet,
  } = useRAG()

  const [input, setInput] = React.useState("")
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(false)
  const [isStudySheetModalOpen, setIsStudySheetModalOpen] = React.useState(false)
  const [isNewChatDialogOpen, setIsNewChatDialogOpen] = React.useState(false)
  
  // Theme logic
  const [isDark, setIsDark] = React.useState(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("theme")
      if (stored) return stored === "dark"
      return window.matchMedia("(prefers-color-scheme: dark)").matches
    }
    return false
  })

  React.useEffect(() => {
    const root = window.document.documentElement
    if (isDark) {
      root.classList.add("dark")
      localStorage.setItem("theme", "dark")
    } else {
      root.classList.remove("dark")
      localStorage.setItem("theme", "light")
    }
  }, [isDark])

  const chatEndRef = React.useRef<HTMLDivElement>(null)

  // Scroll to bottom on new messages
  React.useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isChatLoading])

  const submitQuestion = React.useCallback(async (question: string) => {
    if (!question.trim() || isChatLoading) return
    await askQuestion(question)
  }, [askQuestion, isChatLoading])

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!input.trim() || isChatLoading) return
    const query = input
    setInput("")
    await submitQuestion(query)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const activeQuestions = suggestedQuestions[selectedDocument || "global"] || []

  const uploadNode = (
    <UploadArea 
      onUpload={uploadFile} 
      isUploading={isUploading}
    />
  )

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      {/* Sidebar Panel overlay on mobile */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-background/60 z-30 md:hidden backdrop-blur-sm transition-opacity"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      <Sidebar
        documents={documents}
        selectedDocument={selectedDocument}
        onSelectDocument={(doc) => {
          setSelectedDocument(doc)
          setIsSidebarOpen(false) // Close mobile drawer on selection
        }}
        onDeleteDocument={deleteDoc}
        isDeleting={isDeleting}
        uploadAreaNode={uploadNode}
        suggestedQuestions={activeQuestions}
        onSelectQuestion={submitQuestion}
        className={cn(
          "fixed inset-y-0 left-0 z-40 md:relative md:translate-x-0 transition-transform duration-200",
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      />

      {/* Main Conversation Workspace */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Top Header Navigation Toolbar */}
        <header className="h-16 border-b border-border/40 px-6 md:px-8 flex items-center justify-between bg-card/20 flex-shrink-0">
          <div className="flex items-center gap-3">
            {/* Hamburger Button on mobile */}
            <Button
              variant="outline"
              size="icon"
              className="md:hidden h-8 w-8"
              onClick={() => setIsSidebarOpen(true)}
            >
              <Menu className="h-4 w-4" />
            </Button>
            
            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted-foreground select-none">Search Scope:</span>
              <span className="font-semibold px-2 py-0.5 bg-secondary rounded text-foreground border border-border/50">
                {selectedDocument || "All Documents"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsDark(!isDark)}
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              title="Toggle Theme"
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsStudySheetModalOpen(true)}
              disabled={!selectedDocument}
            >
              Study Sheet
            </Button>
            <Button variant="outline" size="sm" onClick={() => setIsNewChatDialogOpen(true)}>
              New Chat
            </Button>
          </div>
        </header>

        {/* Conversation viewport */}
        <div className="flex-1 overflow-y-auto px-4 md:px-8 py-8 flex flex-col min-h-0 custom-scrollbar">
          <div className="max-w-4xl w-full mx-auto flex-1 flex flex-col">
            {messages.length === 0 ? (
              /* Clean Modern Empty State */
              <div className="flex-1 flex items-center justify-center py-12">
                <div className="border border-border bg-card rounded-lg p-10 max-w-xl text-center space-y-6 shadow-sm">
                  <div className="h-12 w-12 rounded flex items-center justify-center mx-auto text-primary bg-primary/10">
                    <BookOpen className="h-6 w-6" />
                  </div>
                  <div className="space-y-3">
                    <h2 className="text-xl font-semibold tracking-tight text-foreground">
                      Welcome to your Workspace
                    </h2>
                    <p className="text-sm text-muted-foreground leading-relaxed px-4">
                      Upload your research papers or textbooks in the sidebar. 
                      Once indexed, you can ask natural questions and receive verified, 
                      grounded answers with direct citations.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              /* Message List */
              <div className="flex-col divide-y divide-border/20">
                {messages.map((msg) => (
                  <ChatMessage key={msg.id} message={msg} />
                ))}
                
                {/* Modern Clean Skeleton for AI Loading */}
                {isChatLoading && (
                  <div className="flex w-full gap-4 py-8 flex-row animate-pulse">
                    <div className="h-8 w-8 rounded flex items-center justify-center bg-card border border-border flex-shrink-0" />
                    <div className="flex-col space-y-3 flex-1 max-w-[80%] pt-1">
                      <div className="h-4 bg-secondary rounded w-1/4" />
                      <div className="h-4 bg-secondary rounded w-full" />
                      <div className="h-4 bg-secondary rounded w-5/6" />
                    </div>
                  </div>
                )}
                
                <div ref={chatEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* Fixed Input Composer Panel */}
        <div className="p-4 md:p-6 border-t border-border bg-card/50 flex-shrink-0">
          <form onSubmit={handleSend} className="max-w-4xl w-full mx-auto relative group">
            <div className="relative flex items-end border border-border bg-background rounded-md overflow-hidden shadow-sm focus-within:border-primary/50 transition-colors">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  selectedDocument
                    ? `Ask a question scoped to "${selectedDocument}"...`
                    : "Ask a question across all indexed PDFs..."
                }
                rows={2}
                disabled={isChatLoading}
                className="w-full bg-transparent text-sm resize-none focus:outline-none p-4 pr-16 text-foreground placeholder:text-muted-foreground/60 min-h-[60px] max-h-[250px]"
              />
              <div className="absolute right-3 bottom-3">
                <Button
                  type="submit"
                  variant="default"
                  size="icon"
                  className="h-8 w-8 rounded bg-primary hover:bg-primary-hover text-primary-foreground shadow-sm"
                  disabled={!input.trim() || isChatLoading}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="flex justify-between items-center mt-3">
              <p className="text-[11px] text-muted-foreground select-none">
                Grounded on vector-similarity retrieval scores.
              </p>
              <p className="text-[11px] text-muted-foreground select-none">
                Press Enter to send, Shift+Enter for new line.
              </p>
            </div>
          </form>
        </div>
      </div>
      
      <StudySheetModal
        isOpen={isStudySheetModalOpen}
        onClose={() => setIsStudySheetModalOpen(false)}
        documentName={selectedDocument}
        content={selectedDocument ? studySheets[selectedDocument] : ""}
        isLoading={isStudySheetLoading}
        onRegenerate={() => {
          if (selectedDocument) generateStudySheet(selectedDocument)
        }}
      />

      {/* Conversation Safety Dialog */}
      {isNewChatDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
          <div className="bg-card w-full max-w-md rounded-lg shadow-lg border border-border overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="p-6">
              <h2 className="text-lg font-semibold text-foreground mb-2">Start a New Chat?</h2>
              <p className="text-sm text-muted-foreground">
                Your current conversation will be permanently deleted and cannot be recovered.
              </p>
            </div>
            <div className="p-4 bg-secondary border-t border-border flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsNewChatDialogOpen(false)}>
                Cancel
              </Button>
              <Button 
                variant="default" 
                className="bg-destructive hover:bg-destructive/90 text-destructive-foreground border-destructive"
                onClick={() => {
                  clearChat()
                  setIsNewChatDialogOpen(false)
                }}
              >
                Start New Chat
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
