import * as React from "react"
import type { DocumentInfo } from "../../types"
import { Card } from "../ui/Card"
import { Button } from "../ui/Button"
import { FileText, Trash2, Database, HelpCircle } from "lucide-react"
import { cn } from "../../lib/utils"

export interface SidebarProps {
  documents: DocumentInfo[]
  selectedDocument: string | null
  onSelectDocument: (filename: string | null) => void
  onDeleteDocument: (filename: string) => void
  isDeleting: string | null
  uploadAreaNode?: React.ReactNode
  suggestedQuestions?: string[]
  onSelectQuestion?: (question: string) => void
  className?: string
}

export const Sidebar: React.FC<SidebarProps> = ({
  documents,
  selectedDocument,
  onSelectDocument,
  onDeleteDocument,
  isDeleting,
  uploadAreaNode,
  suggestedQuestions = [],
  onSelectQuestion,
  className,
}) => {
  // Always render suggested questions box if a document is selected or if we have questions
  const shouldShowSuggestions = suggestedQuestions.length > 0 || selectedDocument !== null

  return (
    <aside
      className={cn(
        "w-80 flex-shrink-0 border-r bg-secondary p-6 flex flex-col h-full text-foreground",
        className
      )}
    >
      {/* App Logo/Header */}
      <div className="mb-6 flex items-center gap-3 flex-shrink-0">
        <div className="h-8 w-8 rounded flex items-center justify-center bg-primary text-primary-foreground shadow-sm">
          <Database className="h-4 w-4" />
        </div>
        <h1 className="text-base font-semibold tracking-tight text-foreground">Smart PDF Assistant</h1>
      </div>
      
      {/* Upload Area Node Slot */}
      {uploadAreaNode && <div className="mb-4 flex-shrink-0">{uploadAreaNode}</div>}

      <hr className="border-border/60 mb-4 flex-shrink-0" />

      {/* Main split sections: Questions and Documents */}
      <div className="flex-1 flex flex-col min-h-0 space-y-4">
        
        {/* Suggested Questions Section */}
        {shouldShowSuggestions && (
          <div className="flex-1 flex flex-col min-h-[140px] max-h-[40%] border-b border-border/40 pb-4">
            <div className="flex-shrink-0 mb-2">
              <div className="flex items-center gap-2 text-foreground">
                <HelpCircle className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-wider select-none">
                  Suggested Questions
                </span>
              </div>
              <p className="text-[10px] text-muted-foreground/80 mt-0.5 truncate font-medium">
                Scope: {selectedDocument || "All Documents"}
              </p>
            </div>
            
            <div className="flex-1 overflow-y-auto space-y-1.5 pr-2 custom-scrollbar">
              {suggestedQuestions.length > 0 ? (
                suggestedQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => onSelectQuestion?.(q)}
                    className="w-full text-left text-xs bg-background/50 hover:bg-background border border-border/50 text-muted-foreground hover:text-foreground hover:border-border p-2.5 rounded-md transition-all block leading-snug"
                  >
                    {q}
                  </button>
                ))
              ) : (
                /* Small placeholder card if document has no stored questions yet */
                <div className="text-xs text-muted-foreground italic p-3 text-center border border-dashed border-border/60 rounded-md bg-background/30 select-none">
                  No suggestions available for this document.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Indexed Documents Section */}
        <div className="flex-1 flex flex-col min-h-[160px] overflow-hidden">
          <h2 className="text-xs font-semibold text-foreground uppercase tracking-wider mb-3 pl-1 select-none flex-shrink-0">
            Indexed Documents
          </h2>

          {/* Global All Documents Toggle option */}
          <button
            onClick={() => onSelectDocument(null)}
            className={cn(
              "flex items-center gap-3 w-full p-3 rounded-md text-left text-xs transition-colors mb-3 border flex-shrink-0 relative overflow-hidden",
              selectedDocument === null
                ? "bg-card border-border shadow-sm"
                : "bg-transparent hover:bg-card/50 border-transparent hover:border-border/50"
            )}
          >
            {selectedDocument === null && (
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary" />
            )}
            <div className={cn("flex-1 min-w-0", selectedDocument === null ? "pl-1" : "")}>
              <p className="font-semibold truncate text-foreground">All Documents</p>
              <p className="text-[11px] mt-0.5 text-muted-foreground">
                Global search scope
              </p>
            </div>
          </button>

          {/* Independent Scrollable List container */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
            {documents.length === 0 ? (
              <p className="text-xs text-muted-foreground italic text-center py-6 select-none">
                No documents indexed yet.
              </p>
            ) : (
              documents.map((doc) => {
                const isSelected = selectedDocument === doc.filename
                return (
                  <Card
                    key={doc.filename}
                    className={cn(
                      "p-3 cursor-pointer transition-all duration-200 relative group border rounded-md overflow-hidden",
                      isSelected 
                        ? "border-border bg-card shadow-sm" 
                        : "hover:bg-card/50 hover:border-border/50 border-transparent bg-transparent shadow-none"
                    )}
                    onClick={() => onSelectDocument(doc.filename)}
                  >
                    {isSelected && (
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary" />
                    )}
                    <div className={cn("flex items-start gap-2 pr-6", isSelected ? "pl-1" : "")}>
                      <FileText className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-[13px] truncate" title={doc.filename}>
                          {doc.filename}
                        </p>
                        <div className="flex gap-3 text-[11px] text-muted-foreground mt-1">
                          <span>Pages: {doc.page_count}</span>
                          <span>Chunks: {doc.chunk_count}</span>
                        </div>
                      </div>
                    </div>

                    <Button
                      variant="destructive"
                      size="icon"
                      className={cn(
                        "absolute right-2 top-2.5 h-6.5 w-6.5 opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100",
                        isDeleting === doc.filename && "opacity-100"
                      )}
                      isLoading={isDeleting === doc.filename}
                      onClick={(e) => {
                        e.stopPropagation()
                        onDeleteDocument(doc.filename)
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </Card>
                )
              })
            )}
          </div>
        </div>

      </div>
    </aside>
  )
}
