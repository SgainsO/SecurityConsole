"use client"

import { 
  LayoutDashboard, 
  AlertTriangle, 
  MessageSquare, 
  Users, 
  Settings
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export type EmployerView = "dashboard" | "flagged" | "conversations" | "employees" | "settings"

interface EmployerNavigationProps {
  activeView: EmployerView
  onViewChange: (view: EmployerView) => void
  flaggedCount?: number
}

export function EmployerNavigation({ 
  activeView, 
  onViewChange,
  flaggedCount = 0
}: EmployerNavigationProps) {
  const navItems = [
    {
      id: "dashboard" as EmployerView,
      label: "Dashboard",
      icon: LayoutDashboard,
      badge: null
    },
    {
      id: "flagged" as EmployerView,
      label: "Flagged Messages",
      icon: AlertTriangle,
      badge: flaggedCount > 0 ? flaggedCount : null
    },
    {
      id: "conversations" as EmployerView,
      label: "All Conversations",
      icon: MessageSquare,
      badge: null
    },
    {
      id: "employees" as EmployerView,
      label: "Employees",
      icon: Users,
      badge: null
    },
    {
      id: "settings" as EmployerView,
      label: "Settings",
      icon: Settings,
      badge: null
    }
  ]

  return (
    <div className="flex h-full w-64 flex-col border-r border-border bg-background">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-border p-4">
        <h1 className="font-mono text-lg font-bold text-foreground">
          Security Console
        </h1>
        <p className="mt-1 font-mono text-xs text-muted-foreground">
          Employer Dashboard
        </p>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = activeView === item.id
          
          return (
            <Button
              key={item.id}
              variant={isActive ? "secondary" : "ghost"}
              className={`w-full justify-start gap-3 font-mono text-sm ${
                isActive ? "bg-accent" : ""
              }`}
              onClick={() => onViewChange(item.id)}
            >
              <Icon className="h-4 w-4" />
              <span className="flex-1 text-left">{item.label}</span>
              {item.badge !== null && (
                <Badge 
                  variant={item.id === "flagged" ? "destructive" : "secondary"}
                  className="ml-auto"
                >
                  {item.badge}
                </Badge>
              )}
            </Button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="flex-shrink-0 border-t border-border p-4">
        <div className="rounded-lg border border-border bg-card p-3">
          <div className="font-mono text-xs text-muted-foreground">
            Status
          </div>
          <div className="mt-1 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500"></div>
            <span className="font-mono text-xs font-semibold text-foreground">
              System Online
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

