import * as React from "react"
import type { Message } from "../../types"
import { SourceCard } from "./SourceCard"
import { ShieldCheck, AlertTriangle, ShieldAlert, Bot, User, ChevronDown } from "lucide-react"
import { cn } from "../../lib/utils"
import ReactMarkdown from "react-markdown"

export interface ChatMessageProps {
  message: Message
  className?: string
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  className,
}) => {
  const isUser = message.role === "user"

  // Compute confidence level classifications
  const getConfidenceInfo = (score?: number) => {
    if (score === undefined) return null
    if (score >= 0.7) {
      return {
        label: `High (${(score * 100).toFixed(1)}%)`,
        color: "text-emerald-800 bg-emerald-500/10 border-emerald-500/20",
        icon: <ShieldCheck className="h-4 w-4" />,
      }
    } else if (score >= 0.4) {
      return {
        label: `Moderate (${(score * 100).toFixed(1)}%)`,
        color: "text-amber-800 bg-amber-500/10 border-amber-500/20",
        icon: <AlertTriangle className="h-4 w-4" />,
      }
    } else {
      return {
        label: `Low / Groundless (${(score * 100).toFixed(1)}%)`,
        color: "text-rose-900 bg-rose-500/10 border-rose-500/20",
        icon: <ShieldAlert className="h-4 w-4" />,
      }
    }
  }

  const confidenceInfo = getConfidenceInfo(message.confidence)

  return (
    <div
      className={cn(
        "flex w-full gap-4 py-8 border-b border-border/20",
        isUser ? "flex-row-reverse" : "flex-row",
        className
      )}
    >
      {/* Avatar Node */}
      <div
        className={cn(
          "h-9 w-9 rounded flex items-center justify-center text-sm font-medium select-none flex-shrink-0 border",
          isUser
            ? "bg-primary text-primary-foreground border-primary"
            : "bg-card text-primary border-border"
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4 text-primary" />}
      </div>

      {/* Main Message Column */}
      <div className={cn("flex flex-col max-w-[78%] min-w-0 flex-1", isUser && "items-end")}>
        {/* Timestamp */}
        <span className="text-[10px] text-muted-foreground mb-1 select-none">
          {message.timestamp}
        </span>

        {/* Message Bubble Card */}
        <div
          className={cn(
            "rounded-md p-5 text-base leading-relaxed break-words w-full",
            isUser
              ? "bg-transparent text-foreground"
              : "bg-card text-foreground border border-border shadow-sm"
          )}
        >
          <div className="markdown-body">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>

          {!isUser && confidenceInfo && (
            <div className="mt-4 pt-4 border-t border-border flex flex-col gap-2">
              <div
                className={cn(
                  "inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium w-fit border",
                  confidenceInfo.color
                )}
              >
                {confidenceInfo.icon}
                <span>Confidence: {confidenceInfo.label}</span>
              </div>
            </div>
          )}
        </div>

        {/* Collapsible assistant citations / sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <details className="w-full mt-6 group">
            <summary className="list-none flex items-center gap-1.5 cursor-pointer text-xs font-semibold text-muted-foreground uppercase tracking-wider pl-1 select-none hover:text-foreground transition-colors duration-150 outline-none">
              <span>View Sources ({message.sources.length})</span>
              <span className="transition-transform duration-200 group-open:rotate-180">
                <ChevronDown className="h-3.5 w-3.5" />
              </span>
            </summary>
            <div className="space-y-2 mt-3 animate-in fade-in slide-in-from-top-1 duration-200">
              {message.sources.map((src, idx) => (
                <SourceCard key={idx} source={src} index={idx + 1} />
              ))}
            </div>
          </details>
        )}
      </div>
    </div>
  )
}
