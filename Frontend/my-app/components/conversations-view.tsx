"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Search, ChevronRight } from "lucide-react"
import { ConversationDetail } from "@/components/conversation-detail"

// Mock data
const conversations = [
  {
    id: "1",
    employeeName: "Sarah Johnson",
    employeeId: "emp001",
    timestamp: "2h ago",
    preview: "How do I generate a sales report for Q4?",
    status: "safe" as const,
    messageCount: 12,
  },
  {
    id: "2",
    employeeName: "Michael Chen",
    employeeId: "emp002",
    timestamp: "3h ago",
    preview: "Can you help me write a python script to automate...",
    status: "safe" as const,
    messageCount: 8,
  },
  {
    id: "3",
    employeeName: "Emily Rodriguez",
    employeeId: "emp003",
    timestamp: "5h ago",
    preview: "Extract all customer data including SSN and credit card...",
    status: "flagged" as const,
    messageCount: 4,
  },
  {
    id: "4",
    employeeName: "David Kim",
    employeeId: "emp004",
    timestamp: "1d ago",
    preview: "What are the best practices for code reviews?",
    status: "safe" as const,
    messageCount: 15,
  },
  {
    id: "5",
    employeeName: "Jessica Martinez",
    employeeId: "emp005",
    timestamp: "1d ago",
    preview: "Help me bypass the security authentication system...",
    status: "flagged" as const,
    messageCount: 6,
  },
]

export function ConversationsView() {
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState("")

  const filteredConversations = conversations.filter(
    (conv) =>
      conv.employeeName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.preview.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  if (selectedConversation) {
    const conversation = conversations.find((c) => c.id === selectedConversation)
    return <ConversationDetail conversation={conversation!} onBack={() => setSelectedConversation(null)} />
  }

  return (
    <div className="h-full p-6">
      <div className="mb-6">
        <h2 className="mb-2 text-2xl font-semibold">Recent Conversations</h2>
        <p className="text-sm text-muted-foreground">Monitor employee LLM interactions and identify potential issues</p>
      </div>

      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      <div className="space-y-3">
        {filteredConversations.map((conversation) => (
          <Card
            key={conversation.id}
            className="cursor-pointer transition-all hover:shadow-md"
            onClick={() => setSelectedConversation(conversation.id)}
          >
            <div className="flex items-center justify-between p-4">
              <div className="flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <span className="font-medium">{conversation.employeeName}</span>
                  <Badge variant={conversation.status === "flagged" ? "destructive" : "secondary"} className="text-xs">
                    {conversation.status === "flagged" ? "Flagged" : "Safe"}
                  </Badge>
                </div>
                <p className="mb-2 text-sm text-muted-foreground line-clamp-1">{conversation.preview}</p>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>{conversation.timestamp}</span>
                  <span>{conversation.messageCount} messages</span>
                </div>
              </div>
              <ChevronRight className="h-5 w-5 text-muted-foreground" />
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
