"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  Users, 
  AlertTriangle, 
  XCircle,
  MessageSquare,
  Loader2,
  RefreshCw,
  Search,
  Shield
} from "lucide-react"
import { getConversations, type ConversationSummary } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface EmployeeStats {
  employee_id: string
  total_messages: number
  safe_messages: number
  flagged_messages: number
  blocked_messages: number
  conversations_count: number
  risk_score: number
}

export function EmployeesView() {
  const [employees, setEmployees] = useState<EmployeeStats[]>([])
  const [filteredEmployees, setFilteredEmployees] = useState<EmployeeStats[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [sortBy, setSortBy] = useState<"flags" | "blocks" | "total">("flags")
  const { toast } = useToast()

  useEffect(() => {
    loadEmployeeData()
  }, [])

  useEffect(() => {
    filterAndSortEmployees()
  }, [employees, searchTerm, sortBy])

  const loadEmployeeData = async (showToast = false) => {
    try {
      setIsRefreshing(true)
      
      // Get all conversations to aggregate employee statistics
      const conversations = await getConversations({ limit: 1000 })
      
      // Aggregate stats by employee
      const employeeMap = new Map<string, EmployeeStats>()
      
      conversations.forEach(conv => {
        const existing = employeeMap.get(conv.employee_id) || {
          employee_id: conv.employee_id,
          total_messages: 0,
          safe_messages: 0,
          flagged_messages: 0,
          blocked_messages: 0,
          conversations_count: 0,
          risk_score: 0
        }
        
        existing.total_messages += conv.message_count
        existing.safe_messages += conv.safe_count
        existing.flagged_messages += conv.flagged_count
        existing.blocked_messages += conv.blocked_count
        existing.conversations_count += 1
        
        // Calculate simple risk score (0-100)
        const flagWeight = 2
        const blockWeight = 5
        existing.risk_score = Math.min(100, 
          (existing.flagged_messages * flagWeight + existing.blocked_messages * blockWeight)
        )
        
        employeeMap.set(conv.employee_id, existing)
      })
      
      const employeeList = Array.from(employeeMap.values())
      setEmployees(employeeList)
      
      if (showToast) {
        toast({
          title: "Refreshed",
          description: `Loaded data for ${employeeList.length} employees`,
        })
      }
    } catch (error) {
      console.error("Error loading employee data:", error)
      toast({
        title: "Error",
        description: "Failed to load employee data",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  const filterAndSortEmployees = () => {
    let filtered = [...employees]

    // Apply search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase()
      filtered = filtered.filter(emp => 
        emp.employee_id.toLowerCase().includes(search)
      )
    }

    // Sort
    filtered.sort((a, b) => {
      if (sortBy === "flags") return b.flagged_messages - a.flagged_messages
      if (sortBy === "blocks") return b.blocked_messages - a.blocked_messages
      return b.total_messages - a.total_messages
    })

    setFilteredEmployees(filtered)
  }

  const getRiskLevel = (score: number): { label: string; color: string; bgColor: string } => {
    if (score >= 20) return { label: "High", color: "text-red-600", bgColor: "bg-red-500/10" }
    if (score >= 10) return { label: "Medium", color: "text-yellow-600", bgColor: "bg-yellow-500/10" }
    return { label: "Low", color: "text-green-600", bgColor: "bg-green-500/10" }
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-muted-foreground" />
          <p className="mt-4 font-mono text-sm text-muted-foreground">Loading employee data...</p>
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
            <div className="mb-2 flex items-center gap-2">
              <Users className="h-6 w-6 text-muted-foreground" />
              <h1 className="font-mono text-2xl font-bold text-foreground">Employees</h1>
            </div>
            <p className="font-mono text-sm text-muted-foreground">
              {filteredEmployees.length} {filteredEmployees.length === 1 ? "employee" : "employees"}
            </p>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => loadEmployeeData(true)}
            disabled={isRefreshing}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        {/* Search and Sort */}
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search by employee ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 font-mono text-sm"
            />
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant={sortBy === "flags" ? "secondary" : "outline"}
              onClick={() => setSortBy("flags")}
              className="gap-2 font-mono text-xs"
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              Flags
            </Button>
            <Button
              size="sm"
              variant={sortBy === "blocks" ? "secondary" : "outline"}
              onClick={() => setSortBy("blocks")}
              className="gap-2 font-mono text-xs"
            >
              <XCircle className="h-3.5 w-3.5" />
              Blocks
            </Button>
            <Button
              size="sm"
              variant={sortBy === "total" ? "secondary" : "outline"}
              onClick={() => setSortBy("total")}
              className="gap-2 font-mono text-xs"
            >
              <MessageSquare className="h-3.5 w-3.5" />
              Total
            </Button>
          </div>
        </div>
      </div>

      {/* Employee Grid */}
      <ScrollArea className="flex-1">
        <div className="grid gap-4 p-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredEmployees.length === 0 ? (
            <div className="col-span-full flex flex-col items-center justify-center py-12 text-center">
              <Users className="h-16 w-16 text-muted-foreground/30" />
              <p className="mt-4 font-mono text-sm text-muted-foreground">
                {searchTerm ? "No employees match your search" : "No employee data available"}
              </p>
            </div>
          ) : (
            filteredEmployees.map((employee) => {
              const risk = getRiskLevel(employee.risk_score)
              
              return (
                <Card key={employee.employee_id} className="border-border p-4">
                  <div className="mb-4 flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="mb-1 font-mono text-lg font-semibold text-foreground">
                        {employee.employee_id}
                      </h3>
                      <p className="font-mono text-xs text-muted-foreground">
                        {employee.conversations_count} {employee.conversations_count === 1 ? "conversation" : "conversations"}
                      </p>
                    </div>
                    <div className={`rounded-lg ${risk.bgColor} px-2.5 py-1`}>
                      <span className={`font-mono text-xs font-semibold ${risk.color}`}>
                        {risk.label} Risk
                      </span>
                    </div>
                  </div>

                  {/* Statistics */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between rounded-lg border border-border bg-muted/30 px-3 py-2">
                      <div className="flex items-center gap-2">
                        <MessageSquare className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="font-mono text-xs text-muted-foreground">
                          Total Messages
                        </span>
                      </div>
                      <span className="font-mono text-sm font-semibold text-foreground">
                        {employee.total_messages}
                      </span>
                    </div>

                    <div className="flex items-center justify-between rounded-lg border border-border bg-muted/30 px-3 py-2">
                      <div className="flex items-center gap-2">
                        <Shield className="h-3.5 w-3.5 text-green-500" />
                        <span className="font-mono text-xs text-muted-foreground">
                          Safe
                        </span>
                      </div>
                      <span className="font-mono text-sm font-semibold text-green-600">
                        {employee.safe_messages}
                      </span>
                    </div>

                    {employee.flagged_messages > 0 && (
                      <div className="flex items-center justify-between rounded-lg border border-yellow-200 bg-yellow-50 px-3 py-2">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="h-3.5 w-3.5 text-yellow-600" />
                          <span className="font-mono text-xs text-yellow-700">
                            Flagged
                          </span>
                        </div>
                        <span className="font-mono text-sm font-semibold text-yellow-700">
                          {employee.flagged_messages}
                        </span>
                      </div>
                    )}

                    {employee.blocked_messages > 0 && (
                      <div className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50 px-3 py-2">
                        <div className="flex items-center gap-2">
                          <XCircle className="h-3.5 w-3.5 text-red-600" />
                          <span className="font-mono text-xs text-red-700">
                            Blocked
                          </span>
                        </div>
                        <span className="font-mono text-sm font-semibold text-red-700">
                          {employee.blocked_messages}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Risk Score Bar */}
                  <div className="mt-4 rounded-lg border border-border bg-muted/30 p-2">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="font-mono text-xs text-muted-foreground">Risk Score</span>
                      <span className={`font-mono text-xs font-semibold ${risk.color}`}>
                        {employee.risk_score}/100
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-background">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          employee.risk_score >= 20 ? "bg-red-500" :
                          employee.risk_score >= 10 ? "bg-yellow-500" :
                          "bg-green-500"
                        }`}
                        style={{ width: `${Math.min(100, employee.risk_score)}%` }}
                      />
                    </div>
                  </div>
                </Card>
              )
            })
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
