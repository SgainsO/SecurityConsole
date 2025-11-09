"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  MessageSquare, 
  AlertTriangle, 
  XCircle,
  CheckCircle,
  Loader2,
  RefreshCw,
  Search,
  Eye,
  Filter
} from "lucide-react"
import { getConversations, type ConversationSummary } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface AllConversationsViewProps {
  onViewConversation?: (sessionId: string) => void
}

export function AllConversationsView({ onViewConversation }: AllConversationsViewProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [filteredConversations, setFilteredConversations] = useState<ConversationSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [filterStatus, setFilterStatus] = useState<"all" | "flagged" | "blocked">("all")
  const { toast } = useToast()

  useEffect(() => {
    loadConversations()
  }, [])

  useEffect(() => {
    filterConversations()
  }, [conversations, searchTerm, filterStatus])

  const loadConversations = async (showToast = false) => {
    try {
      setIsRefreshing(true)
      const data = await getConversations({ limit: 500 })
      setConversations(data)
      
      if (showToast) {
        toast({
          title: "Refreshed",
          description: `Loaded ${data.length} conversations`,
        })
      }
    } catch (error) {
      console.error("Error loading conversations:", error)
      toast({
        title: "Error",
        description: "Failed to load conversations",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  const filterConversations = () => {
    let filtered = [...conversations]

    // Apply status filter
    if (filterStatus === "flagged") {
      filtered = filtered.filter(conv => conv.flagged_count > 0)
    } else if (filterStatus === "blocked") {
      filtered = filtered.filter(conv => conv.blocked_count > 0)
    }

    // Apply search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase()
      filtered = filtered.filter(conv => 
        conv.session_id.toLowerCase().includes(search) ||
        conv.employee_id.toLowerCase().includes(search) ||
        conv.latest_prompt?.toLowerCase().includes(search)
      )
    }

    setFilteredConversations(filtered)
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
    
    return date.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-muted-foreground" />
          <p className="mt-4 font-mono text-sm text-muted-foreground">Loading conversations...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-border p-6">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h1 className="font-mono text-2xl font-bold text-foreground">All Conversations</h1>
            <p className="mt-1 font-mono text-sm text-muted-foreground">
              {filteredConversations.length} {filteredConversations.length === 1 ? "conversation" : "conversations"}
            </p>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => loadConversations(true)}
            disabled={isRefreshing}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        {/* Search and Filters */}
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search by session ID, employee ID, or message content..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 font-mono text-sm"
            />
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant={filterStatus === "all" ? "secondary" : "outline"}
              onClick={() => setFilterStatus("all")}
              className="gap-2 font-mono text-xs"
            >
              <Filter className="h-3.5 w-3.5" />
              All
            </Button>
            <Button
              size="sm"
              variant={filterStatus === "flagged" ? "secondary" : "outline"}
              onClick={() => setFilterStatus("flagged")}
              className="gap-2 font-mono text-xs"
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              Flagged
            </Button>
            <Button
              size="sm"
              variant={filterStatus === "blocked" ? "secondary" : "outline"}
              onClick={() => setFilterStatus("blocked")}
              className="gap-2 font-mono text-xs"
            >
              <XCircle className="h-3.5 w-3.5" />
              Blocked
            </Button>
          </div>
        </div>
      </div>

      {/* Conversations List */}
      <ScrollArea className="flex-1">
        <div className="space-y-3 p-6">
          {filteredConversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <MessageSquare className="h-16 w-16 text-muted-foreground/30" />
              <p className="mt-4 font-mono text-sm text-muted-foreground">
                {searchTerm || filterStatus !== "all" ? "No conversations match your filters" : "No conversations yet"}
              </p>
            </div>
          ) : (
            filteredConversations.map((conversation) => (
              <Card key={conversation.session_id} className="border-border p-4">
                <div className="flex items-start gap-4">
                  <div className="rounded-lg bg-muted p-3">
                    <MessageSquare className="h-5 w-5 text-muted-foreground" />
                  </div>

                  <div className="flex-1">
                    {/* Top Row: Employee and Session Info */}
                    <div className="mb-3 flex items-start justify-between">
                      <div>
                        <div className="mb-1 flex items-center gap-2">
                          <Badge variant="outline" className="font-mono text-xs">
                            {conversation.employee_id}
                          </Badge>
                          <span className="font-mono text-xs text-muted-foreground">
                            Session: {conversation.session_id.slice(-8)}
                          </span>
                        </div>
                        <p className="font-mono text-xs text-muted-foreground">
                          {formatDate(conversation.last_message_at)}
                        </p>
                      </div>

                      {onViewConversation && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onViewConversation(conversation.session_id)}
                          className="gap-2 font-mono text-xs"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          View
                        </Button>
                      )}
                    </div>

                    {/* Latest Message Preview */}
                    {conversation.latest_prompt && (
                      <p className="mb-3 line-clamp-2 font-mono text-sm text-foreground/80">
                        "{conversation.latest_prompt}"
                      </p>
                    )}

                    {/* Statistics Row */}
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1.5">
                        <MessageSquare className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="font-mono text-xs text-muted-foreground">
                          {conversation.message_count} messages
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5">
                        <CheckCircle className="h-3.5 w-3.5 text-green-500" />
                        <span className="font-mono text-xs text-muted-foreground">
                          {conversation.safe_count} safe
                        </span>
                      </div>

                      {conversation.flagged_count > 0 && (
                        <div className="flex items-center gap-1.5">
                          <AlertTriangle className="h-3.5 w-3.5 text-yellow-500" />
                          <span className="font-mono text-xs font-semibold text-yellow-600">
                            {conversation.flagged_count} flagged
                          </span>
                        </div>
                      )}

                      {conversation.blocked_count > 0 && (
                        <div className="flex items-center gap-1.5">
                          <XCircle className="h-3.5 w-3.5 text-red-500" />
                          <span className="font-mono text-xs font-semibold text-red-600">
                            {conversation.blocked_count} blocked
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  )
}

