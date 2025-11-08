"use client"

import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export function SettingsView() {
  return (
    <div className="h-full p-6">
      <div className="mb-6">
        <h2 className="mb-2 text-2xl font-semibold">Settings</h2>
        <p className="text-sm text-muted-foreground">Configure monitoring rules and notification preferences</p>
      </div>

      <div className="space-y-6">
        <Card className="p-6">
          <h3 className="mb-4 text-lg font-medium">Monitoring Rules</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="sensitive-data">Flag sensitive data requests</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically flag conversations requesting SSN, credit cards, or passwords
                </p>
              </div>
              <Switch id="sensitive-data" defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="security-bypass">Flag security bypass attempts</Label>
                <p className="text-sm text-muted-foreground">
                  Flag conversations attempting to bypass authentication or security measures
                </p>
              </div>
              <Switch id="security-bypass" defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="confidential">Flag confidential info sharing</Label>
                <p className="text-sm text-muted-foreground">
                  Flag attempts to share confidential company information externally
                </p>
              </div>
              <Switch id="confidential" defaultChecked />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="mb-4 text-lg font-medium">Notifications</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="email-alerts">Email alerts for flagged conversations</Label>
                <p className="text-sm text-muted-foreground">
                  Receive email notifications when conversations are flagged
                </p>
              </div>
              <Switch id="email-alerts" defaultChecked />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Alert email address</Label>
              <Input id="email" type="email" placeholder="admin@company.com" defaultValue="admin@company.com" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="mb-4 text-lg font-medium">Data Retention</h3>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="retention">Conversation retention period (days)</Label>
              <Input id="retention" type="number" defaultValue="90" />
              <p className="text-sm text-muted-foreground">
                Conversations older than this will be automatically archived
              </p>
            </div>
          </div>
        </Card>

        <div className="flex justify-end">
          <Button>Save Settings</Button>
        </div>
      </div>
    </div>
  )
}
