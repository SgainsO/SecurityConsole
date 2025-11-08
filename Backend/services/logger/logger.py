"""
Incident Reporting Logger Service.
Single entry point for uploading messages/incidents to MongoDB.
Encapsulates the log_message format from db_service.
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add parent directories to path for imports
current_dir = Path(__file__).resolve().parent
new_backend_dir = current_dir.parent.parent
sys.path.insert(0, str(new_backend_dir))

from database.connection import get_database


async def log_incident(
    employee_id: str,
    text: str,
    response: Optional[str] = None,
    status: str = "ACCEPT",
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Log an incident/message to MongoDB.
    
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

