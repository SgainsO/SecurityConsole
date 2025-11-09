from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
import logging

from database.connection import get_database
from models.message import MessageStatus

# Configure logging
logger = logging.getLogger(__name__)

# Import the security agents
import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
sys.path.insert(0, str(root_dir))

try:
    from services.cloud_agent.agent import process_prompt, gemini_client
except ImportError:
    print("Warning: Could not import cloud agent")
    process_prompt = None
    gemini_client = None


router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    employee_id: str
    message: str
    session_id: Optional[str] = None
    metadata: Optional[dict] = None


class ChatResponse(BaseModel):
    message_id: str
    employee_id: str
    prompt: str
    response: str
    status: MessageStatus
    session_id: Optional[str] = None
    created_at: datetime
    security_info: Optional[dict] = None


@router.post("/send", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """
    Send a chat message from employee to LLM.
    - Runs security checks
    - Gets LLM response if safe
    - Logs everything to database
    - Returns response to employee
    """
    db = await get_database()
    
    # Generate session ID if not provided
    session_id = request.session_id or f"session_{request.employee_id}_{int(datetime.utcnow().timestamp())}"
    
    # Step 1: Run on-premise security checks (PII, SLM, Malicious)
    # For now, we'll assume ACCEPT status - you can integrate the on_premise_agent here
    initial_pii_status = "ACCEPT"
    initial_slm_flag = "ACCEPT"
    initial_malicious_flag = "ACCEPT"
    
    # TODO: Integrate with on_premise_agent for real checks
    # try:
    #     from on_premise_agent import check_query
    #     security_check = await check_query(request.message)
    #     initial_pii_status = security_check.pii_status
    #     initial_slm_flag = security_check.slm_flag
    #     initial_malicious_flag = security_check.malicious_flag
    # except Exception as e:
    #     logger.error(f"Security check failed: {e}")
    
    # Step 2: If blocked by PII, return immediately
    if initial_pii_status == "BLOCK":
        # Log blocked message
        message_dict = {
            "employee_id": request.employee_id,
            "prompt": request.message,
            "response": "Message blocked due to PII detection",
            "session_id": session_id,
            "metadata": {
                **(request.metadata or {}),
                "security_check": {
                    "pii_status": initial_pii_status,
                    "slm_flag": initial_slm_flag,
                    "malicious_flag": initial_malicious_flag
                }
            },
            "status": MessageStatus.BLOCKED.value,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        result = await db.messages.insert_one(message_dict)
        new_message = await db.messages.find_one({"_id": result.inserted_id})
        
        return ChatResponse(
            message_id=str(new_message["_id"]),
            employee_id=request.employee_id,
            prompt=request.message,
            response="Message blocked due to PII detection",
            status=MessageStatus.BLOCKED,
            session_id=session_id,
            created_at=new_message["created_at"],
            security_info={
                "pii_status": initial_pii_status,
                "reason": "PII detected in message"
            }
        )
    
    # Step 3: Process through cloud agent for second opinion and response generation
    llm_response = ""
    final_status = MessageStatus.SAFE
    security_details = {}
    
    try:
        if process_prompt and gemini_client:
            # Use cloud agent for security validation and response
            toolkit_response = await process_prompt(
                prompt=request.message,
                pii_status=initial_pii_status,
                slm_flag=initial_slm_flag,
                malicious_flag=initial_malicious_flag
            )
            
            # Determine status based on toolkit response
            if toolkit_response.status == "BLOCKED":
                final_status = MessageStatus.BLOCKED
                llm_response = "Your message has been blocked due to security concerns."
            elif toolkit_response.status == "FLAGGED":
                final_status = MessageStatus.FLAG
                llm_response = toolkit_response.final_response or "Your message has been flagged for review."
            elif toolkit_response.status == "POSSIBLE_HALLUCINATION":
                final_status = MessageStatus.FLAG
                llm_response = toolkit_response.final_response or "Response generated (flagged for quality review)."
            else:  # SUCCESS
                final_status = MessageStatus.SAFE
                llm_response = toolkit_response.final_response or "Response generated successfully."
            
            security_details = {
                "toolkit_status": toolkit_response.status,
                "details": toolkit_response.details,
                "pii_status": initial_pii_status,
                "slm_flag": initial_slm_flag,
                "malicious_flag": initial_malicious_flag
            }
            
            if toolkit_response.discrepancy_report:
                security_details["discrepancy_report"] = toolkit_response.discrepancy_report.dict()
        else:
            # Fallback to simple Gemini response if cloud agent not available
            if gemini_client:
                llm_response = await gemini_client.get_llm_response(request.message)
                final_status = MessageStatus.SAFE
            else:
                llm_response = "LLM service is currently unavailable. Please try again later."
                final_status = MessageStatus.FLAG
    
    except Exception as e:
        logger.error(f"LLM processing failed: {e}")
        llm_response = "An error occurred while processing your message."
        final_status = MessageStatus.FLAG
        security_details["error"] = str(e)
    
    # Step 4: Log message to database
    message_dict = {
        "employee_id": request.employee_id,
        "prompt": request.message,
        "response": llm_response,
        "session_id": session_id,
        "metadata": {
            **(request.metadata or {}),
            "security_check": security_details
        },
        "status": final_status.value,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    result = await db.messages.insert_one(message_dict)
    new_message = await db.messages.find_one({"_id": result.inserted_id})
    
    # Step 5: Return response
    return ChatResponse(
        message_id=str(new_message["_id"]),
        employee_id=request.employee_id,
        prompt=request.message,
        response=llm_response,
        status=final_status,
        session_id=session_id,
        created_at=new_message["created_at"],
        security_info=security_details if security_details else None
    )


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Get full chat history for a session.
    Returns messages in chronological order.
    """
    db = await get_database()
    
    messages = []
    cursor = db.messages.find({"session_id": session_id}).sort("created_at", 1)
    
    async for message in cursor:
        messages.append({
            "id": str(message["_id"]),
            "employee_id": message["employee_id"],
            "prompt": message["prompt"],
            "response": message.get("response"),
            "status": message.get("status", MessageStatus.SAFE.value),
            "created_at": message["created_at"].isoformat(),
            "metadata": message.get("metadata")
        })
    
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "messages": messages
    }

