"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { 
  MessageSquare, 
  CheckCircle, 
  AlertTriangle, 
  XCircle,
  TrendingUp,
  Users,
  Loader2,
  RefreshCw,
  Eye
} from "lucide-react"
import { getStatistics, getFlaggedMessages, type MessageStatistics, type Message } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface DashboardOverviewProps {
  onViewFlagged?: () => void
}

export function DashboardOverview({ onViewFlagged }: DashboardOverviewProps) {
  const [stats, setStats] = useState<MessageStatistics | null>(null)
  const [recentFlags, setRecentFlags] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async (showToast = false) => {
    try {
      setIsRefreshing(true)
      const [statsData, flaggedData] = await Promise.all([
        getStatistics(),
        getFlaggedMessages()
      ])
      
      setStats(statsData)
      setRecentFlags(flaggedData.slice(0, 5)) // Show only 5 most recent
      
      if (showToast) {
        toast({
          title: "Refreshed",
          description: "Dashboard data updated",
        })
      }
    } catch (error) {
      console.error("Error loading dashboard data:", error)
      toast({
        title: "Error",
        description: "Failed to load dashboard data",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / (1000 * 60))
    
    if (minutes < 1) return "Just now"
    if (minutes < 60) return `${minutes}m ago`
    
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours}h ago`
    
    const days = Math.floor(hours / 24)
    return `${days}d ago`
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-muted-foreground" />
          <p className="mt-4 font-mono text-sm text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="font-mono text-sm text-muted-foreground">No data available</p>
      </div>
    )
  }

  const statCards = [
    {
      title: "Total Messages",
      value: stats.total_messages,
      icon: MessageSquare,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10"
    },
    {
      title: "Safe Messages",
      value: stats.safe_messages,
      icon: CheckCircle,
      color: "text-green-500",
      bgColor: "bg-green-500/10"
    },
    {
      title: "Flagged Messages",
      value: stats.flagged_messages,
      icon: AlertTriangle,
      color: "text-yellow-500",
      bgColor: "bg-yellow-500/10",
      percentage: stats.flagged_percentage
    },
    {
      title: "Blocked Messages",
      value: stats.blocked_messages,
      icon: XCircle,
      color: "text-red-500",
      bgColor: "bg-red-500/10",
      percentage: stats.blocked_percentage
    }
  ]

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="font-mono text-2xl font-bold text-foreground">Dashboard</h1>
            <p className="mt-1 font-mono text-sm text-muted-foreground">
              Security monitoring overview
            </p>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => loadDashboardData(true)}
            disabled={isRefreshing}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        {/* Stat Cards */}
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {statCards.map((stat) => {
            const Icon = stat.icon
            return (
              <Card key={stat.title} className="border-border p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-mono text-xs text-muted-foreground">{stat.title}</p>
                    <p className="mt-2 font-mono text-3xl font-bold text-foreground">
                      {stat.value.toLocaleString()}
                    </p>
                    {stat.percentage !== undefined && (
                      <p className="mt-1 font-mono text-xs text-muted-foreground">
                        {stat.percentage.toFixed(1)}% of total
                      </p>
                    )}
                  </div>
                  <div className={`rounded-lg ${stat.bgColor} p-3`}>
                    <Icon className={`h-5 w-5 ${stat.color}`} />
                  </div>
                </div>
              </Card>
            )
          })}
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Recent Flagged Messages */}
          <Card className="border-border p-4">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                <h2 className="font-mono text-lg font-semibold text-foreground">
                  Recent Flags
                </h2>
              </div>
              {onViewFlagged && (
                <Button size="sm" variant="outline" onClick={onViewFlagged}>
                  View All
                </Button>
              )}
            </div>

            <div className="space-y-3">
              {recentFlags.length === 0 ? (
                <div className="py-8 text-center">
                  <CheckCircle className="mx-auto h-12 w-12 text-muted-foreground/30" />
                  <p className="mt-2 font-mono text-sm text-muted-foreground">
                    No flagged messages
                  </p>
                </div>
              ) : (
                recentFlags.map((message) => (
                  <div
                    key={message.id}
                    className="rounded-lg border border-border bg-card p-3"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <Badge variant="outline" className="font-mono text-xs">
                        {message.employee_id}
                      </Badge>
                      <span className="font-mono text-xs text-muted-foreground">
                        {formatDate(message.created_at)}
                      </span>
                    </div>
                    <p className="line-clamp-2 font-mono text-sm text-foreground/80">
                      {message.prompt}
                    </p>
                  </div>
                ))
              )}
            </div>
          </Card>

          {/* Top Flagged Employees */}
          <Card className="border-border p-4">
            <div className="mb-4 flex items-center gap-2">
              <Users className="h-5 w-5 text-muted-foreground" />
              <h2 className="font-mono text-lg font-semibold text-foreground">
                Top Flagged Employees
              </h2>
            </div>

            <div className="space-y-3">
              {stats.top_flagged_employees.length === 0 ? (
                <div className="py-8 text-center">
                  <Users className="mx-auto h-12 w-12 text-muted-foreground/30" />
                  <p className="mt-2 font-mono text-sm text-muted-foreground">
                    No data available
                  </p>
                </div>
              ) : (
                stats.top_flagged_employees.slice(0, 5).map((employee, index) => (
                  <div
                    key={employee.employee_id}
                    className="flex items-center justify-between rounded-lg border border-border bg-card p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted font-mono text-sm font-semibold text-foreground">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-mono text-sm font-medium text-foreground">
                          {employee.employee_id}
                        </p>
                        <p className="font-mono text-xs text-muted-foreground">
                          {employee.count} {employee.count === 1 ? "flag" : "flags"}
                        </p>
                      </div>
                    </div>
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                  </div>
                ))
              )}
            </div>
          </Card>

          {/* Top Blocked Employees */}
          <Card className="border-border p-4">
            <div className="mb-4 flex items-center gap-2">
              <XCircle className="h-5 w-5 text-red-500" />
              <h2 className="font-mono text-lg font-semibold text-foreground">
                Top Blocked Employees
              </h2>
            </div>

            <div className="space-y-3">
              {stats.top_blocked_employees.length === 0 ? (
                <div className="py-8 text-center">
                  <CheckCircle className="mx-auto h-12 w-12 text-muted-foreground/30" />
                  <p className="mt-2 font-mono text-sm text-muted-foreground">
                    No blocked messages
                  </p>
                </div>
              ) : (
                stats.top_blocked_employees.slice(0, 5).map((employee, index) => (
                  <div
                    key={employee.employee_id}
                    className="flex items-center justify-between rounded-lg border border-border bg-card p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted font-mono text-sm font-semibold text-foreground">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-mono text-sm font-medium text-foreground">
                          {employee.employee_id}
                        </p>
                        <p className="font-mono text-xs text-muted-foreground">
                          {employee.count} {employee.count === 1 ? "block" : "blocks"}
                        </p>
                      </div>
                    </div>
                    <XCircle className="h-4 w-4 text-red-500" />
                  </div>
                ))
              )}
            </div>
          </Card>

          {/* Quick Stats */}
          <Card className="border-border p-4">
            <div className="mb-4 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-muted-foreground" />
              <h2 className="font-mono text-lg font-semibold text-foreground">
                Quick Stats
              </h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm text-muted-foreground">Flag Rate</span>
                <span className="font-mono text-lg font-semibold text-foreground">
                  {stats.flagged_percentage.toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm text-muted-foreground">Block Rate</span>
                <span className="font-mono text-lg font-semibold text-foreground">
                  {stats.blocked_percentage.toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm text-muted-foreground">Safe Rate</span>
                <span className="font-mono text-lg font-semibold text-foreground">
                  {((stats.safe_messages / stats.total_messages) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="mt-4 rounded-lg border border-border bg-muted p-3">
                <p className="font-mono text-xs text-muted-foreground">
                  System Health
                </p>
                <div className="mt-2 flex items-center gap-2">
                  <div className="h-2 flex-1 rounded-full bg-background">
                    <div
                      className="h-2 rounded-full bg-green-500"
                      style={{
                        width: `${((stats.safe_messages / stats.total_messages) * 100).toFixed(0)}%`
                      }}
                    />
                  </div>
                  <span className="font-mono text-xs font-semibold text-foreground">
                    {((stats.safe_messages / stats.total_messages) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

