"use client"

import { useState, useEffect } from "react"
import { EmployerNavigation, type EmployerView } from "@/components/employer-navigation"
import { ThreeColumnDashboard } from "@/components/three-column-dashboard"
import { DashboardOverview } from "@/components/dashboard-overview"
import { AllConversationsView } from "@/components/all-conversations-view"
import { EmployeesView } from "@/components/employees-view"
import { ConversationDetail } from "@/components/conversation-detail"
import { SettingsView } from "@/components/settings-view"
import { getFlaggedMessages } from "@/lib/api"

export function EmployerView() {
  const [activeView, setActiveView] = useState<EmployerView>("dashboard")
  const [flaggedCount, setFlaggedCount] = useState(0)
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null)

  // Load flagged count for navigation badge
  useEffect(() => {
    loadFlaggedCount()
    
    // Refresh count every 30 seconds
    const interval = setInterval(loadFlaggedCount, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadFlaggedCount = async () => {
    try {
      const messages = await getFlaggedMessages()
      setFlaggedCount(messages.length)
    } catch (error) {
      console.error("Error loading flagged count:", error)
    }
  }

  const handleViewChange = (view: EmployerView) => {
    setActiveView(view)
    setSelectedConversationId(null)
  }

  const handleViewConversation = (sessionId: string) => {
    setSelectedConversationId(sessionId)
  }

  const handleBackFromConversation = () => {
    setSelectedConversationId(null)
  }

  const handleConversationUpdate = () => {
    loadFlaggedCount()
  }

  // Render conversation detail if a conversation is selected
  if (selectedConversationId) {
    return (
      <div className="flex h-screen bg-background">
        <EmployerNavigation
          activeView={activeView}
          onViewChange={handleViewChange}
          flaggedCount={flaggedCount}
        />
        <div className="flex-1">
          <ConversationDetail
            sessionId={selectedConversationId}
            onBack={handleBackFromConversation}
            onUpdate={handleConversationUpdate}
          />
        </div>
      </div>
    )
  }

  // Render main content based on active view
  let content
  switch (activeView) {
    case "dashboard":
      content = <DashboardOverview onViewFlagged={() => setActiveView("flagged")} />
      break
    case "flagged":
      content = <ThreeColumnDashboard />
      break
    case "conversations":
      content = <AllConversationsView onViewConversation={handleViewConversation} />
      break
    case "employees":
      content = <EmployeesView />
      break
    case "settings":
      content = <SettingsView />
      break
    default:
      content = <DashboardOverview onViewFlagged={() => setActiveView("flagged")} />
  }

  return (
    <div className="flex h-screen bg-background">
      <EmployerNavigation
        activeView={activeView}
        onViewChange={handleViewChange}
        flaggedCount={flaggedCount}
      />
      <div className="flex-1 overflow-hidden">
        {content}
      </div>
    </div>
  )
}

