"use client"

import { useState } from "react"
import { ChatInterface } from "@/components/chat-interface"
import { ReviewPanel } from "@/components/review-panel"

export type View = "conversations" | "employees" | "review" | "settings"

export function EmployerDashboard() {
  const [activeView, setActiveView] = useState<View>("conversations")

  return (
    <div className="flex h-screen bg-background">
      <ChatInterface />
      <ReviewPanel />
    </div>
  )
}
