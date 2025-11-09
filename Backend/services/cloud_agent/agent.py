import sys
import json
import asyncio
import httpx
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

# Add parent directories to path for imports
current_dir = Path(__file__).resolve().parent
new_backend_dir = current_dir.parent.parent
sys.path.insert(0, str(new_backend_dir))

from config.config import settings

# --- Configuration ---
GEMINI_MODEL = "google/gemini-2.5-flash"  # Gemini via OpenRouter
HALLUCINATION_CHECKER_MODEL = "x-ai/grok-4-fast"


# --- Pydantic Models ---
class DiscrepancyReport(BaseModel):
    pii_discrepancy: bool
    slm_discrepancy: bool
    malicious_discrepancy: bool
    initial_flags: Dict[str, str]
    expert_flags: Dict[str, str]

class ToolkitResponse(BaseModel):
    status: str = Field(..., description="Final status: BLOCKED, FLAGGED, POSSIBLE_HALLUCINATION, or SUCCESS.")
    details: str
    final_response: Optional[str] = None
    discrepancy_report: Optional[DiscrepancyReport] = None


# --- LLM Clients ---
class GeminiClient:
    """Client for Gemini model via OpenRouter API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_second_opinion(self, prompt: str, initial_flags: Dict[str, str]) -> Dict[str, str]:
        """Ask Gemini for a second opinion with structured JSON response via OpenRouter."""
        system_prompt = f"""
You are a security analysis expert. Provide a JSON-only expert review of the following prompt.

Initial scan results:
- pii_status: {initial_flags.get('pii_status')}
- slm_flag: {initial_flags.get('slm_flag')}
- malicious_flag: {initial_flags.get('malicious_flag')}

Analyze the user prompt below and return JSON with:
{{
  "pii_status": "ACCEPT" or "BLOCK",
  "slm_flag": "ACCEPT" or "FLAG" or "BLOCK",
  "malicious_flag": "ACCEPT" or "FLAG" or "BLOCK"
}}

Prompt: "{prompt}"
"""
        
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": GEMINI_MODEL,
                        "messages": [{"role": "user", "content": system_prompt}]
                    },
                    timeout=90.0
                )
                response.raise_for_status()
                data = response.json()
                raw_text = data['choices'][0]['message']['content']
                
            except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError) as e:
                raise

        try:
            # Find the start and end of the JSON object to strip markdown
            json_start = raw_text.find('{')
            json_end = raw_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise json.JSONDecodeError("No JSON object found in response", raw_text, 0)

            json_str = raw_text[json_start:json_end]
            
            # Use a local Pydantic model for validation
            class Opinion(BaseModel):
                pii_status: str
                slm_flag: str
                malicious_flag: str
            
            opinion = Opinion.parse_raw(json_str)
            return opinion.dict()

        except (json.JSONDecodeError, Exception) as e:
            return {"pii_status": "ACCEPT", "slm_flag": "ACCEPT", "malicious_flag": "ACCEPT"}

    async def get_llm_response(self, prompt: str) -> str:
        """Generate a normal LLM response via OpenRouter."""
        if not self.api_key:
            return "Error: OpenRouter API key not configured."
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": GEMINI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 200
                    },
                    timeout=90.0
                )
                response.raise_for_status()
                data = response.json()
                text = data['choices'][0]['message']['content']
                
                return text
                
            except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError) as e:
                return f"Error: Could not get response from Gemini."

async def get_openrouter_response(prompt: str, model: str) -> str:
    if not settings.OPENROUTER_API_KEY:
        return f"Error: OpenRouter API key not configured."
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                timeout=90.0
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError) as e:
            return f"Error: Could not get response from {model}."

async def check_hallucination_with_grok(prompt: str, response: str) -> bool:
    """Use Grok to analyze a single response and determine if there's hallucination."""
    if not settings.OPENROUTER_API_KEY:
        return True  # Assume hallucination if we can't check
    
    analysis_prompt = f"""You are a hallucination detection expert. Analyze the AI response below and determine if it contains hallucinations, made-up information, or factually incorrect claims.

User Prompt:
{prompt}

AI Response:
{response}

Analyze if this response:
1. Contains factually incorrect information
2. Makes up information that isn't verifiable
3. Provides inconsistent or contradictory claims
4. Shows signs of hallucination

Respond with ONLY a JSON object in this exact format:
{{
  "is_hallucinated": true or false,
  "reasoning": "Brief explanation of your decision"
}}"""

    async with httpx.AsyncClient() as client:
        try:
            grok_response = await client.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": HALLUCINATION_CHECKER_MODEL,
                    "messages": [{"role": "user", "content": analysis_prompt}]
                },
                timeout=90.0
            )
            grok_response.raise_for_status()
            data = grok_response.json()
            raw_text = data['choices'][0]['message']['content']
            
            # Parse the JSON response
            json_start = raw_text.find('{')
            json_end = raw_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return True  # Assume hallucination if we can't parse
            
            json_str = raw_text[json_start:json_end]
            result = json.loads(json_str)
            
            is_hallucinated = result.get('is_hallucinated', True)
            
            return is_hallucinated
            
        except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError, json.JSONDecodeError) as e:
            return True  # Assume hallucination on error


