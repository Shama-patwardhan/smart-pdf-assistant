import * as React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import remarkMath from "remark-math"
import rehypeKatex from "rehype-katex"
import "katex/dist/katex.min.css"
import { X, RefreshCw, FileText, Copy, Check } from "lucide-react"
import { Button } from "../ui/Button"

interface StudySheetModalProps {
  isOpen: boolean
  onClose: () => void
  documentName: string | null
  content: string
  isLoading: boolean
  onRegenerate: () => void
}

export const StudySheetModal: React.FC<StudySheetModalProps> = ({
  isOpen,
  onClose,
  documentName,
  content,
  isLoading,
  onRegenerate
}) => {
  const [copyStatus, setCopyStatus] = React.useState<"idle" | "copied" | "error">("idle")

  const handleCopy = async () => {
    if (!content) return
    try {
      await navigator.clipboard.writeText(content)
      setCopyStatus("copied")
      setTimeout(() => setCopyStatus("idle"), 2000)
    } catch (err) {
      console.error("Failed to copy text: ", err)
      setCopyStatus("error")
      setTimeout(() => setCopyStatus("idle"), 2000)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 md:p-12 bg-background/80 backdrop-blur-sm">
      <div className="bg-card w-full max-w-5xl h-full sm:max-h-full rounded-lg shadow-xl flex flex-col border border-border overflow-hidden animate-in fade-in zoom-in-95 duration-300">
        
        {/* Header */}
        <div className="h-16 px-6 border-b border-border flex items-center justify-between bg-secondary flex-shrink-0">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="h-10 w-10 rounded bg-card border border-border flex items-center justify-center text-primary flex-shrink-0">
              <FileText className="h-5 w-5" />
            </div>
            <div className="flex flex-col min-w-0">
              <h2 className="font-semibold text-foreground truncate tracking-tight">Study Sheet</h2>
              <span className="text-xs text-muted-foreground truncate opacity-80">{documentName || "Unknown Document"}</span>
            </div>
          </div>
          
          <div className="flex items-center gap-2 flex-shrink-0">
            {content && !isLoading && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopy}
                  className="hidden sm:flex min-w-[90px]"
                >
                  {copyStatus === "copied" ? (
                    <><Check className="h-4 w-4 mr-2 text-green-500" /> Copied</>
                  ) : copyStatus === "error" ? (
                    <><X className="h-4 w-4 mr-2 text-red-500" /> Error</>
                  ) : (
                    <><Copy className="h-4 w-4 mr-2" /> Copy</>
                  )}
                </Button>
                {/* Mobile copy button */}
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleCopy}
                  className="sm:hidden h-9 w-9"
                >
                  {copyStatus === "copied" ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : copyStatus === "error" ? (
                    <X className="h-4 w-4 text-red-500" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={onRegenerate}
              disabled={isLoading}
              className="hidden sm:flex"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Regenerate
            </Button>
            {/* Mobile regenerate button */}
            <Button
              variant="outline"
              size="icon"
              onClick={onRegenerate}
              disabled={isLoading}
              className="sm:hidden h-9 w-9"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
            
            <Button variant="ghost" size="icon" onClick={onClose} className="h-9 w-9 text-muted-foreground hover:text-foreground">
              <X className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* Content area */}
        <div className="flex-1 overflow-y-auto p-6 md:p-12 bg-background custom-scrollbar">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center h-full space-y-8 animate-in fade-in duration-500">
              <RefreshCw className="h-8 w-8 animate-spin text-primary" />
              <div className="text-center space-y-2">
                <p className="text-xl font-semibold text-foreground tracking-tight">Synthesizing Study Sheet...</p>
                <p className="text-sm max-w-md mx-auto text-muted-foreground">
                  Analyzing document structure and extracting key formulas, concepts, and workflows into a comprehensive guide.
                </p>
              </div>
              
              {/* Premium Skeleton Block */}
              <div className="w-full max-w-3xl mx-auto space-y-4 mt-8 opacity-60">
                <div className="flex gap-4 items-end mb-8">
                  <div className="h-10 bg-secondary rounded w-1/3 animate-pulse" />
                  <div className="h-4 bg-secondary rounded w-24 animate-pulse" />
                </div>
                {[1, 2, 3].map(i => (
                  <div key={i} className="space-y-3 pt-4">
                    <div className="h-6 bg-secondary rounded w-1/4 animate-pulse" />
                    <div className="h-4 bg-secondary rounded w-full animate-pulse" />
                    <div className="h-4 bg-secondary rounded w-11/12 animate-pulse" />
                    <div className="h-4 bg-secondary rounded w-4/5 animate-pulse" />
                  </div>
                ))}
              </div>
            </div>
          ) : !content ? (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-6 animate-in fade-in zoom-in-95 duration-500">
              <div className="h-16 w-16 rounded border border-border bg-card flex items-center justify-center text-muted-foreground shadow-sm">
                <FileText className="h-8 w-8 opacity-40" />
              </div>
              <div className="space-y-1">
                <h3 className="text-lg font-semibold text-foreground">No Study Sheet Available</h3>
                <p className="text-sm text-muted-foreground max-w-sm">Generate a comprehensive markdown summary covering all critical concepts.</p>
              </div>
              <Button onClick={onRegenerate} size="default" className="mt-4 shadow-sm bg-primary hover:bg-primary-hover transition-colors">
                Generate Now
              </Button>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto markdown-body animate-in fade-in duration-500">
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
              >
                {content}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
