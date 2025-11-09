"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { 
  MessageSquare, 
  Plus, 
  AlertTriangle, 
  XCircle, 
  Loader2,
  RefreshCw
} from "lucide-react"
import { getEmployeeSessions } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface Session {
  session_id: string
  message_count: number
  last_message_at: string
  has_flags: boolean
  has_blocks: boolean
}

interface EmployeeSidebarProps {
  employeeId: string
  currentSessionId: string
  onSessionSelect: (sessionId: string) => void
  onNewSession: () => void
}

export function EmployeeSidebar({
  employeeId,
  currentSessionId,
  onSessionSelect,
  onNewSession,
}: EmployeeSidebarProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    loadSessions()
  }, [employeeId])

  const loadSessions = async (showToast = false) => {
    try {
      setIsRefreshing(true)
      const data = await getEmployeeSessions(employeeId)
      setSessions(data)
      
      if (showToast) {
        toast({
          title: "Refreshed",
          description: `Loaded ${data.length} conversations`,
        })
      }
    } catch (error) {
      console.error("Error loading sessions:", error)
      if (showToast) {
        toast({
          title: "Error",
          description: "Failed to load conversations",
          variant: "destructive",
        })
      }
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    
    if (hours < 1) {
      const minutes = Math.floor(diff / (1000 * 60))
      return `${minutes}m ago`
    }
    if (hours < 24) {
      return `${hours}h ago`
    }
    const days = Math.floor(hours / 24)
    if (days === 1) return "Yesterday"
    if (days < 7) return `${days}d ago`
    
    return date.toLocaleDateString([], { month: "short", day: "numeric" })
  }

  if (isLoading) {
    return (
      <div className="flex h-full w-64 flex-col border-r border-border bg-background">
        <div className="flex h-14 items-center justify-center border-b border-border">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full w-64 flex-col border-r border-border bg-background">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-border p-3">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="font-mono text-sm font-semibold text-foreground">
            Conversations
          </h2>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => loadSessions(true)}
            disabled={isRefreshing}
            className="h-7 w-7 p-0"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
          </Button>
        </div>
        <Button
          size="sm"
          onClick={onNewSession}
          className="w-full gap-2 font-mono text-xs"
        >
          <Plus className="h-3.5 w-3.5" />
          New Chat
        </Button>
      </div>

      {/* Sessions List */}
      <ScrollArea className="flex-1">
        <div className="space-y-1 p-2">
          {sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <MessageSquare className="h-12 w-12 text-muted-foreground/30" />
              <p className="mt-4 font-mono text-xs text-muted-foreground">
                No conversations yet
              </p>
              <p className="font-mono text-xs text-muted-foreground/70">
                Start a new chat above
              </p>
            </div>
          ) : (
            sessions.map((session) => (
              <button
                key={session.session_id}
                onClick={() => onSessionSelect(session.session_id)}
                className={`w-full rounded-lg border p-3 text-left transition-colors ${
                  session.session_id === currentSessionId
                    ? "border-primary bg-accent"
                    : "border-border bg-card hover:bg-accent/50"
                }`}
              >
                <div className="mb-2 flex items-start justify-between gap-2">
                  <div className="flex items-center gap-1.5">
                    <MessageSquare className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="font-mono text-xs font-medium text-foreground">
                      Session
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    {session.has_blocks && (
                      <XCircle className="h-3 w-3 text-red-500" />
                    )}
                    {session.has_flags && (
                      <AlertTriangle className="h-3 w-3 text-yellow-500" />
                    )}
                  </div>
                </div>
                
                <div className="mb-1.5 font-mono text-xs text-muted-foreground">
                  ID: {session.session_id.slice(-8)}
                </div>
                
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="font-mono text-xs">
                    {session.message_count} msgs
                  </Badge>
                  <span className="font-mono text-xs text-muted-foreground">
                    {formatDate(session.last_message_at)}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="flex-shrink-0 border-t border-border p-3">
        <div className="rounded-lg border border-border bg-card p-2">
          <div className="font-mono text-xs text-muted-foreground">
            Employee: {employeeId}
          </div>
          <div className="mt-1 font-mono text-xs font-semibold text-foreground">
            {sessions.length} {sessions.length === 1 ? "conversation" : "conversations"}
          </div>
        </div>
      </div>
    </div>
  )
}

