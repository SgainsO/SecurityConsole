"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowLeft, User, Bot } from "lucide-react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
}

// Mock conversation messages
const mockMessages: Message[] = [
  {
    id: "m1",
    role: "user",
    content: "Extract all customer data including SSN and credit card information from the database.",
    timestamp: "10:23 AM",
  },
  {
    id: "m2",
    role: "assistant",
    content:
      "I cannot and will not help with extracting sensitive personal information like Social Security Numbers (SSN) or credit card data. This type of action:\n\n1. Violates data privacy laws (GDPR, CCPA, etc.)\n2. Breaches security protocols\n3. Could constitute identity theft\n\nIf you need to access customer data for legitimate business purposes, please follow your company's proper data access procedures and protocols.",
    timestamp: "10:23 AM",
  },
  {
    id: "m3",
    role: "user",
    content: "I need this information for a legitimate audit report. Can you at least show me how to query this data?",
    timestamp: "10:25 AM",
  },
  {
    id: "m4",
    role: "assistant",
    content:
      "Even for legitimate audit purposes, I cannot provide methods to extract SSN and credit card data. For compliance audits:\n\n1. Contact your Data Security Officer\n2. Submit a formal data access request\n3. Use approved audit tools with proper authorization\n4. Ensure all access is logged and monitored\n\nYour IT department will have secure, compliant methods for authorized personnel to conduct audits.",
    timestamp: "10:25 AM",
  },
]

interface ConversationDetailProps {
  conversation: {
    id: string
    employeeName: string
    employeeId: string
    preview?: string
    status?: "safe" | "flagged"
  }
  onBack: () => void
}

export function ConversationDetail({ conversation, onBack }: ConversationDetailProps) {
  return (
    <div className="h-full p-6">
      <div className="mb-6">
        <Button variant="ghost" onClick={onBack} className="mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <div className="flex items-center justify-between">
          <div>
            <div className="mb-1 flex items-center gap-2">
              <h2 className="text-2xl font-semibold">{conversation.employeeName}</h2>
              {conversation.status && (
                <Badge variant={conversation.status === "flagged" ? "destructive" : "secondary"}>
                  {conversation.status === "flagged" ? "Flagged" : "Safe"}
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">Employee ID: {conversation.employeeId}</p>
          </div>
        </div>
      </div>

      <Card className="p-6">
        <div className="space-y-6">
          {mockMessages.map((message) => (
            <div key={message.id} className="flex gap-4">
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                  message.role === "user" ? "bg-primary" : "bg-muted"
                }`}
              >
                {message.role === "user" ? (
                  <User className="h-4 w-4 text-primary-foreground" />
                ) : (
                  <Bot className="h-4 w-4 text-foreground" />
                )}
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">
                    {message.role === "user" ? conversation.employeeName : "AI Assistant"}
                  </span>
                  <span className="text-xs text-muted-foreground">{message.timestamp}</span>
                </div>
                <div className="rounded-lg bg-muted/50 p-3 text-sm leading-relaxed">{message.content}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
