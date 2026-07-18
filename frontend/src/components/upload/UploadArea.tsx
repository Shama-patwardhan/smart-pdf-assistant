import * as React from "react"
import { Upload, CheckCircle2, AlertCircle } from "lucide-react"
import { cn } from "../../lib/utils"
import type { UploadResponse } from "../../types"

export interface UploadAreaProps {
  onUpload: (file: File) => Promise<UploadResponse>
  isUploading: boolean
  className?: string
}

export const UploadArea: React.FC<UploadAreaProps> = ({
  onUpload,
  isUploading,
  className,
}) => {
  const [dragActive, setDragActive] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [success, setSuccess] = React.useState<boolean>(false)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const validateAndUpload = async (file: File) => {
    setError(null)
    setSuccess(false)

    if (file.type !== "application/pdf" && !file.name.endsWith(".pdf")) {
      setError("Only PDF files are supported.")
      return
    }

    const maxSize = 20 * 1024 * 1024 // 20 MB
    if (file.size > maxSize) {
      setError("File exceeds 20 MB size limit.")
      return
    }

    try {
      await onUpload(file)
      setSuccess(true)
      
      // Auto-clear success message after 3 seconds
      setTimeout(() => {
        setSuccess(false)
      }, 3000)
    } catch (err: any) {
      setError(err?.message || "Ingestion pipeline failed.")
    }
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await validateAndUpload(e.dataTransfer.files[0])
    }
  }

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      await validateAndUpload(e.target.files[0])
    }
  }

  const onButtonClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className={cn("w-full", className)}>
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf"
        onChange={handleChange}
        disabled={isUploading}
      />
      
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={onButtonClick}
        className={cn(
          "flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-6 cursor-pointer text-center transition-all duration-200 min-h-[140px]",
          dragActive
            ? "border-primary bg-primary/10"
            : "border-border hover:border-primary/50 hover:bg-card/50",
          isUploading && "pointer-events-none opacity-80 bg-card/50"
        )}
      >
        {isUploading ? (
          <div className="flex flex-col items-center space-y-3 w-full">
            <div className="flex w-full gap-3 flex-col animate-pulse items-center">
              <div className="h-8 w-8 rounded bg-card border border-border flex items-center justify-center" />
              <div className="space-y-2 w-3/4 max-w-[150px]">
                <div className="h-2 bg-border rounded w-full" />
                <div className="h-2 bg-border rounded w-5/6 mx-auto" />
              </div>
            </div>
            <p className="text-xs font-medium text-muted-foreground mt-2">Indexing vectors...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-2 text-muted-foreground">
            <div className="h-10 w-10 rounded-full bg-secondary flex items-center justify-center mb-1">
              <Upload className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div className="text-xs mt-2">
              <span className="font-medium text-foreground">Click to upload</span> or drag & drop
            </div>
            <p className="text-[10px] text-muted-foreground font-medium tracking-wide">PDF (MAX 20 MB)</p>
          </div>
        )}
      </div>

      {/* Subtle, temporary success message */}
      {success && (
        <div className="flex items-center gap-1.5 text-green-500 text-xs mt-2 px-1 animate-in fade-in duration-200">
          <CheckCircle2 className="h-3.5 w-3.5 flex-shrink-0" />
          <span>PDF indexed successfully.</span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-1.5 text-destructive text-xs mt-2 px-1">
          <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
          <span className="truncate">{error}</span>
        </div>
      )}
    </div>
  )
}
