from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MessageBase(BaseModel):
    employee_id: str
    employee_name: str
    prompt: str
    response: Optional[str] = None
    session_id: Optional[str] = None
    model_name: Optional[str] = None
    metadata: Optional[dict] = None


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    response: Optional[str] = None
    needs_review: Optional[bool] = None
    is_flagged: Optional[bool] = None
    flag_reason: Optional[str] = None
    reviewed_by: Optional[str] = None
    metadata: Optional[dict] = None


class MessageResponse(MessageBase):
    id: str
    needs_review: bool
    is_flagged: bool
    flag_reason: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserMessageRequest(BaseModel):
    user_id: str
    prompt: str
    employee_name: Optional[str] = None
    session_id: Optional[str] = None
    model_name: Optional[str] = None
    response: Optional[str] = None
    metadata: Optional[dict] = None


class FlagMessageRequest(BaseModel):
    is_flagged: bool
    flag_reason: Optional[str] = None
    reviewed_by: Optional[str] = None


class ReviewMessageRequest(BaseModel):
    needs_review: bool
    reviewed_by: str


class BulkFlagRequest(BaseModel):
    message_ids: list[str]
    is_flagged: bool
    flag_reason: Optional[str] = None
    reviewed_by: str


class FlagStatistics(BaseModel):
    total_messages: int
    flagged_messages: int
    needs_review: int
    flagged_percentage: float
    top_flagged_employees: list[dict]
    recent_flags: list[dict]

