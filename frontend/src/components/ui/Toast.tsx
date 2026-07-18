import React, { createContext, useContext, useState, useCallback, ReactNode } from "react"
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react"
import { cn } from "../../lib/utils"

export type ToastType = "success" | "error" | "info"

export interface ToastMessage {
  id: string
  title: string
  description?: string
  type: ToastType
}

interface ToastContextType {
  toast: (options: Omit<ToastMessage, "id">) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

export const useToast = () => {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider")
  }
  return context
}

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const toast = useCallback(({ title, description, type }: Omit<ToastMessage, "id">) => {
    const id = Math.random().toString(36).substring(2, 9)
    setToasts((prev) => [...prev, { id, title, description, type }])
    
    // Auto remove after 4 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }, [])

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-full max-w-sm px-4 md:px-0">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "group pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-md border p-4 pr-8 shadow-sm transition-all data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=move]:transition-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[swipe=end]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-top-full data-[state=open]:sm:slide-in-from-bottom-full",
              t.type === "error" && "border-destructive bg-card text-foreground",
              t.type === "success" && "border-success bg-card text-foreground",
              t.type === "info" && "border-border bg-card text-foreground"
            )}
          >
            <div className="flex items-start gap-3 w-full">
              {t.type === "success" && <CheckCircle2 className="h-5 w-5 text-primary mt-0.5" />}
              {t.type === "error" && <AlertCircle className="h-5 w-5 text-destructive-foreground mt-0.5" />}
              {t.type === "info" && <Info className="h-5 w-5 text-muted-foreground mt-0.5" />}
              
              <div className="flex flex-col gap-1 w-full">
                <h3 className="text-sm font-semibold">{t.title}</h3>
                {t.description && (
                  <p className="text-sm text-muted-foreground opacity-90">
                    {t.description}
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={() => removeToast(t.id)}
              className="absolute right-2 top-2 rounded-md p-1 opacity-0 transition-opacity focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
