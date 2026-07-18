import * as React from "react"
import type { SourceCitation } from "../../types"
import { ChevronDown, ChevronUp, FileText } from "lucide-react"
import { cn } from "../../lib/utils"

export interface SourceCardProps {
  source: SourceCitation
  index: number
  className?: string
}

export const SourceCard: React.FC<SourceCardProps> = ({
  source,
  index,
  className,
}) => {
  const [isOpen, setIsOpen] = React.useState(false)

  return (
    <div
      className={cn(
        "border border-border rounded bg-card overflow-hidden transition-all duration-200",
        isOpen ? "shadow-sm" : "hover:bg-secondary/30",
        className
      )}
    >
      {/* Summary Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3.5 text-left text-sm select-none hover:bg-accent/40 transition-colors"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          <div className="flex items-center gap-2 truncate">
            <span className="font-semibold text-xs text-muted-foreground uppercase tracking-wider">
              [Source {index}]
            </span>
            <span className="font-medium truncate text-card-foreground" title={source.filename}>
              {source.filename}
            </span>
            <span className="text-muted-foreground text-xs whitespace-nowrap">
              (Page {source.page_number})
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0 ml-2">
          <span className="text-xs text-muted-foreground bg-secondary px-2 py-0.5 rounded font-medium border border-border">
            Similarity: {source.similarity_score.toFixed(2)}
          </span>
          {isOpen ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </button>

      {/* Expanded Text Content */}
      {isOpen && (
        <div className="p-4 bg-secondary/30 border-t border-border text-sm leading-relaxed text-foreground/90 font-mono text-xs whitespace-pre-wrap">
          &ldquo;{source.chunk_text}&rdquo;
        </div>
      )}
    </div>
  )
}
