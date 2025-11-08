from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from database.connection import get_database
from models.message import (
    MessageCreate,
    MessageResponse,
    MessageUpdate,
    UserMessageRequest,
    SetMessageStatusRequest,
    BulkStatusRequest,
    MessageStatistics,
    MessageStatus
)


router = APIRouter(prefix="/api/messages", tags=["messages"])


def message_helper(message) -> dict:
    return {
        "id": str(message["_id"]),
        "employee_id": message["employee_id"],
        "prompt": message["prompt"],
        "response": message.get("response"),
        "session_id": message.get("session_id"),
        "metadata": message.get("metadata"),
        "status": message.get("status", MessageStatus.SAFE.value),
        "created_at": message["created_at"],
        "updated_at": message["updated_at"],
    }


@router.post("/user_messages", response_model=MessageResponse, status_code=201)
async def upload_user_message(request: UserMessageRequest):
    db = await get_database()
    
    message_dict = {
        "employee_id": request.user_id,
        "prompt": request.prompt,
        "response": request.response,
        "session_id": request.session_id,
        "metadata": request.metadata,
        "status": MessageStatus.SAFE.value,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    result = await db.messages.insert_one(message_dict)
    
    new_message = await db.messages.find_one({"_id": result.inserted_id})
    
    return message_helper(new_message)


@router.post("/", response_model=MessageResponse, status_code=201)
async def create_message(message: MessageCreate):
    db = await get_database()
    
    message_dict = message.model_dump()
    message_dict["status"] = MessageStatus.SAFE.value
    message_dict["created_at"] = datetime.utcnow()
    message_dict["updated_at"] = datetime.utcnow()
    
    result = await db.messages.insert_one(message_dict)
    
    new_message = await db.messages.find_one({"_id": result.inserted_id})
    
    return message_helper(new_message)


@router.get("/", response_model=List[MessageResponse])
async def get_all_messages(
    employee_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    status: Optional[MessageStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    db = await get_database()
    
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if session_id:
        query["session_id"] = session_id
    if status is not None:
        query["status"] = status.value
    
    messages = []
    cursor = db.messages.find(query).sort("created_at", -1).skip(skip).limit(limit)
    
    async for message in cursor:
        messages.append(message_helper(message))
    
    return messages


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(message_id: str):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=400, detail="Invalid message ID format")
    
    db = await get_database()
    message = await db.messages.find_one({"_id": ObjectId(message_id)})
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return message_helper(message)


@router.get("/employee/{employee_id}", response_model=List[MessageResponse])
async def get_employee_messages(
    employee_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    db = await get_database()
    
    messages = []
    cursor = db.messages.find({"employee_id": employee_id}).sort("created_at", -1).skip(skip).limit(limit)
    
    async for message in cursor:
        messages.append(message_helper(message))
    
    if not messages:
        raise HTTPException(status_code=404, detail=f"No messages found for employee {employee_id}")
    
    return messages


@router.get("/session/{session_id}", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    db = await get_database()
    
    messages = []
    cursor = db.messages.find({"session_id": session_id}).sort("created_at", 1).skip(skip).limit(limit)
    
    async for message in cursor:
        messages.append(message_helper(message))
    
    if not messages:
        raise HTTPException(status_code=404, detail=f"No messages found for session {session_id}")
    
    return messages


@router.patch("/{message_id}", response_model=MessageResponse)
async def update_message(message_id: str, update_data: MessageUpdate):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=400, detail="Invalid message ID format")
    
    db = await get_database()
    
    update_dict = {}
    for key, value in update_data.model_dump(exclude_unset=True).items():
        if value is not None:
            if key == "status":
                update_dict[key] = value.value
            else:
                update_dict[key] = value
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    update_dict["updated_at"] = datetime.utcnow()
    
    result = await db.messages.update_one(
        {"_id": ObjectId(message_id)},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    
    updated_message = await db.messages.find_one({"_id": ObjectId(message_id)})
    return message_helper(updated_message)


@router.post("/{message_id}/status", response_model=MessageResponse)
async def set_message_status(message_id: str, status_request: SetMessageStatusRequest):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=400, detail="Invalid message ID format")
    
    db = await get_database()
    
    update_dict = {
        "status": status_request.status.value,
        "updated_at": datetime.utcnow()
    }
    
    result = await db.messages.update_one(
        {"_id": ObjectId(message_id)},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    
    updated_message = await db.messages.find_one({"_id": ObjectId(message_id)})
    return message_helper(updated_message)


@router.post("/status/bulk", response_model=dict)
async def bulk_set_status(bulk_request: BulkStatusRequest):
    db = await get_database()
    
    valid_ids = []
    for msg_id in bulk_request.message_ids:
        if ObjectId.is_valid(msg_id):
            valid_ids.append(ObjectId(msg_id))
    
    if not valid_ids:
        raise HTTPException(status_code=400, detail="No valid message IDs provided")
    
    update_dict = {
        "status": bulk_request.status.value,
        "updated_at": datetime.utcnow()
    }
    
    result = await db.messages.update_many(
        {"_id": {"$in": valid_ids}},
        {"$set": update_dict}
    )
    
    return {
        "success": True,
        "modified_count": result.modified_count,
        "matched_count": result.matched_count,
        "status": bulk_request.status.value
    }


@router.get("/flagged/manual-review", response_model=List[MessageResponse])
async def get_flagged_for_manual_review(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get all messages with FLAG status that require manual review by employer.
    These are messages that have been flagged but not yet reviewed/blocked.
    """
    db = await get_database()
    
    messages = []
    cursor = db.messages.find({"status": MessageStatus.FLAG.value}).sort("created_at", -1).skip(skip).limit(limit)
    
    async for message in cursor:
        messages.append(message_helper(message))
    
    return messages


@router.get("/status/{status_type}", response_model=List[MessageResponse])
async def get_messages_by_status(
    status_type: MessageStatus,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get all messages with a specific status (SAFE, FLAG, or BLOCKED).
    """
    db = await get_database()
    
    messages = []
    cursor = db.messages.find({"status": status_type.value}).sort("created_at", -1).skip(skip).limit(limit)
    
    async for message in cursor:
        messages.append(message_helper(message))
    
    return messages


@router.get("/employee/{employee_id}/status/{status_type}", response_model=List[MessageResponse])
async def get_employee_messages_by_status(
    employee_id: str,
    status_type: MessageStatus,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get all messages for a specific employee filtered by status.
    """
    db = await get_database()
    
    messages = []
    cursor = db.messages.find({
        "employee_id": employee_id,
        "status": status_type.value
    }).sort("created_at", -1).skip(skip).limit(limit)
    
    async for message in cursor:
        messages.append(message_helper(message))
    
    return messages


@router.get("/analytics/statistics", response_model=MessageStatistics)
async def get_message_statistics():
    """
    Get comprehensive statistics about message statuses.
    """
    db = await get_database()
    
    total_messages = await db.messages.count_documents({})
    safe_messages = await db.messages.count_documents({"status": MessageStatus.SAFE.value})
    flagged_messages = await db.messages.count_documents({"status": MessageStatus.FLAG.value})
    blocked_messages = await db.messages.count_documents({"status": MessageStatus.BLOCKED.value})
    
    flagged_percentage = (flagged_messages / total_messages * 100) if total_messages > 0 else 0.0
    blocked_percentage = (blocked_messages / total_messages * 100) if total_messages > 0 else 0.0
    
    # Top flagged employees
    top_flagged_pipeline = [
        {"$match": {"status": MessageStatus.FLAG.value}},
        {"$group": {
            "_id": "$employee_id",
            "flag_count": {"$sum": 1}
        }},
        {"$sort": {"flag_count": -1}},
        {"$limit": 10}
    ]
    
    top_flagged_cursor = db.messages.aggregate(top_flagged_pipeline)
    top_flagged_employees = []
    async for emp in top_flagged_cursor:
        top_flagged_employees.append({
            "employee_id": emp["_id"],
            "count": emp["flag_count"]
        })
    
    # Top blocked employees
    top_blocked_pipeline = [
        {"$match": {"status": MessageStatus.BLOCKED.value}},
        {"$group": {
            "_id": "$employee_id",
            "blocked_count": {"$sum": 1}
        }},
        {"$sort": {"blocked_count": -1}},
        {"$limit": 10}
    ]
    
    top_blocked_cursor = db.messages.aggregate(top_blocked_pipeline)
    top_blocked_employees = []
    async for emp in top_blocked_cursor:
        top_blocked_employees.append({
            "employee_id": emp["_id"],
            "count": emp["blocked_count"]
        })
    
    # Recent flags
    recent_flags_cursor = db.messages.find(
        {"status": MessageStatus.FLAG.value}
    ).sort("updated_at", -1).limit(10)
    
    recent_flags = []
    async for msg in recent_flags_cursor:
        recent_flags.append({
            "message_id": str(msg["_id"]),
            "employee_id": msg["employee_id"],
            "flagged_at": msg["updated_at"].isoformat() if msg.get("updated_at") else None
        })
    
    return MessageStatistics(
        total_messages=total_messages,
        safe_messages=safe_messages,
        flagged_messages=flagged_messages,
        blocked_messages=blocked_messages,
        flagged_percentage=round(flagged_percentage, 2),
        blocked_percentage=round(blocked_percentage, 2),
        top_flagged_employees=top_flagged_employees,
        top_blocked_employees=top_blocked_employees,
        recent_flags=recent_flags
    )


@router.delete("/{message_id}", status_code=204)
async def delete_message(message_id: str):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=400, detail="Invalid message ID format")
    
    db = await get_database()
    
    result = await db.messages.delete_one({"_id": ObjectId(message_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return None
