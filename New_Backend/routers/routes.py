import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Add parent directories to path for imports
current_dir = Path(__file__).resolve().parent
new_backend_dir = current_dir.parent
sys.path.insert(0, str(new_backend_dir))

from services.cloud_agent.agent import process_prompt, ToolkitResponse, DiscrepancyReport
from services.db_service.db import log_message
from config.config import settings


router = APIRouter(prefix="/api", tags=["agent"])

"""
Routes

    /process-promt
        - Streamlines the process from the SML to the Cloud Agent
        - Returns discrepency report and flags
"""


# --- Request/Response Models ---
class LocalAgentRequest(BaseModel):
    """Request from local agent to process a prompt."""
    prompt: str
    pii_status: str
    slm_flag: str
    malicious_flag: str
    employee_id: Optional[str] = None
    session_id: Optional[str] = None


# --- Routes ---
@router.post("/process-prompt", response_model=ToolkitResponse)
async def process_prompt_from_local_agent(request: LocalAgentRequest):
    """
    Process a prompt from the local agent through the cloud security agent.
    
    Args:
        request: LocalAgentRequest containing prompt and security flags
        
    Returns:
        ToolkitResponse with status, details, and optional response
    """
    try:
        # Call the agent function directly
        result = await process_prompt(
            prompt=request.prompt,
            pii_status=request.pii_status,
            slm_flag=request.slm_flag,
            malicious_flag=request.malicious_flag
        )
        
        # Log the message to database
        if request.employee_id:
            try:
                await log_message(
                    employee_id=request.employee_id,
                    text=request.prompt,
                    response=result.final_response,
                    status=result.status,
                    session_id=request.session_id,
                    metadata={
                        "pii_status": request.pii_status,
                        "slm_flag": request.slm_flag,
                        "malicious_flag": request.malicious_flag,
                        "details": result.details,
                        "discrepancy_report": result.discrepancy_report.dict() if result.discrepancy_report else None
                    }
                )
            except Exception as log_error:
                print(f"Warning: Failed to log message to database: {log_error}")
        
        # Return the agent response
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing prompt: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "New Backend API",
        "database_configured": bool(settings.MONGODB_STRING),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "openrouter_configured": bool(settings.OPENAI_API_KEY)
    }
