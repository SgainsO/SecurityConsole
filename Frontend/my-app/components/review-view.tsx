"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AlertTriangle, CheckCircle, XCircle } from "lucide-react"
import { ConversationDetail } from "@/components/conversation-detail"

// Mock data for flagged conversations
const flaggedConversations = [
  {
    id: "f1",
    employeeName: "Emily Rodriguez",
    employeeId: "emp003",
    timestamp: "5h ago",
    preview: "Extract all customer data including SSN and credit card...",
    status: "flagged" as const,
    messageCount: 4,
    reason: "Attempting to access sensitive customer information",
    severity: "high" as const,
  },
  {
    id: "f2",
    employeeName: "Jessica Martinez",
    employeeId: "emp005",
    timestamp: "1d ago",
    preview: "Help me bypass the security authentication system...",
    status: "flagged" as const,
    messageCount: 6,
    reason: "Potential security bypass attempt",
    severity: "critical" as const,
  },
  {
    id: "f3",
    employeeName: "Robert Taylor",
    employeeId: "emp007",
    timestamp: "2d ago",
    preview: "How can I share confidential client contracts with...",
    status: "flagged" as const,
    messageCount: 3,
    reason: "Attempting to share confidential information",
    severity: "high" as const,
  },
]

const reviewedConversations = [
  {
    id: "r1",
    employeeName: "Alex Thompson",
    employeeId: "emp006",
    timestamp: "3d ago",
    preview: "Generate template for employee performance review",
    reviewStatus: "approved" as const,
    reviewedBy: "Admin",
  },
  {
    id: "r2",
    employeeName: "Lisa Anderson",
    employeeId: "emp008",
    timestamp: "4d ago",
    preview: "Can you access the HR database to update...",
    reviewStatus: "rejected" as const,
    reviewedBy: "Admin",
  },
]

export function ReviewView() {
  const [selectedConversation, setSelectedConversation] = useState<any | null>(null)

  if (selectedConversation) {
    return <ConversationDetail conversation={selectedConversation} onBack={() => setSelectedConversation(null)} />
  }

  return (
    <div className="h-full p-6">
      <div className="mb-6">
        <h2 className="mb-2 text-2xl font-semibold">Review Queue</h2>
        <p className="text-sm text-muted-foreground">Review flagged conversations and take appropriate action</p>
      </div>

      <Tabs defaultValue="pending" className="space-y-4">
        <TabsList>
          <TabsTrigger value="pending">Pending Review ({flaggedConversations.length})</TabsTrigger>
          <TabsTrigger value="reviewed">Reviewed ({reviewedConversations.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4">
          {flaggedConversations.map((conversation) => (
            <Card key={conversation.id} className="p-4">
              <div className="mb-3 flex items-start justify-between">
                <div className="flex-1">
                  <div className="mb-2 flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-destructive" />
                    <span className="font-medium">{conversation.employeeName}</span>
                    <Badge
                      variant="destructive"
                      className={
                        conversation.severity === "critical"
                          ? "bg-destructive text-destructive-foreground"
                          : "bg-warning text-warning-foreground"
                      }
                    >
                      {conversation.severity}
                    </Badge>
                  </div>
                  <p className="mb-2 text-sm">{conversation.preview}</p>
                  <p className="mb-3 text-sm text-muted-foreground">
                    <span className="font-medium">Reason:</span> {conversation.reason}
                  </p>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>{conversation.timestamp}</span>
                    <span>{conversation.messageCount} messages</span>
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={() => setSelectedConversation(conversation)} variant="outline">
                  View Details
                </Button>
                <Button size="sm" variant="default">
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Approve
                </Button>
                <Button size="sm" variant="destructive">
                  <XCircle className="mr-2 h-4 w-4" />
                  Flag & Notify
                </Button>
              </div>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="reviewed" className="space-y-4">
          {reviewedConversations.map((conversation) => (
            <Card key={conversation.id} className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="mb-2 flex items-center gap-2">
                    {conversation.reviewStatus === "approved" ? (
                      <CheckCircle className="h-5 w-5 text-accent" />
                    ) : (
                      <XCircle className="h-5 w-5 text-destructive" />
                    )}
                    <span className="font-medium">{conversation.employeeName}</span>
                    <Badge variant={conversation.reviewStatus === "approved" ? "secondary" : "destructive"}>
                      {conversation.reviewStatus}
                    </Badge>
                  </div>
                  <p className="mb-2 text-sm">{conversation.preview}</p>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>{conversation.timestamp}</span>
                    <span>Reviewed by {conversation.reviewedBy}</span>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}
