"""
Database service for message logging and retrieval.
Status values: ACCEPT, FLAG, BLOCK
Functions: log_message (create), get_message_by_id (read by ID), get_messages_by_employee (read by employee), get_messages_by_status (read by status), get_messages_by_session (read by session), get_all_messages (read all), get_training_data (get untrained messages as {text, status}), mark_as_trained (mark messages as trained), update_message_status (update status), update_message_response (update response), delete_message (delete), get_message_count (count total)
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId

# Add parent directories to path for imports
current_dir = Path(__file__).resolve().parent
new_backend_dir = current_dir.parent.parent
sys.path.insert(0, str(new_backend_dir))

from database.connection import get_database


async def log_message(
    employee_id: str,
    text: str,
    response: Optional[str] = None,
    status: str = "ACCEPT",
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Log a message to the database.
    
    Args:
        employee_id: The ID of the employee
        text: The user's prompt/message text
        response: The AI response (optional)
        status: Message status (ACCEPT, FLAG, BLOCK)
        session_id: Optional session identifier
        metadata: Additional metadata dictionary
        
    Returns:
        The inserted message ID as a string
    """
    db = await get_database()
    messages_collection = db["messages"]
    
    now = datetime.utcnow()
    message_doc = {
        "employee_id": employee_id,
        "text": text,
        "response": response,
        "status": status,
        "session_id": session_id,
        "metadata": metadata or {},
        "is_trained": False,
        "created_at": now,
        "updated_at": now
    }
    
    result = await messages_collection.insert_one(message_doc)
    return str(result.inserted_id)


