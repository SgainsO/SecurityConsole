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
import { formatRelativeTime } from "@/lib/date-utils"

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
              <Card 
                key={conversation.session_id} 
                className="group cursor-pointer overflow-hidden transition-all hover:border-primary/50 hover:bg-accent/5"
                onClick={() => onViewConversation?.(conversation.session_id)}
              >
                <div className="p-4">
                  {/* Header Row */}
                  <div className="mb-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className="font-mono text-xs font-semibold">
                        {conversation.employee_id}
                      </Badge>
                      <span className="font-mono text-xs text-muted-foreground">
                        {formatRelativeTime(conversation.last_message_at)}
                      </span>
                    </div>
                    <span className="font-mono text-xs text-muted-foreground">
                      #{conversation.session_id.slice(-8)}
                    </span>
                  </div>

                  {/* Message Preview */}
                  {conversation.latest_prompt && (
                    <p className="mb-3 line-clamp-2 text-sm text-foreground/90">
                      {conversation.latest_prompt}
                    </p>
                  )}

                  {/* Stats Bar */}
                  <div className="flex items-center justify-between border-t border-border/50 pt-3">
                    <div className="flex items-center gap-4">
                      <span className="flex items-center gap-1.5 font-mono text-xs text-muted-foreground">
                        <MessageSquare className="h-3.5 w-3.5" />
                        {conversation.message_count}
                      </span>
                      <span className="flex items-center gap-1.5 font-mono text-xs text-green-600">
                        <CheckCircle className="h-3.5 w-3.5" />
                        {conversation.safe_count}
                      </span>
                      {conversation.flagged_count > 0 && (
                        <span className="flex items-center gap-1.5 font-mono text-xs font-semibold text-yellow-600">
                          <AlertTriangle className="h-3.5 w-3.5" />
                          {conversation.flagged_count}
                        </span>
                      )}
                      {conversation.blocked_count > 0 && (
                        <span className="flex items-center gap-1.5 font-mono text-xs font-semibold text-red-600">
                          <XCircle className="h-3.5 w-3.5" />
                          {conversation.blocked_count}
                        </span>
                      )}
                    </div>
                    <Eye className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
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

