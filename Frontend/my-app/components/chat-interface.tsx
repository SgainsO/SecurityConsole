"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Send, Loader2 } from "lucide-react"
import { createMessage, setMessageStatus } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

const EMPLOYEE_ID = "emp_test_001" // Test employee ID
const SESSION_ID = `session_${Date.now()}` // Unique session ID

export function ChatInterface() {
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<Array<{
    id: string
    role: "user" | "assistant"
    content: string
    timestamp: string
  }>>([])
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userContent = input.trim()
    const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })

    const newMessage = {
      id: String(messages.length + 1),
      role: "user" as const,
      content: userContent,
      timestamp,
    }

    setMessages([...messages, newMessage])
    setInput("")
    setIsLoading(true)

    try {
      // Create message in backend
      const createdMessage = await createMessage({
        user_id: EMPLOYEE_ID,
        prompt: userContent,
        session_id: SESSION_ID,
        metadata: {
          timestamp,
          source: "employee_chat",
        },
      })

      // Immediately flag it for testing purposes
      await setMessageStatus(createdMessage.id, "FLAG")

      toast({
        title: "Message Sent & Flagged",
        description: "Message has been sent and flagged for testing purposes",
      })
    } catch (error) {
      console.error("Error sending message:", error)
      toast({
        title: "Error",
        description: "Failed to send message to backend",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex w-[60%] flex-col border-r border-border">
      {/* Header */}
      <div className="flex h-14 items-center border-b border-border px-4">
        <div className="font-mono text-sm text-foreground">Employee Chat Monitor</div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl p-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`mb-6 rounded-lg border border-border bg-card p-4 ${message.role === "user" ? "ml-8" : "mr-8"}`}
            >
              <div className="mb-2 flex items-center gap-2">
                <span className="font-mono text-xs font-semibold uppercase text-foreground">
                  {message.role === "user" ? "EMPLOYEE" : "AI ASSISTANT"}
                </span>
                <span className="font-mono text-xs text-muted-foreground">{message.timestamp}</span>
              </div>
              <div className="whitespace-pre-wrap font-mono text-sm text-foreground/90">{message.content}</div>
            </div>
          ))}
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
              placeholder="Monitoring employee messages..."
              className="min-h-[80px] resize-none border-0 bg-transparent font-mono text-sm focus-visible:ring-0"
            />
            <div className="flex items-center justify-between border-t border-border p-2">
              <div className="font-mono text-xs text-muted-foreground">
                {isLoading ? "Sending to backend..." : "Shift + Enter for new line"}
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