async def get_message_by_id(message_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single message by its ID.
    
    Args:
        message_id: The message ID to retrieve
        
    Returns:
        The message document or None if not found
    """
    db = await get_database()
    messages_collection = db["messages"]
    
    message = await messages_collection.find_one({"_id": ObjectId(message_id)})
    
    if message:
        message["id"] = str(message.pop("_id"))
    
    return message


async def get_messages_by_employee(
    employee_id: str,
    limit: int = 50,
    skip: int = 0
) -> List[Dict[str, Any]]:
    """
    Retrieve all messages for a specific employee.
    
    Args:
        employee_id: The employee ID to filter by
        limit: Maximum number of messages to return
        skip: Number of messages to skip (for pagination)
        
    Returns:
        List of message documents
    """
    db = await get_database()
    messages_collection = db["messages"]
    
    cursor = messages_collection.find(
        {"employee_id": employee_id}
    ).sort("created_at", -1).skip(skip).limit(limit)
    
    messages = await cursor.to_list(length=limit)
    
    for message in messages:
        message["id"] = str(message.pop("_id"))
    
    return messages


async def get_messages_by_status(
    status: str,
    limit: int = 50,
    skip: int = 0
) -> List[Dict[str, Any]]:
    """
    Retrieve all messages with a specific status.
    
    Args:
        status: The status to filter by (ACCEPT, FLAG, BLOCK)
        limit: Maximum number of messages to return
        skip: Number of messages to skip (for pagination)
        
    Returns:
        List of message documents
    """
    db = await get_database()
    messages_collection = db["messages"]
    
    cursor = messages_collection.find(
        {"status": status}
    ).sort("created_at", -1).skip(skip).limit(limit)
    
    messages = await cursor.to_list(length=limit)
    
    for message in messages:
        message["id"] = str(message.pop("_id"))
    
    return messages


async def get_messages_by_session(session_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all messages for a specific session.
    
    Args:
        session_id: The session ID to filter by
        
    Returns:
        List of message documents ordered by creation time
    """
    db = await get_database()
    messages_collection = db["messages"]
    
    cursor = messages_collection.find(
        {"session_id": session_id}
    ).sort("created_at", 1)
    
    messages = await cursor.to_list(length=None)
    
    for message in messages:
        message["id"] = str(message.pop("_id"))
    
    return messages


async def get_all_messages(
    limit: int = 100,
    skip: int = 0
) -> List[Dict[str, Any]]:
    """
    Retrieve all messages with pagination.
    
    Args:
        limit: Maximum number of messages to return
        skip: Number of messages to skip (for pagination)
        
    Returns:
        List of message documents
    """
    db = await get_database()
    messages_collection = db["messages"]
    
    cursor = messages_collection.find().sort("created_at", -1).skip(skip).limit(limit)
    
    messages = await cursor.to_list(length=limit)
    
    for message in messages:
        message["id"] = str(message.pop("_id"))
    
    return messages


async def update_message_status(message_id: str, status: str) -> bool:
    """
    Update the status of a message.
    
    Args:
        message_id: The message ID to update
        status: The new status (ACCEPT, FLAG, BLOCK)
        
    Returns:
        True if updated successfully, False otherwise
    """
    db = await get_database()
    messages_collection = db["messages"]
    
    result = await messages_collection.update_one(
        {"_id": ObjectId(message_id)},
        {
            "$set": {
                "status": status,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return result.modified_count > 0


async def update_message_response(message_id: str, response: str) -> bool:
    """
    Update the response of a message.
    
    Args:
        message_id: The message ID to update
        response: The AI response text
        
    Returns:
        True if updated successfully, False otherwise
    """
    db = await get_database()
    messages_collection = db["messages"]
    
    result = await messages_collection.update_one(
        {"_id": ObjectId(message_id)},
        {
            "$set": {
                "response": response,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return result.modified_count > 0


async def delete_message(message_id: str) -> bool:
    """
    Delete a message from the database.
    
    Args:
        message_id: The message ID to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    db = await get_database()
    messages_collection = db["messages"]
    
    result = await messages_collection.delete_one({"_id": ObjectId(message_id)})
    
    return result.deleted_count > 0


async def get_message_count() -> int:
    """
    Get the total count of messages in the database.
    
    Returns:
        Total number of messages
    """
    db = await get_database()
    messages_collection = db["messages"]
    
    return await messages_collection.count_documents({})


async def get_training_data(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
) -> List[Dict[str, str]]:
    """
    Get untrained messages in simplified format: {text: "...", status: "..."}
    Only returns messages where is_trained is False or doesn't exist.
    
    Args:
        employee_id: Optional employee ID to filter by
        status: Optional status to filter by (ACCEPT, FLAG, BLOCK)
        session_id: Optional session ID to filter by
        limit: Maximum number of messages to return
        skip: Number of messages to skip (for pagination)
        
    Returns:
        List of message dictionaries with only text and status fields
    """
    db = await get_database()
    messages_collection = db["messages"]
    
    # Build query filter - only get untrained messages
    query_filter = {
        "$or": [
            {"is_trained": False},
            {"is_trained": {"$exists": False}}
        ]
    }
    
    if employee_id:
        query_filter["employee_id"] = employee_id
    if status:
        query_filter["status"] = status
    if session_id:
        query_filter["session_id"] = session_id
    
    # Query with projection to only get text and status
    cursor = messages_collection.find(
        query_filter,
        {"text": 1, "status": 1, "_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit)
    
    messages = await cursor.to_list(length=limit)
    
    return messages


async def mark_as_trained(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    session_id: Optional[str] = None,
    message_ids: Optional[List[str]] = None
) -> int:
    """
    Mark messages as trained (is_trained = True).
    
    Args:
        employee_id: Optional - mark all messages for this employee
        status: Optional - mark all messages with this status
        session_id: Optional - mark all messages in this session
        message_ids: Optional - mark specific messages by ID
        
    Returns:
        Number of messages marked as trained
        
    Note: If no filters provided, does nothing for safety
    """
    db = await get_database()
    messages_collection = db["messages"]
    
    # Build query filter
    query_filter = {}
    
    if message_ids:
        # Mark specific messages by ID
        query_filter["_id"] = {"$in": [ObjectId(id) for id in message_ids]}
    else:
        # Build filter from other parameters
        if employee_id:
            query_filter["employee_id"] = employee_id
        if status:
            query_filter["status"] = status
        if session_id:
            query_filter["session_id"] = session_id
    
    # Safety check - don't mark everything as trained without filters
    if not query_filter:
        return 0
    
    # Only mark untrained messages
    query_filter["$or"] = [
        {"is_trained": False},
        {"is_trained": {"$exists": False}}
    ]
    
    result = await messages_collection.update_many(
        query_filter,
        {
            "$set": {
                "is_trained": True,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return result.modified_count

