"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  ArrowLeft, 
  User, 
  Bot, 
  Loader2,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Shield
} from "lucide-react"
import { getConversationDetail, setMessageStatus, type ConversationDetail as ConversationDetailType } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"
import { formatFullDate, formatTime } from "@/lib/date-utils"

interface ConversationDetailProps {
  sessionId: string
  onBack: () => void
  onUpdate?: () => void
}

export function ConversationDetail({ sessionId, onBack, onUpdate }: ConversationDetailProps) {
  const [conversation, setConversation] = useState<ConversationDetailType | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [actioningMessageId, setActioningMessageId] = useState<string | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    loadConversation()
  }, [sessionId])

  const loadConversation = async () => {
    try {
      setIsLoading(true)
      const data = await getConversationDetail(sessionId)
      setConversation(data)
    } catch (error) {
      console.error("Error loading conversation:", error)
      toast({
        title: "Error",
        description: "Failed to load conversation details",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleMessageAction = async (messageId: string, status: "SAFE" | "BLOCKED") => {
    try {
      setActioningMessageId(messageId)
      await setMessageStatus(messageId, status)
      
      // Reload conversation to get updated data
      await loadConversation()
      
      toast({
        title: status === "SAFE" ? "Message Cleared" : "Message Blocked",
        description: `Message has been marked as ${status.toLowerCase()}`,
      })

      if (onUpdate) {
        onUpdate()
      }
    } catch (error) {
      console.error("Error updating message status:", error)
      toast({
        title: "Error",
        description: "Failed to update message status",
        variant: "destructive",
      })
    } finally {
      setActioningMessageId(null)
    }
  }

  const getStatusIcon = (status: string) => {
    if (status === "SAFE") return <CheckCircle className="h-3.5 w-3.5 text-green-500" />
    if (status === "FLAG") return <AlertTriangle className="h-3.5 w-3.5 text-yellow-500" />
    return <XCircle className="h-3.5 w-3.5 text-red-500" />
  }


  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-muted-foreground" />
          <p className="mt-4 font-mono text-sm text-muted-foreground">Loading conversation...</p>
        </div>
      </div>
    )
  }

  if (!conversation) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="font-mono text-sm text-muted-foreground">Conversation not found</p>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-border p-6">
        <Button variant="ghost" onClick={onBack} className="mb-4 gap-2 font-mono text-sm">
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        
        <div className="flex items-start justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <h2 className="font-mono text-2xl font-bold text-foreground">
                Conversation Details
              </h2>
            </div>
            <div className="space-y-1">
              <p className="font-mono text-sm text-muted-foreground">
                Employee: <span className="font-semibold text-foreground">{conversation.employee_id}</span>
              </p>
              <p className="font-mono text-sm text-muted-foreground">
                Session: <span className="font-semibold text-foreground">{sessionId.slice(-8)}</span>
              </p>
              <p className="font-mono text-xs text-muted-foreground">
                {formatFullDate(conversation.statistics.first_message_at)} - {formatTime(conversation.statistics.first_message_at)}
              </p>
            </div>
          </div>

          {/* Statistics */}
          <Card className="border-border p-4">
            <div className="space-y-2 font-mono text-xs">
              <div className="flex items-center justify-between gap-8">
                <span className="text-muted-foreground">Total Messages:</span>
                <span className="font-semibold text-foreground">{conversation.statistics.total_messages}</span>
              </div>
              <div className="flex items-center justify-between gap-8">
                <span className="text-green-600">Safe:</span>
                <span className="font-semibold text-green-600">{conversation.statistics.safe_messages}</span>
              </div>
              <div className="flex items-center justify-between gap-8">
                <span className="text-yellow-600">Flagged:</span>
                <span className="font-semibold text-yellow-600">{conversation.statistics.flagged_messages}</span>
              </div>
              <div className="flex items-center justify-between gap-8">
                <span className="text-red-600">Blocked:</span>
                <span className="font-semibold text-red-600">{conversation.statistics.blocked_messages}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1">
        <div className="space-y-6 p-6">
          {conversation.messages.map((message, index) => {
            const isUserMessage = index % 2 === 0 // Alternating user/assistant pattern
            
            return (
              <div key={message.id}>
                {/* User Prompt */}
                <Card className="border-border p-4">
                  <div className="mb-3 flex items-start gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary">
                      <User className="h-4 w-4 text-primary-foreground" />
                    </div>
                    <div className="flex-1">
                      <div className="mb-2 flex items-center gap-2">
                        <span className="font-mono text-sm font-semibold text-foreground">
                          {conversation.employee_id}
                        </span>
                        <span className="font-mono text-xs text-muted-foreground">
                          {formatTime(message.created_at)}
                        </span>
                        {getStatusIcon(message.status)}
                        <Badge 
                          variant={
                            message.status === "SAFE" ? "outline" : 
                            message.status === "FLAG" ? "outline" : 
                            "destructive"
                          }
                          className="font-mono text-xs"
                        >
                          {message.status}
                        </Badge>
                      </div>
                      <div className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-foreground/90">
                        {message.prompt}
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons for Flagged Messages */}
                  {message.status === "FLAG" && (
                    <div className="mt-3 flex gap-2 border-t border-border pt-3">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleMessageAction(message.id, "SAFE")}
                        disabled={actioningMessageId === message.id}
                        className="gap-2 font-mono text-xs"
                      >
                        {actioningMessageId === message.id ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <CheckCircle className="h-3.5 w-3.5" />
                        )}
                        Mark Safe
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleMessageAction(message.id, "BLOCKED")}
                        disabled={actioningMessageId === message.id}
                        className="gap-2 font-mono text-xs bg-red-600 hover:bg-red-700 text-white"
                      >
                        {actioningMessageId === message.id ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <XCircle className="h-3.5 w-3.5" />
                        )}
                        Block
                      </Button>
                    </div>
                  )}
                </Card>

                {/* Assistant Response */}
                {message.response && (
                  <Card className="ml-12 mt-3 border-border bg-muted/30 p-4">
                    <div className="flex items-start gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                        <Bot className="h-4 w-4 text-foreground" />
                      </div>
                      <div className="flex-1">
                        <div className="mb-2 flex items-center gap-2">
                          <span className="font-mono text-sm font-semibold text-foreground">
                            AI Assistant
                          </span>
                          <span className="font-mono text-xs text-muted-foreground">
                            {formatTime(message.created_at)}
                          </span>
                        </div>
                        <div className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-foreground/90">
                          {message.response}
                        </div>
                      </div>
                    </div>
                  </Card>
                )}
              </div>
            )
          })}
        </div>
      </ScrollArea>
    </div>
  )
}
