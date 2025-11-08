import * as React from "react"

type ToastProps = {
  title: string
  description?: string
  variant?: "default" | "destructive"
}

type ToastActionElement = React.ReactElement

export function useToast() {
  const toast = ({ title, description, variant }: ToastProps) => {
    // Simple console log for now - you can enhance this with a proper toast UI
    console.log(`[${variant || "default"}] ${title}: ${description || ""}`)
    
    // For now, use browser alert for visibility during testing
    if (variant === "destructive") {
      console.error(`${title}: ${description}`)
    } else {
      console.log(`${title}: ${description}`)
    }
  }

  return { toast }
}

