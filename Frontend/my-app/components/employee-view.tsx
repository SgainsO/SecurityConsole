"use client"

import { useState } from "react"
import { EmployeeSidebar } from "@/components/employee-sidebar"
import { EmployeeChat } from "@/components/employee-chat"

interface EmployeeViewProps {
  employeeId: string
}

export function EmployeeView({ employeeId }: EmployeeViewProps) {
  const [currentSessionId, setCurrentSessionId] = useState<string>(
    `session_${employeeId}_${Date.now()}`
  )
  const [refreshKey, setRefreshKey] = useState(0)

  const handleNewSession = () => {
    const newSessionId = `session_${employeeId}_${Date.now()}`
    setCurrentSessionId(newSessionId)
  }

  const handleSessionSelect = (sessionId: string) => {
    setCurrentSessionId(sessionId)
  }

  const handleSessionChange = () => {
    // Trigger sidebar refresh when a message is sent
    setRefreshKey(prev => prev + 1)
  }

  return (
    <div className="flex h-screen bg-background">
      <EmployeeSidebar
        key={refreshKey}
        employeeId={employeeId}
        currentSessionId={currentSessionId}
        onSessionSelect={handleSessionSelect}
        onNewSession={handleNewSession}
      />
      <div className="flex-1">
        <EmployeeChat
          employeeId={employeeId}
          sessionId={currentSessionId}
          onSessionChange={handleSessionChange}
        />
      </div>
    </div>
  )
}

