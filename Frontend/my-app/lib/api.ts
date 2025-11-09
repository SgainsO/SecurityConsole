const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://45.32.58.116:8000'

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

// ============== CHAT ENDPOINTS ==============

export interface ChatRequest {
  employee_id: string
  message: string
  session_id?: string
  metadata?: Record<string, any>
}

export interface ChatResponse {
  message_id: string
  employee_id: string
  prompt: string
  response: string
  status: 'SAFE' | 'FLAG' | 'BLOCKED'
  session_id?: string
  created_at: string
  security_info?: Record<string, any>
}

// Send a chat message to the LLM
export async function sendChatMessage(data: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/send`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error('Failed to send chat message')
  }

  return response.json()
}

// Get chat history for a session
export async function getChatHistory(sessionId: string): Promise<{
  session_id: string
  message_count: number
  messages: Array<{
    id: string
    employee_id: string
    prompt: string
    response?: string
    status: string
    created_at: string
    metadata?: Record<string, any>
  }>
}> {
  const response = await fetch(`${API_BASE_URL}/api/chat/history/${sessionId}`)

  if (!response.ok) {
    throw new Error('Failed to fetch chat history')
  }

  return response.json()
}

// ============== CONVERSATION ENDPOINTS ==============

export interface ConversationSummary {
  session_id: string
  employee_id: string
  message_count: number
  safe_count: number
  flagged_count: number
  blocked_count: number
  first_message_at: string
  last_message_at: string
  latest_prompt?: string
}

export interface ConversationDetail {
  session_id: string
  employee_id: string
  messages: Array<{
    id: string
    prompt: string
    response?: string
    status: string
    created_at: string
    metadata?: Record<string, any>
  }>
  statistics: {
    total_messages: number
    safe_messages: number
    flagged_messages: number
    blocked_messages: number
    first_message_at: string
    last_message_at: string
  }
}

// Get all conversations with optional filters
export async function getConversations(params?: {
  employee_id?: string
  has_flags?: boolean
  has_blocks?: boolean
  skip?: number
  limit?: number
}): Promise<ConversationSummary[]> {
  const queryParams = new URLSearchParams()

  if (params?.employee_id) queryParams.append('employee_id', params.employee_id)
  if (params?.has_flags !== undefined) queryParams.append('has_flags', params.has_flags.toString())
  if (params?.has_blocks !== undefined) queryParams.append('has_blocks', params.has_blocks.toString())
  if (params?.skip) queryParams.append('skip', params.skip.toString())
  if (params?.limit) queryParams.append('limit', params.limit.toString())

  const response = await fetch(
    `${API_BASE_URL}/api/conversations/?${queryParams.toString()}`
  )

  if (!response.ok) {
    throw new Error('Failed to fetch conversations')
  }

  return response.json()
}

// Get detailed conversation by session ID
export async function getConversationDetail(sessionId: string): Promise<ConversationDetail> {
  const response = await fetch(`${API_BASE_URL}/api/conversations/${sessionId}`)

  if (!response.ok) {
    throw new Error('Failed to fetch conversation detail')
  }

  return response.json()
}

// Get all sessions for an employee
export async function getEmployeeSessions(employeeId: string): Promise<Array<{
  session_id: string
  message_count: number
  last_message_at: string
  has_flags: boolean
  has_blocks: boolean
}>> {
  const response = await fetch(`${API_BASE_URL}/api/conversations/employee/${employeeId}/sessions`)

  if (!response.ok) {
    throw new Error('Failed to fetch employee sessions')
  }

  return response.json()
}

// ============== EMPLOYEE ENDPOINTS ==============

export interface EmployeeStatistics {
  employee_id: string
  total_messages: number
  safe_messages: number
  flagged_messages: number
  blocked_messages: number
  conversations_count: number
  risk_score: number
  last_activity: string
}

export interface EmployeeRiskSummary {
  total_employees: number
  high_risk: number
  medium_risk: number
  low_risk: number
}

// Get all employees with statistics
export async function getEmployees(params?: {
  min_risk?: number
  sort_by?: 'risk' | 'flags' | 'blocks' | 'total'
  skip?: number
  limit?: number
}): Promise<EmployeeStatistics[]> {
  const queryParams = new URLSearchParams()

  if (params?.min_risk !== undefined) queryParams.append('min_risk', params.min_risk.toString())
  if (params?.sort_by) queryParams.append('sort_by', params.sort_by)
  if (params?.skip) queryParams.append('skip', params.skip.toString())
  if (params?.limit) queryParams.append('limit', params.limit.toString())

  const response = await fetch(
    `${API_BASE_URL}/api/employees/?${queryParams.toString()}`
  )

  if (!response.ok) {
    throw new Error('Failed to fetch employees')
  }

  return response.json()
}

// Get detailed statistics for a specific employee
export async function getEmployeeDetail(employeeId: string): Promise<EmployeeStatistics> {
  const response = await fetch(`${API_BASE_URL}/api/employees/${employeeId}`)

  if (!response.ok) {
    throw new Error('Failed to fetch employee detail')
  }

  return response.json()
}

// Get employee risk level summary
export async function getEmployeeRiskSummary(): Promise<EmployeeRiskSummary> {
  const response = await fetch(`${API_BASE_URL}/api/employees/summary/risk-levels`)

  if (!response.ok) {
    throw new Error('Failed to fetch employee risk summary')
  }

  return response.json()
}

