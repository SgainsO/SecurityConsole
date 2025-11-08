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
    FlagMessageRequest,
    ReviewMessageRequest,
    BulkFlagRequest,
    FlagStatistics
)


router = APIRouter(prefix="/api/messages", tags=["messages"])


def message_helper(message) -> dict:
    return {
        "id": str(message["_id"]),
        "employee_id": message["employee_id"],
        "employee_name": message["employee_name"],
        "prompt": message["prompt"],
        "response": message.get("response"),
        "session_id": message.get("session_id"),
        "model_name": message.get("model_name"),
        "metadata": message.get("metadata"),
        "needs_review": message.get("needs_review", False),
        "is_flagged": message.get("is_flagged", False),
        "flag_reason": message.get("flag_reason"),
        "reviewed_by": message.get("reviewed_by"),
        "reviewed_at": message.get("reviewed_at"),
        "created_at": message["created_at"],
        "updated_at": message["updated_at"],
    }


@router.post("/user_messages", response_model=MessageResponse, status_code=201)
async def upload_user_message(request: UserMessageRequest):
    db = await get_database()
    
    message_dict = {
        "employee_id": request.user_id,
        "employee_name": request.employee_name or f"User {request.user_id}",
        "prompt": request.prompt,
        "response": request.response,
        "session_id": request.session_id,
        "model_name": request.model_name,
        "metadata": request.metadata,
        "needs_review": False,
        "is_flagged": False,
        "flag_reason": None,
        "reviewed_by": None,
        "reviewed_at": None,
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
    message_dict["needs_review"] = False
    message_dict["is_flagged"] = False
    message_dict["flag_reason"] = None
    message_dict["reviewed_by"] = None
    message_dict["reviewed_at"] = None
    message_dict["created_at"] = datetime.utcnow()
    message_dict["updated_at"] = datetime.utcnow()
    
    result = await db.messages.insert_one(message_dict)
    
    new_message = await db.messages.find_one({"_id": result.inserted_id})
    
    return message_helper(new_message)


@router.get("/", response_model=List[MessageResponse])
async def get_all_messages(
    employee_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    needs_review: Optional[bool] = Query(None),
    is_flagged: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    db = await get_database()
    
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if session_id:
        query["session_id"] = session_id
    if needs_review is not None:
        query["needs_review"] = needs_review
    if is_flagged is not None:
        query["is_flagged"] = is_flagged
    
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
    
    update_dict = {k: v for k, v in update_data.model_dump(exclude_unset=True).items() if v is not None}
    
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


@router.post("/{message_id}/flag", response_model=MessageResponse)
async def flag_message(message_id: str, flag_data: FlagMessageRequest):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=400, detail="Invalid message ID format")
    
    db = await get_database()
    
    update_dict = {
        "is_flagged": flag_data.is_flagged,
        "updated_at": datetime.utcnow()
    }
    
    if flag_data.flag_reason:
        update_dict["flag_reason"] = flag_data.flag_reason
    elif not flag_data.is_flagged:
        update_dict["flag_reason"] = None
    
    if flag_data.reviewed_by:
        update_dict["reviewed_by"] = flag_data.reviewed_by
        update_dict["reviewed_at"] = datetime.utcnow()
    
    result = await db.messages.update_one(
        {"_id": ObjectId(message_id)},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    
    updated_message = await db.messages.find_one({"_id": ObjectId(message_id)})
    return message_helper(updated_message)


@router.post("/{message_id}/review", response_model=MessageResponse)
async def review_message(message_id: str, review_data: ReviewMessageRequest):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=400, detail="Invalid message ID format")
    
    db = await get_database()
    
    update_dict = {
        "needs_review": review_data.needs_review,
        "reviewed_by": review_data.reviewed_by,
        "reviewed_at": datetime.utcnow(),
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


@router.get("/flagged/all", response_model=List[MessageResponse])
async def get_flagged_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    db = await get_database()
    
    messages = []
    cursor = db.messages.find({"is_flagged": True}).sort("created_at", -1).skip(skip).limit(limit)
    
    async for message in cursor:
        messages.append(message_helper(message))
    
    return messages


@router.get("/review/pending", response_model=List[MessageResponse])
async def get_messages_needing_review(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    db = await get_database()
    
    messages = []
    cursor = db.messages.find({"needs_review": True}).sort("created_at", -1).skip(skip).limit(limit)
    
    async for message in cursor:
        messages.append(message_helper(message))
    
    return messages


@router.delete("/{message_id}", status_code=204)
async def delete_message(message_id: str):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=400, detail="Invalid message ID format")
    
    db = await get_database()
    
    result = await db.messages.delete_one({"_id": ObjectId(message_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return None


@router.post("/flag/bulk", response_model=dict)
async def bulk_flag_messages(bulk_flag: BulkFlagRequest):
    db = await get_database()
    
    valid_ids = []
    for msg_id in bulk_flag.message_ids:
        if ObjectId.is_valid(msg_id):
            valid_ids.append(ObjectId(msg_id))
    
    if not valid_ids:
        raise HTTPException(status_code=400, detail="No valid message IDs provided")
    
    update_dict = {
        "is_flagged": bulk_flag.is_flagged,
        "reviewed_by": bulk_flag.reviewed_by,
        "reviewed_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    if bulk_flag.flag_reason:
        update_dict["flag_reason"] = bulk_flag.flag_reason
    elif not bulk_flag.is_flagged:
        update_dict["flag_reason"] = None
    
    result = await db.messages.update_many(
        {"_id": {"$in": valid_ids}},
        {"$set": update_dict}
    )
    
    return {
        "success": True,
        "modified_count": result.modified_count,
        "matched_count": result.matched_count,
        "action": "flagged" if bulk_flag.is_flagged else "unflagged"
    }


@router.post("/{message_id}/unflag", response_model=MessageResponse)
async def unflag_message(message_id: str, reviewed_by: str = Query(...)):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=400, detail="Invalid message ID format")
    
    db = await get_database()
    
    update_dict = {
        "is_flagged": False,
        "flag_reason": None,
        "reviewed_by": reviewed_by,
        "reviewed_at": datetime.utcnow(),
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


@router.get("/flagged/employee/{employee_id}", response_model=List[MessageResponse])
async def get_flagged_messages_by_employee(
    employee_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    db = await get_database()
    
    messages = []
    cursor = db.messages.find({
        "employee_id": employee_id,
        "is_flagged": True
    }).sort("created_at", -1).skip(skip).limit(limit)
    
    async for message in cursor:
        messages.append(message_helper(message))
    
    return messages


@router.get("/analytics/flags", response_model=FlagStatistics)
async def get_flag_statistics():
    db = await get_database()
    
    total_messages = await db.messages.count_documents({})
    flagged_messages = await db.messages.count_documents({"is_flagged": True})
    needs_review = await db.messages.count_documents({"needs_review": True})
    
    flagged_percentage = (flagged_messages / total_messages * 100) if total_messages > 0 else 0.0
    
    top_flagged_pipeline = [
        {"$match": {"is_flagged": True}},
        {"$group": {
            "_id": "$employee_id",
            "employee_name": {"$first": "$employee_name"},
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
            "employee_name": emp["employee_name"],
            "flag_count": emp["flag_count"]
        })
    
    recent_flags_cursor = db.messages.find(
        {"is_flagged": True}
    ).sort("updated_at", -1).limit(10)
    
    recent_flags = []
    async for msg in recent_flags_cursor:
        recent_flags.append({
            "message_id": str(msg["_id"]),
            "employee_id": msg["employee_id"],
            "employee_name": msg["employee_name"],
            "flag_reason": msg.get("flag_reason"),
            "flagged_at": msg["updated_at"].isoformat() if msg.get("updated_at") else None
        })
    
    return FlagStatistics(
        total_messages=total_messages,
        flagged_messages=flagged_messages,
        needs_review=needs_review,
        flagged_percentage=round(flagged_percentage, 2),
        top_flagged_employees=top_flagged_employees,
        recent_flags=recent_flags
    )

