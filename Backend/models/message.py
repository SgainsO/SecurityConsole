from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class MessageStatus(str, Enum):
    SAFE = "SAFE"
    FLAG = "FLAG"
    BLOCKED = "BLOCKED"


class MessageBase(BaseModel):
    employee_id: str
    prompt: str
    response: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[dict] = None


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    response: Optional[str] = None
    status: Optional[MessageStatus] = None
    metadata: Optional[dict] = None


class MessageResponse(MessageBase):
    id: str
    status: MessageStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserMessageRequest(BaseModel):
    user_id: str
    prompt: str
    session_id: Optional[str] = None
    response: Optional[str] = None
    metadata: Optional[dict] = None


class SetMessageStatusRequest(BaseModel):
    status: MessageStatus


class BulkStatusRequest(BaseModel):
    message_ids: list[str]
    status: MessageStatus


class MessageStatistics(BaseModel):
    total_messages: int
    safe_messages: int
    flagged_messages: int
    blocked_messages: int
    flagged_percentage: float
    blocked_percentage: float
    top_flagged_employees: list[dict]
    top_blocked_employees: list[dict]
    recent_flags: list[dict]