# --- Hallucination Detector ---
class HallucinationDetector:
    def __init__(self):
        pass

    async def check(self, prompt: str, response: str) -> bool:
        """Return True if hallucination suspected. Uses Grok to analyze a single response."""
        try:
            result = await check_hallucination_with_grok(prompt, response)
            return result
        except Exception as e:
            return True

# --- Global Instances ---
gemini_client = GeminiClient(api_key=settings.OPENROUTER_API_KEY)
hallucination_detector = HallucinationDetector()


# --- Main Function ---
async def process_prompt(
    prompt: str,
    pii_status: str,
    slm_flag: str,
    malicious_flag: str
) -> ToolkitResponse:
    """
    Process a prompt through the security toolkit.
    
    Args:
        prompt: The user's prompt/query
        pii_status: Initial PII status (ACCEPT/BLOCK)
        slm_flag: Initial SLM flag (ACCEPT/FLAG/BLOCK)
        malicious_flag: Initial malicious flag (ACCEPT/FLAG/BLOCK)
        
    Returns:
        ToolkitResponse with status, details, and optional response/discrepancy report
    """
    initial_flags = {
        'pii_status': pii_status,
        'slm_flag': slm_flag,
        'malicious_flag': malicious_flag
    }

    # Part 1: Second Opinion
    try:
        expert_flags = await gemini_client.get_second_opinion(prompt, initial_flags)
    except Exception as e:
        return ToolkitResponse(status="BLOCKED", details=f"Gemini expert opinion failed: {e}")

    discrepancy_report = DiscrepancyReport(
        pii_discrepancy=(initial_flags['pii_status'] != expert_flags['pii_status']),
        slm_discrepancy=(initial_flags['slm_flag'] != expert_flags['slm_flag']),
        malicious_discrepancy=(initial_flags['malicious_flag'] != expert_flags['malicious_flag']),
        initial_flags=initial_flags,
        expert_flags=expert_flags
    )

    has_discrepancy = any(v for k, v in discrepancy_report.dict().items() if k.endswith('_discrepancy'))

    # Part 2: Decision Logic
    
    all_flags = {**initial_flags, **expert_flags}

    if any(flag == 'BLOCK' for flag in all_flags.values()):
        return ToolkitResponse(
            status="BLOCKED",
            details="A BLOCK flag was issued.",
            discrepancy_report=discrepancy_report if has_discrepancy else None
        )

    if any(flag == 'FLAG' for flag in all_flags.values()):
        return ToolkitResponse(
            status="FLAGGED",
            details="A FLAG was issued.",
            discrepancy_report=discrepancy_report if has_discrepancy else None
        )

    # Part 3: Generate Response and Check for Hallucinations
    try:
        gemini_response = await gemini_client.get_llm_response(prompt)
        
        # Check if response is valid
        if not gemini_response or gemini_response.startswith("Error:"):
            return ToolkitResponse(
                status="BLOCKED",
                details="Failed to generate response from Gemini.",
                discrepancy_report=discrepancy_report if has_discrepancy else None
            )

        # Check for hallucination using Grok
        is_hallucinated = await hallucination_detector.check(prompt, gemini_response)

        if is_hallucinated:
            return ToolkitResponse(
                status="POSSIBLE_HALLUCINATION",
                details="Response may contain hallucinated information.",
                final_response=gemini_response,
                discrepancy_report=discrepancy_report if has_discrepancy else None
            )

        return ToolkitResponse(
            status="SUCCESS",
            details="Prompt processed successfully.",
            final_response=gemini_response,
            discrepancy_report=discrepancy_report if has_discrepancy else None
        )

    except Exception as e:
        return ToolkitResponse(status="BLOCKED", details=f"Error during response generation: {e}")


# --- Example Usage ---
if __name__ == "__main__":
    async def main():
        print("Cloud Agent - Function Mode")
        print("=" * 60)
        
        # Example: Process a safe prompt
        result = await process_prompt(
            prompt="What is the weather like today?",
            pii_status="ACCEPT",
            slm_flag="ACCEPT",
            malicious_flag="ACCEPT"
        )
        
        print(f"\nStatus: {result.status}")
        print(f"Details: {result.details}")
        if result.final_response:
            print(f"Response: {result.final_response}")
        if result.discrepancy_report:
            print(f"Discrepancy Report: {result.discrepancy_report}")
    
    asyncio.run(main())
