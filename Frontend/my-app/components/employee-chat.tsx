"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Send, Loader2, AlertCircle, CheckCircle, XCircle } from "lucide-react"
import { sendChatMessage, getChatHistory, type ChatResponse } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"
import { Badge } from "@/components/ui/badge"

interface EmployeeChatProps {
  employeeId: string
  sessionId: string
  onSessionChange?: () => void
}

interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
  status?: "SAFE" | "FLAG" | "BLOCKED"
}

export function EmployeeChat({ employeeId, sessionId, onSessionChange }: EmployeeChatProps) {
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load chat history when session changes
  useEffect(() => {
    loadChatHistory()
  }, [sessionId])

  const loadChatHistory = async () => {
    try {
      setIsLoadingHistory(true)
      const history = await getChatHistory(sessionId)
      
      const chatMessages: ChatMessage[] = []
      history.messages.forEach((msg) => {
        // Add user message
        chatMessages.push({
          id: `${msg.id}-user`,
          role: "user",
          content: msg.prompt,
          timestamp: new Date(msg.created_at).toLocaleTimeString([], { 
            hour: "2-digit", 
            minute: "2-digit" 
          }),
          status: msg.status as "SAFE" | "FLAG" | "BLOCKED"
        })
        
        // Add assistant response if exists
        if (msg.response) {
          chatMessages.push({
            id: `${msg.id}-assistant`,
            role: "assistant",
            content: msg.response,
            timestamp: new Date(msg.created_at).toLocaleTimeString([], { 
              hour: "2-digit", 
              minute: "2-digit" 
            }),
            status: msg.status as "SAFE" | "FLAG" | "BLOCKED"
          })
        }
      })
      
      setMessages(chatMessages)
    } catch (error) {
      console.error("Error loading chat history:", error)
      // Start with empty messages if history doesn't exist
      setMessages([])
    } finally {
      setIsLoadingHistory(false)
    }
  }

  const getStatusIcon = (status?: "SAFE" | "FLAG" | "BLOCKED") => {
    if (!status || status === "SAFE") {
      return <CheckCircle className="h-3 w-3 text-green-500" />
    }
    if (status === "FLAG") {
      return <AlertCircle className="h-3 w-3 text-yellow-500" />
    }
    return <XCircle className="h-3 w-3 text-red-500" />
  }

  const getStatusBadge = (status?: "SAFE" | "FLAG" | "BLOCKED") => {
    if (!status || status === "SAFE") return null
    
    return (
      <Badge 
        variant={status === "FLAG" ? "outline" : "destructive"} 
        className="ml-2 text-xs"
      >
        {status}
      </Badge>
    )
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userContent = input.trim()
    const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })

    // Optimistically add user message
    const tempUserMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: userContent,
      timestamp,
    }

    setMessages(prev => [...prev, tempUserMessage])
    setInput("")
    setIsLoading(true)

    try {
      // Send message to backend
      const response = await sendChatMessage({
        employee_id: employeeId,
        message: userContent,
        session_id: sessionId,
        metadata: {
          timestamp,
          source: "employee_chat",
        },
      })

      // Replace temp message with actual message and add assistant response
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== tempUserMessage.id)
        return [
          ...filtered,
          {
            id: `${response.message_id}-user`,
            role: "user",
            content: userContent,
            timestamp,
            status: response.status
          },
          {
            id: `${response.message_id}-assistant`,
            role: "assistant",
            content: response.response,
            timestamp,
            status: response.status
          }
        ]
      })

      // Show notification if message was flagged or blocked
      if (response.status === "BLOCKED") {
        toast({
          title: "Message Blocked",
          description: "Your message was blocked due to security concerns.",
          variant: "destructive",
        })
      } else if (response.status === "FLAG") {
        toast({
          title: "Message Flagged",
          description: "Your message has been flagged for review.",
        })
      }

      // Notify parent of session change
      if (onSessionChange) {
        onSessionChange()
      }
    } catch (error) {
      console.error("Error sending message:", error)
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      })
      // Remove the temp message on error
      setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id))
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoadingHistory) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-muted-foreground" />
          <p className="mt-4 font-mono text-sm text-muted-foreground">Loading conversation...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex h-14 items-center justify-between border-b border-border px-4">
        <div className="font-mono text-sm text-foreground">
          Chat Assistant
        </div>
        <div className="font-mono text-xs text-muted-foreground">
          Session: {sessionId.slice(-8)}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl p-4">
          {messages.length === 0 ? (
            <div className="flex h-full items-center justify-center py-12 text-center">
              <div>
                <p className="font-mono text-sm text-muted-foreground">
                  Start a conversation by sending a message below.
                </p>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`mb-6 rounded-lg border border-border bg-card p-4 ${
                  message.role === "user" ? "ml-8" : "mr-8"
                }`}
              >
                <div className="mb-2 flex items-center gap-2">
                  {getStatusIcon(message.status)}
                  <span className="font-mono text-xs font-semibold uppercase text-foreground">
                    {message.role === "user" ? "YOU" : "AI ASSISTANT"}
                  </span>
                  <span className="font-mono text-xs text-muted-foreground">{message.timestamp}</span>
                  {getStatusBadge(message.status)}
                </div>
                <div className="whitespace-pre-wrap font-mono text-sm text-foreground/90">
                  {message.content}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="border-t border-border bg-background p-4">
        <div className="mx-auto max-w-3xl">
          <div className="relative rounded-lg border border-border bg-card">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
              placeholder="Type your message..."
              className="min-h-[80px] resize-none border-0 bg-transparent font-mono text-sm focus-visible:ring-0"
              disabled={isLoading}
            />
            <div className="flex items-center justify-between border-t border-border p-2">
              <div className="font-mono text-xs text-muted-foreground">
                {isLoading ? "Sending..." : "Shift + Enter for new line"}
              </div>
              <Button size="sm" onClick={handleSend} disabled={!input.trim() || isLoading} className="gap-2">
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
                {isLoading ? "Sending..." : "Send"}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

