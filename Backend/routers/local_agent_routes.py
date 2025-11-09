"""Routes for local security agent API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Optional

from services.local_agent import LocalSecurityAgent, QueryRequest, QueryResponse

router = APIRouter(prefix="/local-agent", tags=["Local Agent"])

# Global agent instance - initialized on startup
local_agent: Optional[LocalSecurityAgent] = None


def initialize_local_agent(model_path: str = "betModel"):
    """Initialize the local agent instance."""
    global local_agent
    if local_agent is None:
        print("Initializing Local Security Agent...")
        try:
            local_agent = LocalSecurityAgent(model_path=model_path)
            print("Local Security Agent ready.")
        except Exception as e:
            print(f"Error initializing Local Security Agent: {e}")
            print("Note: Place your fine-tuned 'betModel' directory in the project root")
            print("The system will continue without the misuse detection model")
            raise  # Re-raise to let main.py handle it gracefully


def get_local_agent() -> LocalSecurityAgent:
    """Dependency to get the local agent instance."""
    if local_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Local Security Agent not initialized"
        )
    return local_agent


@router.post("/check-query", response_model=QueryResponse)
async def check_query(request: QueryRequest):
    """
    Process a query through the local security pipeline.
    
    Performs:
    1. PII detection using Presidio
    2. Malicious intent detection using local model
    3. Sensitive data classification
    
    Returns security flags indicating if the query should be blocked, flagged, or accepted.
    """
    agent = get_local_agent()
    
    try:
        result = await agent.check_query(request.query)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@router.get("/status")
async def get_status():
    """Get the current status of the local security agent."""
    agent = get_local_agent()
    return agent.get_status()


@router.get("/health")
async def health_check():
    """Health check endpoint for the local agent service."""
    try:
        agent = get_local_agent()
        status = agent.get_status()
        return {
            "status": "healthy",
            "service": status["service"],
            "components": status["components"]
        }
    except HTTPException:
        return {
            "status": "unhealthy",
            "reason": "Local agent not initialized"
        }

