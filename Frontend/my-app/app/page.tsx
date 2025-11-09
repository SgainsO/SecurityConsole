"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Users, Shield } from "lucide-react"

export default function Home() {
  const router = useRouter()

  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="w-full max-w-md p-6">
        <div className="mb-8 text-center">
          <h1 className="mb-2 font-mono text-3xl font-bold text-foreground">
            Aiber
          </h1>
          <p className="font-mono text-sm text-muted-foreground">
            Select your role to continue
          </p>
        </div>

        <div className="space-y-4">
          <Card 
            className="cursor-pointer border-border p-6 transition-all hover:border-primary hover:shadow-lg"
            onClick={() => router.push("/employee")}
          >
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-lg bg-blue-500/10 p-3">
                <Users className="h-6 w-6 text-blue-500" />
              </div>
              <div>
                <h2 className="font-mono text-lg font-semibold text-foreground">
                  Employee Portal
                </h2>
                <p className="font-mono text-xs text-muted-foreground">
                  Chat with AI Assistant
                </p>
              </div>
            </div>
            <p className="font-mono text-sm text-muted-foreground">
              Access your AI chat assistant and view your conversation history.
            </p>
          </Card>

          <Card 
            className="cursor-pointer border-border p-6 transition-all hover:border-primary hover:shadow-lg"
            onClick={() => router.push("/employer")}
          >
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-lg bg-purple-500/10 p-3">
                <Shield className="h-6 w-6 text-purple-500" />
              </div>
              <div>
                <h2 className="font-mono text-lg font-semibold text-foreground">
                  Employer Dashboard
                </h2>
                <p className="font-mono text-xs text-muted-foreground">
                  Monitor & Review
                </p>
              </div>
            </div>
            <p className="font-mono text-sm text-muted-foreground">
              Monitor employee conversations, review flagged messages, and manage security.
            </p>
          </Card>
        </div>

        <div className="mt-8 rounded-lg border border-border bg-muted/30 p-4">
          <p className="font-mono text-xs text-muted-foreground">
            <strong className="text-foreground">Demo Mode:</strong> In production, authentication would automatically route users based on their role.
          </p>
        </div>
      </div>
    </div>
  )
}
