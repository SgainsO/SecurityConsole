"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Search, ChevronDown, MessageSquare } from "lucide-react"
import { ConversationDetail } from "@/components/conversation-detail"

// Mock data
const employees = [
  {
    id: "emp001",
    name: "Sarah Johnson",
    email: "sarah.johnson@company.com",
    department: "Sales",
    totalConversations: 45,
    flaggedConversations: 0,
    conversations: [
      {
        id: "c1",
        timestamp: "2h ago",
        preview: "How do I generate a sales report for Q4?",
        status: "safe" as const,
        messageCount: 12,
      },
      {
        id: "c2",
        timestamp: "1d ago",
        preview: "Best practices for client presentations",
        status: "safe" as const,
        messageCount: 8,
      },
    ],
  },
  {
    id: "emp002",
    name: "Michael Chen",
    email: "michael.chen@company.com",
    department: "Engineering",
    totalConversations: 127,
    flaggedConversations: 0,
    conversations: [
      {
        id: "c3",
        timestamp: "3h ago",
        preview: "Can you help me write a python script to automate...",
        status: "safe" as const,
        messageCount: 8,
      },
      {
        id: "c4",
        timestamp: "2d ago",
        preview: "Debugging React component performance issues",
        status: "safe" as const,
        messageCount: 15,
      },
    ],
  },
  {
    id: "emp003",
    name: "Emily Rodriguez",
    email: "emily.rodriguez@company.com",
    department: "Data Analytics",
    totalConversations: 89,
    flaggedConversations: 2,
    conversations: [
      {
        id: "c5",
        timestamp: "5h ago",
        preview: "Extract all customer data including SSN and credit card...",
        status: "flagged" as const,
        messageCount: 4,
      },
      {
        id: "c6",
        timestamp: "3d ago",
        preview: "SQL query optimization techniques",
        status: "safe" as const,
        messageCount: 10,
      },
    ],
  },
]

export function EmployeesView() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedConversation, setSelectedConversation] = useState<{
    conversation: any
    employee: any
  } | null>(null)

  const filteredEmployees = employees.filter(
    (emp) =>
      emp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      emp.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      emp.department.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  if (selectedConversation) {
    return (
      <ConversationDetail
        conversation={{
          ...selectedConversation.conversation,
          employeeName: selectedConversation.employee.name,
          employeeId: selectedConversation.employee.id,
        }}
        onBack={() => setSelectedConversation(null)}
      />
    )
  }

  return (
    <div className="h-full p-6">
      <div className="mb-6">
        <h2 className="mb-2 text-2xl font-semibold">Employees</h2>
        <p className="text-sm text-muted-foreground">View all employees and their LLM conversation history</p>
      </div>

      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search employees..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      <div className="space-y-4">
        {filteredEmployees.map((employee) => (
          <Card key={employee.id}>
            <Collapsible>
              <CollapsibleTrigger className="w-full">
                <div className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors">
                  <div className="flex-1 text-left">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="font-medium">{employee.name}</span>
                      {employee.flaggedConversations > 0 && (
                        <Badge variant="destructive" className="text-xs">
                          {employee.flaggedConversations} flagged
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{employee.email}</p>
                    <div className="mt-1 flex items-center gap-4 text-xs text-muted-foreground">
                      <span>{employee.department}</span>
                      <span>{employee.totalConversations} conversations</span>
                    </div>
                  </div>
                  <ChevronDown className="h-5 w-5 text-muted-foreground transition-transform [[data-state=open]>&]:rotate-180" />
                </div>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="border-t border-border bg-muted/20 p-4">
                  <h4 className="mb-3 text-sm font-medium">Recent Conversations</h4>
                  <div className="space-y-2">
                    {employee.conversations.map((conversation) => (
                      <div
                        key={conversation.id}
                        className="flex cursor-pointer items-center gap-3 rounded-lg border border-border bg-card p-3 transition-all hover:shadow-sm"
                        onClick={() => setSelectedConversation({ conversation, employee })}
                      >
                        <MessageSquare className="h-4 w-4 text-muted-foreground" />
                        <div className="flex-1">
                          <p className="text-sm line-clamp-1">{conversation.preview}</p>
                          <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                            <span>{conversation.timestamp}</span>
                            <span>{conversation.messageCount} messages</span>
                            <Badge
                              variant={conversation.status === "flagged" ? "destructive" : "secondary"}
                              className="text-xs"
                            >
                              {conversation.status}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>
          </Card>
        ))}
      </div>
    </div>
  )
}
