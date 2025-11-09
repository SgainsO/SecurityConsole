"use client"
import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { AlertTriangle, CheckCircle, XCircle, Eye, Loader2, RefreshCw } from "lucide-react"
import { getFlaggedMessages, setMessageStatus, type Message } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"
import { formatRelativeTime } from "@/lib/date-utils"

export function ReviewPanel() {
  const [flaggedMessages, setFlaggedMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const { toast } = useToast()

  const loadFlaggedMessages = async (showRefreshToast = false) => {
    try {
      setIsRefreshing(true)
      const messages = await getFlaggedMessages()
      setFlaggedMessages(messages)
      
      if (showRefreshToast) {
        toast({
          title: "Refreshed",
          description: `Loaded ${messages.length} flagged messages`,
        })
      }
    } catch (error) {
      console.error("Error loading flagged messages:", error)
      toast({
        title: "Error",
        description: "Failed to load flagged messages",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    loadFlaggedMessages()
    
    // Auto-refresh every 10 seconds
    const interval = setInterval(() => {
      loadFlaggedMessages()
    }, 10000)

    return () => clearInterval(interval)
  }, [])

  const handleClearFlag = async (messageId: string) => {
    try {
      await setMessageStatus(messageId, "SAFE")
      setFlaggedMessages((prev) => prev.filter((m) => m.id !== messageId))
      
      toast({
        title: "Message Cleared",
        description: "Message has been marked as safe",
      })
    } catch (error) {
      console.error("Error clearing flag:", error)
      toast({
        title: "Error",
        description: "Failed to clear flag",
        variant: "destructive",
      })
    }
  }

  const handleBlock = async (messageId: string) => {
    try {
      await setMessageStatus(messageId, "BLOCKED")
      setFlaggedMessages((prev) => prev.filter((m) => m.id !== messageId))
      
      toast({
        title: "Message Blocked",
        description: "Message has been blocked",
        variant: "destructive",
      })
    } catch (error) {
      console.error("Error blocking message:", error)
      toast({
        title: "Error",
        description: "Failed to block message",
        variant: "destructive",
      })
    }
  }
  if (isLoading) {
    return (
      <div className="flex h-screen w-[40%] flex-col items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <p className="mt-4 font-mono text-sm text-muted-foreground">Loading flagged messages...</p>
      </div>
    )
  }

  return (
    <div className="flex h-screen w-[40%] flex-col bg-background">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-border p-6">
        <div className="mb-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            <h2 className="font-mono text-lg font-semibold text-foreground">FLAGGED MESSAGES</h2>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => loadFlaggedMessages(true)}
            disabled={isRefreshing}
            className="gap-2"
          >
            <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
            Refresh
          </Button>
        </div>
        <p className="font-mono text-xs text-muted-foreground">{flaggedMessages.length} messages requiring review</p>
      </div>

      <ScrollArea className="flex-1 overflow-auto">
        <div className="space-y-3 p-6">
          {flaggedMessages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <CheckCircle className="h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 font-mono text-sm text-muted-foreground">No flagged messages</p>
              <p className="font-mono text-xs text-muted-foreground">All clear!</p>
            </div>
          ) : (
            flaggedMessages.map((message) => (
              <Card key={message.id} className="border-border bg-card p-4">
                <div className="space-y-3">
                  {/* Top row: badge, employee info, timestamp */}
                  <div className="flex items-center gap-3">
                    <Badge variant="destructive" className="font-mono text-xs uppercase">
                      FLAG
                    </Badge>

                    <div className="font-mono text-xs text-muted-foreground">ID: {message.employee_id}</div>

                    <div className="ml-auto font-mono text-xs text-muted-foreground">
                      {formatRelativeTime(message.created_at)}
                    </div>
                  </div>

                  {/* Message content */}
                  <p className="font-mono text-sm leading-relaxed text-foreground/80">{message.prompt}</p>

                  {/* Response if available */}
                  {message.response && (
                    <div className="rounded border border-border bg-muted/50 p-2">
                      <p className="font-mono text-xs text-muted-foreground">
                        <span className="font-semibold text-foreground">RESPONSE:</span> {message.response}
                      </p>
                    </div>
                  )}

                  {/* Metadata */}
                  {message.metadata && (
                    <div className="rounded border border-border bg-muted/50 p-2">
                      <p className="font-mono text-xs text-muted-foreground">
                        <span className="font-semibold text-foreground">SESSION:</span> {message.session_id}
                      </p>
                    </div>
                  )}

                  {/* Action buttons */}
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="default"
                      className="gap-1.5 font-mono text-xs"
                      onClick={() => handleClearFlag(message.id)}
                    >
                      <CheckCircle className="h-3.5 w-3.5" />
                      Clear
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      className="gap-1.5 font-mono text-xs bg-red-600 hover:bg-red-700 text-white"
                      onClick={() => handleBlock(message.id)}
                    >
                      <XCircle className="h-3.5 w-3.5" />
                      Block
                    </Button>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Footer stats */}
      <div className="flex-shrink-0 border-t border-border p-6">
        <div className="rounded-lg border border-border bg-card p-3">
          <div className="space-y-2 font-mono text-xs">
            <div className="flex items-center justify-between border-t border-border pt-2">
              <span className="text-muted-foreground">TOTAL FLAGGED</span>
              <span className="font-semibold text-foreground">{flaggedMessages.length}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ")
}
