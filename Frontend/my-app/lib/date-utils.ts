/**
 * Date formatting utilities for consistent timestamp handling across the application
 */

/**
 * Format a date string as a relative time (e.g., "5m ago", "2h ago", "Yesterday")
 * Handles timezone issues by treating negative differences as "Just now"
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  // Handle negative differences (future dates - likely timezone issues)
  if (diff < 0) {
    return "Just now"
  }
  
  if (minutes < 1) {
    return "Just now"
  }
  if (minutes < 60) {
    return `${minutes}m ago`
  }
  if (hours < 24) {
    return `${hours}h ago`
  }
  if (days === 1) {
    return "Yesterday"
  }
  if (days < 7) {
    return `${days}d ago`
  }
  if (days < 30) {
    const weeks = Math.floor(days / 7)
    return weeks === 1 ? "1 week ago" : `${weeks} weeks ago`
  }
  
  return date.toLocaleDateString([], { 
    month: "short", 
    day: "numeric", 
    year: now.getFullYear() !== date.getFullYear() ? "numeric" : undefined 
  })
}

/**
 * Format a date string as a full date (e.g., "Nov 9, 2025")
 */
export function formatFullDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString([], { 
    month: "short", 
    day: "numeric", 
    year: "numeric" 
  })
}

/**
 * Format a date string as a time (e.g., "02:45 PM")
 */
export function formatTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleTimeString([], { 
    hour: "2-digit", 
    minute: "2-digit" 
  })
}

/**
 * Format a date string as a full datetime (e.g., "Nov 9, 2025 at 02:45 PM")
 */
export function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString([], { 
    month: "short", 
    day: "numeric", 
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  })
}

