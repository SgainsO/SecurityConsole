"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  CheckCircle,
  AlertTriangle, 
  XCircle,
  Loader2,
  Search,
  Clock,
  User,
  Shield,
  AlertCircle
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { getMessagesByStatus, setMessageStatus, type Message } from "@/lib/api"

type ViewType = "safe" | "review" | "blocked"

export function ThreeColumnDashboard() {
  const [safeMessages, setSafeMessages] = useState<Message[]>([])
  const [flaggedMessages, setFlaggedMessages] = useState<Message[]>([])
  const [blockedMessages, setBlockedMessages] = useState<Message[]>([])
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null)
  const [activeView, setActiveView] = useState<ViewType>("review")
  const [searchQuery, setSearchQuery] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actioningMessageId, setActioningMessageId] = useState<string | null>(null)
  const { toast } = useToast()

  // Load all messages on component mount
  useEffect(() => {
    loadAllMessages()
  }, [])

  // Auto-select first message when changing views
  useEffect(() => {
    if (activeView === "safe" && safeMessages.length > 0) {
      setSelectedMessage(safeMessages[0])
    } else if (activeView === "review" && flaggedMessages.length > 0) {
      setSelectedMessage(flaggedMessages[0])
    } else if (activeView === "blocked" && blockedMessages.length > 0) {
      setSelectedMessage(blockedMessages[0])
    } else {
      setSelectedMessage(null)
    }
  }, [activeView, safeMessages, flaggedMessages, blockedMessages])

  const loadAllMessages = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const [safe, flagged, blocked] = await Promise.all([
        getMessagesByStatus("SAFE"),
        getMessagesByStatus("FLAG"),
        getMessagesByStatus("BLOCKED")
      ])

      setSafeMessages(safe)
      setFlaggedMessages(flagged)
      setBlockedMessages(blocked)
      
      // Set initial selected message
      if (flagged.length > 0) {
        setSelectedMessage(flagged[0])
      }
    } catch (err) {
      console.error("Error loading messages:", err)
      setError("Failed to load messages. Please try again.")
      toast({
        title: "Error",
        description: "Failed to load messages from the server.",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleMessageAction = async (messageId: string, newStatus: "SAFE" | "BLOCKED") => {
    try {
      setActioningMessageId(messageId)
      
      // Update status in backend
      await setMessageStatus(messageId, newStatus)
      
      const message = flaggedMessages.find(m => m.id === messageId)
      if (!message) return
      
      // Update local state
      setFlaggedMessages(prev => prev.filter(m => m.id !== messageId))
      
      const updatedMessage = { ...message, status: newStatus, updated_at: new Date().toISOString() }
      if (newStatus === "SAFE") {
        setSafeMessages(prev => [updatedMessage, ...prev])
      } else {
        setBlockedMessages(prev => [updatedMessage, ...prev])
      }
      
      // Select next message or clear selection
      const nextMessage = flaggedMessages.find(m => m.id !== messageId)
      setSelectedMessage(nextMessage || null)
      
      toast({
        title: newStatus === "SAFE" ? "Approved" : "Blocked",
        description: `Message marked as ${newStatus.toLowerCase()}`,
      })
    } catch (error) {
      console.error("Error updating message:", error)
      toast({
        title: "Error",
        description: "Failed to update message status. Please try again.",
        variant: "destructive"
      })
    } finally {
      setActioningMessageId(null)
    }
  }

  const handleRestoreMessage = async (messageId: string) => {
    try {
      setActioningMessageId(messageId)
      
      // Update status in backend
      await setMessageStatus(messageId, "SAFE")
      
      const message = blockedMessages.find(m => m.id === messageId)
      if (!message) return
      
      // Update local state
      setBlockedMessages(prev => prev.filter(m => m.id !== messageId))
      const updatedMessage = { ...message, status: "SAFE" as const, updated_at: new Date().toISOString() }
      setSafeMessages(prev => [updatedMessage, ...prev])
      
      // Clear selection if it was the restored message
      if (selectedMessage?.id === messageId) {
        setSelectedMessage(null)
      }
      
      toast({
        title: "Restored",
        description: "Message restored successfully",
      })
    } catch (error) {
      console.error("Error restoring message:", error)
      toast({
        title: "Error",
        description: "Failed to restore message. Please try again.",
        variant: "destructive"
      })
    } finally {
      setActioningMessageId(null)
    }
  }

  const getTimeAgo = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (seconds < 60) return `${seconds} seconds ago`
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`
    const days = Math.floor(hours / 24)
    return `${days} day${days !== 1 ? 's' : ''} ago`
  }

  const getRiskScore = (message: Message): number => {
    // Try to get risk score from metadata if available
    if (message.metadata?.risk_score) {
      return message.metadata.risk_score
    }
    
    // Otherwise, calculate based on prompt keywords
    const prompt = message.prompt.toLowerCase()
    let score = 30
    
    if (prompt.includes("ssn")) score += 20
    if (prompt.includes("credit card")) score += 20
    if (prompt.includes("password")) score += 15
    if (prompt.includes("bypass")) score += 15
    if (prompt.includes("jailbreak")) score += 15
    if (prompt.includes("data")) score += 10
    if (prompt.includes("access")) score += 10
    if (prompt.includes("confidential")) score += 10
    if (prompt.includes("admin")) score += 10
    
    return Math.min(100, score)
  }

  const getRiskFactors = (message: Message) => {
    // Try to get risk factors from metadata if available
    if (message.metadata?.risk_factors && Array.isArray(message.metadata.risk_factors)) {
      return message.metadata.risk_factors
    }
    
    // Otherwise, determine based on prompt analysis
    const prompt = message.prompt.toLowerCase()
    const factors = []
    
    if (prompt.includes("ssn") || prompt.includes("credit card") || prompt.includes("social security")) {
      factors.push({ name: "PII Detection", level: "HIGH" as const })
    }
    if (prompt.includes("bypass") || prompt.includes("jailbreak") || prompt.includes("ignore")) {
      factors.push({ name: "Security Bypass", level: "HIGH" as const })
    }
    if (prompt.includes("password") || prompt.includes("credentials") || prompt.includes("admin")) {
      factors.push({ name: "Unauthorized Access", level: "MEDIUM" as const })
    }
    if (prompt.includes("data") || prompt.includes("database") || prompt.includes("extract")) {
      factors.push({ name: "Data Exfiltration", level: "MEDIUM" as const })
    }
    
    return factors.length > 0 ? factors : [{ name: "General Review", level: "LOW" as const }]
  }

  const getCurrentMessages = () => {
    switch (activeView) {
      case "safe": return safeMessages
      case "review": return flaggedMessages
      case "blocked": return blockedMessages
    }
  }

  const filteredMessages = getCurrentMessages().filter(msg => 
    searchQuery === "" || 
    msg.prompt.toLowerCase().includes(searchQuery.toLowerCase()) ||
    msg.employee_id.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-muted-foreground" />
          <p className="mt-4 text-sm text-muted-foreground">Loading messages...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-destructive" />
          <h3 className="mt-4 text-lg font-semibold text-foreground">Error Loading Messages</h3>
          <p className="mt-2 text-sm text-muted-foreground">{error}</p>
          <Button onClick={loadAllMessages} className="mt-4">
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col bg-background">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-border p-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-foreground">Security Dashboard</h1>
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search messages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Message List */}
        <div className="flex w-96 flex-col border-r border-border">
          {/* Category Tabs */}
          <div className="flex-shrink-0 border-b border-border">
            <div className="flex">
              <button
                onClick={() => {
                  setActiveView("safe")
                  setSelectedMessage(safeMessages[0] || null)
                }}
                className={`flex flex-1 items-center justify-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                  activeView === "safe"
                    ? "border-green-500 text-foreground"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <CheckCircle className="h-4 w-4" />
                SAFE ({safeMessages.length})
              </button>
              <button
                onClick={() => {
                  setActiveView("review")
                  setSelectedMessage(flaggedMessages[0] || null)
                }}
                className={`flex flex-1 items-center justify-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                  activeView === "review"
                    ? "border-yellow-500 text-foreground"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <AlertTriangle className="h-4 w-4" />
                REVIEW ({flaggedMessages.length})
              </button>
              <button
                onClick={() => {
                  setActiveView("blocked")
                  setSelectedMessage(blockedMessages[0] || null)
                }}
                className={`flex flex-1 items-center justify-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                  activeView === "blocked"
                    ? "border-red-500 text-foreground"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <XCircle className="h-4 w-4" />
                BLOCKED ({blockedMessages.length})
              </button>
            </div>
          </div>

          {/* Message List */}
          <ScrollArea className="flex-1">
            <div className="p-2">
              {filteredMessages.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <p className="text-sm text-muted-foreground">No messages found</p>
                </div>
              ) : (
                filteredMessages.map((message) => {
                  const riskScore = getRiskScore(message)
                  const isSelected = selectedMessage?.id === message.id
                  
                  return (
                    <button
                      key={message.id}
                      onClick={() => setSelectedMessage(message)}
                      className={`mb-2 w-full rounded-lg border p-3 text-left transition-colors ${
                        isSelected
                          ? "border-primary bg-accent"
                          : "border-border bg-card hover:bg-accent/50"
                      }`}
                    >
                      <div className="mb-2 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {activeView === "review" && riskScore >= 70 && (
                            <div className="h-2 w-2 rounded-full bg-red-500" />
                          )}
                          {activeView === "review" && riskScore >= 50 && riskScore < 70 && (
                            <div className="h-2 w-2 rounded-full bg-yellow-500" />
                          )}
                          {activeView === "review" && riskScore < 50 && (
                            <div className="h-2 w-2 rounded-full bg-green-500" />
                          )}
                          <span className="text-xs font-medium text-foreground">{message.employee_id}</span>
                        </div>
                        <span className="text-xs text-muted-foreground">{getTimeAgo(message.created_at).split(' ')[0]}{getTimeAgo(message.created_at).split(' ')[1]}</span>
                      </div>
                      <p className="line-clamp-2 text-sm text-foreground/80">{message.prompt}</p>
                      {activeView === "review" && (
                        <div className="mt-2 text-xs text-muted-foreground">
                          Risk: {riskScore}%
                        </div>
                      )}
                    </button>
                  )
                })
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Right Panel - Message Details */}
        <div className="flex flex-1 flex-col">
          {selectedMessage ? (
            <ScrollArea className="flex-1">
              <div className="p-6">
                {/* Header */}
                <div className="mb-6">
                  <div className="mb-4 flex items-start justify-between">
                    <div>
                      <div className="mb-2 flex items-center gap-2">
                        {selectedMessage.status === "SAFE" && (
                          <Badge variant="outline" className="bg-green-500/10 text-green-700">
                            <CheckCircle className="mr-1 h-3 w-3" />
                            SAFE
                          </Badge>
                        )}
                        {selectedMessage.status === "FLAG" && (
                          <Badge variant="outline" className="bg-yellow-500/10 text-yellow-700">
                            <AlertTriangle className="mr-1 h-3 w-3" />
                            FLAGGED
                          </Badge>
                        )}
                        {selectedMessage.status === "BLOCKED" && (
                          <Badge variant="destructive">
                            <XCircle className="mr-1 h-3 w-3" />
                            BLOCKED
                          </Badge>
                        )}
                      </div>
                      <h2 className="text-2xl font-semibold text-foreground">Message Details</h2>
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="grid grid-cols-3 gap-4">
                    <Card className="p-3">
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <User className="h-4 w-4" />
                        <span className="text-xs">Employee</span>
                      </div>
                      <p className="mt-1 font-medium text-foreground">{selectedMessage.employee_id}</p>
                    </Card>
                    <Card className="p-3">
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Clock className="h-4 w-4" />
                        <span className="text-xs">Time</span>
                      </div>
                      <p className="mt-1 font-medium text-foreground">{getTimeAgo(selectedMessage.created_at)}</p>
                    </Card>
                    <Card className="p-3">
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Shield className="h-4 w-4" />
                        <span className="text-xs">Session</span>
                      </div>
                      <p className="mt-1 font-medium text-foreground">#{selectedMessage.session_id?.slice(-4) || "N/A"}</p>
                    </Card>
                  </div>
                </div>

                {/* Full Message */}
                <div className="mb-6">
                  <h3 className="mb-3 text-sm font-medium text-muted-foreground">Full Message</h3>
                  <Card className="p-4">
                    <p className="whitespace-pre-wrap text-foreground">{selectedMessage.prompt}</p>
                  </Card>
                </div>

                {/* Risk Analysis */}
                {selectedMessage.status === "FLAG" && (
                  <div className="mb-6">
                    <h3 className="mb-3 text-sm font-medium text-muted-foreground">Risk Analysis</h3>
                    <Card className="p-4">
                      <div className="mb-4">
                        {getRiskFactors(selectedMessage).map((factor, idx) => (
                          <div key={idx} className="mb-2 flex items-center justify-between">
                            <span className="text-sm text-foreground">{factor.name}:</span>
                            <Badge
                              variant={
                                factor.level === "HIGH" ? "destructive" :
                                factor.level === "MEDIUM" ? "outline" :
                                "secondary"
                              }
                              className="text-xs"
                            >
                              {factor.level}
                            </Badge>
                          </div>
                        ))}
                      </div>

                      <div className="border-t border-border pt-4">
                        <div className="mb-2 flex items-center justify-between">
                          <span className="text-sm font-medium text-foreground">Overall Risk Score</span>
                          <span className="text-lg font-bold text-foreground">{getRiskScore(selectedMessage)}/100</span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                          <div
                            className={`h-full ${
                              getRiskScore(selectedMessage) >= 70 ? "bg-red-500" :
                              getRiskScore(selectedMessage) >= 50 ? "bg-yellow-500" :
                              "bg-green-500"
                            }`}
                            style={{ width: `${getRiskScore(selectedMessage)}%` }}
                          />
                        </div>
                      </div>
                    </Card>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-3">
                  {selectedMessage.status === "FLAG" && (
                    <>
                      <Button
                        size="lg"
                        variant="outline"
                        onClick={() => handleMessageAction(selectedMessage.id, "SAFE")}
                        disabled={actioningMessageId === selectedMessage.id}
                        className="flex-1"
                      >
                        {actioningMessageId === selectedMessage.id ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <CheckCircle className="mr-2 h-4 w-4" />
                        )}
                        Approve Message
                      </Button>
                      <Button
                        size="lg"
                        variant="destructive"
                        onClick={() => handleMessageAction(selectedMessage.id, "BLOCKED")}
                        disabled={actioningMessageId === selectedMessage.id}
                        className="flex-1"
                      >
                        {actioningMessageId === selectedMessage.id ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <XCircle className="mr-2 h-4 w-4" />
                        )}
                        Block Message
                      </Button>
                    </>
                  )}
                  {selectedMessage.status === "BLOCKED" && (
                    <Button
                      size="lg"
                      variant="outline"
                      onClick={() => handleRestoreMessage(selectedMessage.id)}
                      disabled={actioningMessageId === selectedMessage.id}
                      className="w-full"
                    >
                      {actioningMessageId === selectedMessage.id ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        "Restore Message"
                      )}
                    </Button>
                  )}
                </div>
              </div>
            </ScrollArea>
          ) : (
            <div className="flex flex-1 items-center justify-center">
              <div className="text-center">
                <Shield className="mx-auto h-12 w-12 text-muted-foreground/30" />
                <p className="mt-4 text-sm text-muted-foreground">Select a message to view details</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
