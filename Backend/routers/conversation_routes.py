from fastapi import APIRouter, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from database.connection import get_database
from models.message import MessageStatus


router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class ConversationSummary(BaseModel):
    session_id: str
    employee_id: str
    message_count: int
    safe_count: int
    flagged_count: int
    blocked_count: int
    first_message_at: datetime
    last_message_at: datetime
    latest_prompt: Optional[str] = None


class ConversationDetail(BaseModel):
    session_id: str
    employee_id: str
    messages: List[dict]
    statistics: dict


@router.get("/", response_model=List[ConversationSummary])
async def get_all_conversations(
    employee_id: Optional[str] = Query(None),
    has_flags: Optional[bool] = Query(None),
    has_blocks: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get all conversations (grouped by session_id) with summary statistics.
    
    Query Parameters:
    - employee_id: Filter by specific employee
    - has_flags: Filter conversations that have flagged messages
    - has_blocks: Filter conversations that have blocked messages
    - skip: Pagination offset
    - limit: Max results to return
    """
    db = await get_database()
    
    # Build aggregation pipeline
    match_stage = {
        "session_id": {"$ne": None}  # Exclude messages without session_id
    }
    if employee_id:
        match_stage["employee_id"] = employee_id
    
    pipeline = [{"$match": match_stage}]
    
    # Group by session_id and calculate statistics
    pipeline.extend([
        {
            "$group": {
                "_id": "$session_id",
                "employee_id": {"$first": "$employee_id"},
                "message_count": {"$sum": 1},
                "safe_count": {
                    "$sum": {"$cond": [{"$eq": ["$status", MessageStatus.SAFE.value]}, 1, 0]}
                },
                "flagged_count": {
                    "$sum": {"$cond": [{"$eq": ["$status", MessageStatus.FLAG.value]}, 1, 0]}
                },
                "blocked_count": {
                    "$sum": {"$cond": [{"$eq": ["$status", MessageStatus.BLOCKED.value]}, 1, 0]}
                },
                "first_message_at": {"$min": "$created_at"},
                "last_message_at": {"$max": "$created_at"},
                "latest_prompt": {"$last": "$prompt"}
            }
        },
        {"$sort": {"last_message_at": -1}},
        {"$skip": skip},
        {"$limit": limit}
    ])
    
    # Execute aggregation
    cursor = db.messages.aggregate(pipeline)
    conversations = []
    
    async for conv in cursor:
        # Apply optional filters
        if has_flags is not None:
            if has_flags and conv["flagged_count"] == 0:
                continue
            if not has_flags and conv["flagged_count"] > 0:
                continue
        
        if has_blocks is not None:
            if has_blocks and conv["blocked_count"] == 0:
                continue
            if not has_blocks and conv["blocked_count"] > 0:
                continue
        
        conversations.append(ConversationSummary(
            session_id=conv["_id"],
            employee_id=conv["employee_id"],
            message_count=conv["message_count"],
            safe_count=conv["safe_count"],
            flagged_count=conv["flagged_count"],
            blocked_count=conv["blocked_count"],
            first_message_at=conv["first_message_at"],
            last_message_at=conv["last_message_at"],
            latest_prompt=conv.get("latest_prompt")
        ))
    
    return conversations


@router.get("/{session_id}", response_model=ConversationDetail)
async def get_conversation_detail(session_id: str):
    """
    Get detailed view of a specific conversation including all messages.
    """
    db = await get_database()
    
    # Get all messages in this conversation
    messages = []
    cursor = db.messages.find({"session_id": session_id}).sort("created_at", 1)
    
    employee_id = None
    status_counts = {
        MessageStatus.SAFE.value: 0,
        MessageStatus.FLAG.value: 0,
        MessageStatus.BLOCKED.value: 0
    }
    
    async for message in cursor:
        if not employee_id:
            employee_id = message["employee_id"]
        
        status_counts[message.get("status", MessageStatus.SAFE.value)] += 1
        
        messages.append({
            "id": str(message["_id"]),
            "prompt": message["prompt"],
            "response": message.get("response"),
            "status": message.get("status", MessageStatus.SAFE.value),
            "created_at": message["created_at"].isoformat(),
            "metadata": message.get("metadata")
        })
    
    if not messages:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Conversation {session_id} not found")
    
    statistics = {
        "total_messages": len(messages),
        "safe_messages": status_counts[MessageStatus.SAFE.value],
        "flagged_messages": status_counts[MessageStatus.FLAG.value],
        "blocked_messages": status_counts[MessageStatus.BLOCKED.value],
        "first_message_at": messages[0]["created_at"],
        "last_message_at": messages[-1]["created_at"]
    }
    
    return ConversationDetail(
        session_id=session_id,
        employee_id=employee_id,
        messages=messages,
        statistics=statistics
    )


@router.get("/employee/{employee_id}/sessions", response_model=List[dict])
async def get_employee_sessions(
    employee_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
):
    """
    Get all session IDs for a specific employee with basic info.
    Useful for sidebar/dropdown of conversations.
    """
    db = await get_database()
    
    pipeline = [
        {"$match": {"employee_id": employee_id}},
        {
            "$group": {
                "_id": "$session_id",
                "message_count": {"$sum": 1},
                "last_message_at": {"$max": "$created_at"},
                "has_flags": {
                    "$sum": {"$cond": [{"$eq": ["$status", MessageStatus.FLAG.value]}, 1, 0]}
                },
                "has_blocks": {
                    "$sum": {"$cond": [{"$eq": ["$status", MessageStatus.BLOCKED.value]}, 1, 0]}
                }
            }
        },
        {"$sort": {"last_message_at": -1}},
        {"$skip": skip},
        {"$limit": limit}
    ]
    
    cursor = db.messages.aggregate(pipeline)
    sessions = []
    
    async for session in cursor:
        sessions.append({
            "session_id": session["_id"],
            "message_count": session["message_count"],
            "last_message_at": session["last_message_at"].isoformat(),
            "has_flags": session["has_flags"] > 0,
            "has_blocks": session["has_blocks"] > 0
        })
    
    return sessions

