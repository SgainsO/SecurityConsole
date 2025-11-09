"""Unified Agent Routes - Integrates local pre-check with cloud agent processing."""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

# Add parent directories to path for imports
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
sys.path.insert(0, str(backend_dir))

from services.local_agent import LocalSecurityAgent, QueryResponse as LocalQueryResponse
from services.cloud_agent.agent import process_prompt, ToolkitResponse

router = APIRouter(prefix="/agent", tags=["Unified Agent"])

# Global agent instances
local_agent: Optional[LocalSecurityAgent] = None


class PromptRequest(BaseModel):
    """Request model for processing a user prompt."""
    prompt: str
    entities_to_filter: Optional[list] = None


class UnifiedResponse(BaseModel):
    """Complete response from the unified agent workflow."""
    prompt: str
    local_check: LocalQueryResponse
    final_status: str
    details: str
    llm_response: Optional[str] = None
    discrepancy_report: Optional[dict] = None


def initialize_unified_agent(model_path: str = "betModel"):
    """Initialize the unified agent system."""
    global local_agent
    if local_agent is None:
        print("Initializing Unified Agent System...")
        try:
            local_agent = LocalSecurityAgent(model_path=model_path)
            print("Unified Agent System ready.")
        except Exception as e:
            print(f"Error initializing Unified Agent: {e}")
            print("Note: Place your fine-tuned 'betModel' directory in the project root")
            print("The system will continue without the misuse detection model")
            raise  # Re-raise to let main.py handle it gracefully


def get_local_agent() -> LocalSecurityAgent:
    """Get the local agent instance."""
    if local_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Unified Agent System not initialized"
        )
    return local_agent


@router.post("/process", response_model=UnifiedResponse)
async def process_user_prompt(request: PromptRequest):
    """
    Process a user prompt through the complete security workflow.
    
    Workflow:
    1. Local Agent Pre-Check (check_query):
       - PII detection using Presidio
       - Malicious intent detection using local ML model
       - Sensitive data classification
    
    2. Cloud Agent Processing (process_prompt):
       - Second opinion from Gemini via OpenRouter
       - Discrepancy detection between local and cloud analysis
       - LLM response generation
       - Hallucination detection using Grok
    
    Returns:
        Complete security analysis and the final LLM response
    """
    agent = get_local_agent()
    
    try:
        # Step 1: Local agent pre-check
        print(f"\n{'='*60}")
        print(f"Processing prompt: {request.prompt[:50]}...")
        print(f"{'='*60}")
        print("\n[STEP 1] Local Agent Pre-Check...")
        
        local_result = await agent.check_query(
            query=request.prompt,
            entities_to_filter=request.entities_to_filter
        )
        
        print(f"  ├─ PII Status: {local_result.pii_status}")
        print(f"  ├─ SLM Flag: {local_result.slm_flag}")
        print(f"  └─ Malicious Flag: {local_result.malicious_flag}")
        
        # Step 2: Cloud agent processing
        print("\n[STEP 2] Cloud Agent Processing...")
        
        cloud_result = await process_prompt(
            prompt=request.prompt,
            pii_status=local_result.pii_status,
            slm_flag=local_result.slm_flag,
            malicious_flag=local_result.malicious_flag
        )
        
        print(f"  ├─ Final Status: {cloud_result.status}")
        print(f"  └─ Details: {cloud_result.details}")
        print(f"\n{'='*60}")
        print(f"Processing Complete")
        print(f"{'='*60}\n")
        
        # Build unified response
        response = UnifiedResponse(
            prompt=request.prompt,
            local_check=local_result,
            final_status=cloud_result.status,
            details=cloud_result.details,
            llm_response=cloud_result.final_response,
            discrepancy_report=cloud_result.discrepancy_report.dict() if cloud_result.discrepancy_report else None
        )
        
        return response
        
    except Exception as e:
        print(f"Error in unified agent workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing prompt: {str(e)}"
        )


@router.get("/status")
async def get_status():
    """Get the status of the unified agent system."""
    agent = get_local_agent()
    local_status = agent.get_status()
    
    return {
        "service": "unified_agent",
        "status": "operational",
        "workflow": "local_check -> cloud_processing -> llm_response",
        "components": {
            "local_agent": local_status,
            "cloud_agent": {
                "service": "cloud_agent",
                "status": "operational",
                "components": {
                    "gemini_client": "active",
                    "hallucination_detector": "active"
                }
            }
        }
    }


@router.get("/health")
async def health_check():
    """Health check endpoint for the unified agent system."""
    try:
        agent = get_local_agent()
        status = agent.get_status()
        
        return {
            "status": "healthy",
            "service": "unified_agent",
            "local_agent": status["status"]
        }
    except HTTPException:
        return {
            "status": "unhealthy",
            "reason": "Unified agent system not initialized"
        }

