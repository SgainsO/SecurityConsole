"use client"

import { MessageSquare, Users, AlertTriangle, Settings } from "lucide-react"
import { cn } from "@/lib/utils"
import type { View } from "@/components/employer-dashboard"

interface SidebarProps {
  activeView: View
  onViewChange: (view: View) => void
}

export function Sidebar({ activeView, onViewChange }: SidebarProps) {
  const navItems = [
    {
      id: "conversations" as View,
      label: "Conversations",
      icon: MessageSquare,
    },
    {
      id: "employees" as View,
      label: "Employees",
      icon: Users,
    },
    {
      id: "review" as View,
      label: "Review",
      icon: AlertTriangle,
    },
    {
      id: "settings" as View,
      label: "Settings",
      icon: Settings,
    },
  ]

  return (
    <aside className="w-64 border-r border-sidebar-border bg-sidebar">
      <div className="flex h-16 items-center border-b border-sidebar-border px-6">
        <h1 className="text-lg font-semibold text-sidebar-foreground">LLM Monitor</h1>
      </div>
      <nav className="space-y-1 p-4">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={cn(
                "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                activeView === item.id
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground",
              )}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </button>
          )
        })}
      </nav>
    </aside>
  )
}
