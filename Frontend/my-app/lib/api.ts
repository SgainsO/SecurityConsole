const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Message {
  id: string
  employee_id: string
  prompt: string
  response?: string
  session_id?: string
  metadata?: Record<string, any>
  status: 'SAFE' | 'FLAG' | 'BLOCKED'
  created_at: string
  updated_at: string
}

export interface MessageCreate {
  user_id: string
  prompt: string
  response?: string
  session_id?: string
  metadata?: Record<string, any>
}

export interface SetStatusRequest {
  status: 'SAFE' | 'FLAG' | 'BLOCKED'
}

export interface BulkStatusRequest {
  message_ids: string[]
  status: 'SAFE' | 'FLAG' | 'BLOCKED'
}

export interface MessageStatistics {
  total_messages: number
  safe_messages: number
  flagged_messages: number
  blocked_messages: number
  flagged_percentage: number
  blocked_percentage: number
  top_flagged_employees: Array<{
    employee_id: string
    count: number
  }>
  top_blocked_employees: Array<{
    employee_id: string
    count: number
  }>
  recent_flags: Array<{
    message_id: string
    employee_id: string
    flagged_at: string
  }>
}

// Create a new message
export async function createMessage(data: MessageCreate): Promise<Message> {
  const response = await fetch(`${API_BASE_URL}/api/messages/user_messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error('Failed to create message')
  }

  return response.json()
}

// Set message status (FLAG, BLOCKED, SAFE)
export async function setMessageStatus(messageId: string, status: 'SAFE' | 'FLAG' | 'BLOCKED'): Promise<Message> {
  const response = await fetch(`${API_BASE_URL}/api/messages/${messageId}/status`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ status }),
  })

  if (!response.ok) {
    throw new Error('Failed to update message status')
  }

  return response.json()
}

// Get all flagged messages (for manual review)
export async function getFlaggedMessages(): Promise<Message[]> {
  const response = await fetch(`${API_BASE_URL}/api/messages/flagged/manual-review`)

  if (!response.ok) {
    throw new Error('Failed to fetch flagged messages')
  }

  return response.json()
}

// Get messages by status
export async function getMessagesByStatus(status: 'SAFE' | 'FLAG' | 'BLOCKED'): Promise<Message[]> {
  const response = await fetch(`${API_BASE_URL}/api/messages/status/${status}`)

  if (!response.ok) {
    throw new Error('Failed to fetch messages')
  }

  return response.json()
}

// Get all messages with optional filters
export async function getAllMessages(params?: {
  employee_id?: string
  session_id?: string
  status?: 'SAFE' | 'FLAG' | 'BLOCKED'
  skip?: number
  limit?: number
}): Promise<Message[]> {
  const queryParams = new URLSearchParams()

  if (params?.employee_id) queryParams.append('employee_id', params.employee_id)
  if (params?.session_id) queryParams.append('session_id', params.session_id)
  if (params?.status) queryParams.append('status', params.status)
  if (params?.skip) queryParams.append('skip', params.skip.toString())
  if (params?.limit) queryParams.append('limit', params.limit.toString())

  const response = await fetch(
    `${API_BASE_URL}/api/messages/?${queryParams.toString()}`
  )

  if (!response.ok) {
    throw new Error('Failed to fetch messages')
  }

  return response.json()
}

// Get employee messages
export async function getEmployeeMessages(employeeId: string): Promise<Message[]> {
  const response = await fetch(`${API_BASE_URL}/api/messages/employee/${employeeId}`)

  if (!response.ok) {
    throw new Error('Failed to fetch employee messages')
  }

  return response.json()
}

// Get session messages
export async function getSessionMessages(sessionId: string): Promise<Message[]> {
  const response = await fetch(`${API_BASE_URL}/api/messages/session/${sessionId}`)

  if (!response.ok) {
    throw new Error('Failed to fetch session messages')
  }

  return response.json()
}

// Bulk update message status
export async function bulkSetStatus(data: BulkStatusRequest): Promise<{
  success: boolean
  modified_count: number
  matched_count: number
  status: string
}> {
  const response = await fetch(`${API_BASE_URL}/api/messages/status/bulk`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error('Failed to bulk update status')
  }

  return response.json()
}

// Get statistics
export async function getStatistics(): Promise<MessageStatistics> {
  const response = await fetch(`${API_BASE_URL}/api/messages/analytics/statistics`)

  if (!response.ok) {
    throw new Error('Failed to fetch statistics')
  }

  return response.json()
}

