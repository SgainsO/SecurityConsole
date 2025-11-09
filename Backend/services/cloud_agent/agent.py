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
        print(f"GeminiClient initialized to use {GEMINI_MODEL} via OpenRouter.")

    async def get_second_opinion(self, prompt: str, initial_flags: Dict[str, str]) -> Dict[str, str]:
        """Ask Gemini for a second opinion with structured JSON response via OpenRouter."""
        print("🔄 Calling Gemini (via OpenRouter) for expert second opinion...")
        
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
            print("❌ ERROR: OPENROUTER_API_KEY not set")
            raise ValueError("OpenRouter API key not configured")
        
        async with httpx.AsyncClient() as client:
            try:
                print("⏳ Waiting for Gemini API response via OpenRouter...")
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
                print("✅ Received response from Gemini API")
                
            except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError) as e:
                print(f"❌ ERROR: Failed to call Gemini via OpenRouter: {e}")
                raise

        print(f"📄 Raw Gemini response (first 200 chars): {raw_text[:200]}...")
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
            print(f"Could not parse JSON from Gemini response: {e}")
            print(f"Raw response was: {raw_text}")
            return {"pii_status": "ACCEPT", "slm_flag": "ACCEPT", "malicious_flag": "ACCEPT"}

    async def get_llm_response(self, prompt: str) -> str:
        """Generate a normal LLM response via OpenRouter."""
        print("🔄 Calling Gemini (via OpenRouter) for LLM response...")
        
        if not self.api_key:
            print("❌ ERROR: OPENROUTER_API_KEY not set")
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
                
                print("✅ Received LLM response from Gemini")
                print(f"   Response length: {len(text)} chars")
                return text
                
            except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError) as e:
                print(f"❌ ERROR: Failed to get LLM response from Gemini via OpenRouter: {e}")
                print(f"   Exception type: {type(e).__name__}")
                return f"Error: Could not get response from Gemini."

async def get_openrouter_response(prompt: str, model: str) -> str:
    if not settings.OPENROUTER_API_KEY:
        print(f"Warning: OPENROUTER_API_KEY not set. Cannot call model {model}.")
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
            print(f"Error calling OpenRouter for model {model}: {e}")
            return f"Error: Could not get response from {model}."

async def check_hallucination_with_grok(prompt: str, response: str) -> bool:
    """Use Grok to analyze a single response and determine if there's hallucination."""
    print("\n" + "="*80)
    print("HALLUCINATION CHECK - Starting Analysis with Grok-4-Fast")
    print("="*80)
    
    if not settings.OPENROUTER_API_KEY:
        print("❌ WARNING: OPENROUTER_API_KEY not set. Cannot call Grok hallucination checker.")
        print("⚠️  Assuming hallucination due to missing API key.")
        return True  # Assume hallucination if we can't check
    
    print(f"\n📋 User Prompt:")
    print("-" * 80)
    print(prompt)
    
    print(f"\n📋 Gemini Response to Analyze:")
    print("-" * 80)
    print(response)
    
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

    print("\n🤖 Calling Grok-4-Fast for hallucination analysis...")
    
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
            
            print(f"✅ Received response from Grok-4-Fast")
            print(f"📄 Raw response: {raw_text[:300]}..." if len(raw_text) > 300 else f"📄 Raw response: {raw_text}")
            
            # Parse the JSON response
            json_start = raw_text.find('{')
            json_end = raw_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                print(f"❌ ERROR: No JSON found in Grok response")
                print(f"Full response: {raw_text}")
                return True  # Assume hallucination if we can't parse
            
            json_str = raw_text[json_start:json_end]
            result = json.loads(json_str)
            
            is_hallucinated = result.get('is_hallucinated', True)
            reasoning = result.get('reasoning', 'No reasoning provided')
            
            print("\n" + "="*80)
            print("HALLUCINATION CHECK - RESULTS")
            print("="*80)
            if is_hallucinated:
                print("🚨 HALLUCINATION DETECTED: True")
            else:
                print("✅ HALLUCINATION DETECTED: False (responses are consistent)")
            print(f"\n💭 Grok's Reasoning:")
            print(f"   {reasoning}")
            print("="*80 + "\n")
            
            return is_hallucinated
            
        except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"\n❌ ERROR: Exception during Grok hallucination check")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {e}")
            print("⚠️  Assuming hallucination due to error.")
            print("="*80 + "\n")
            return True  # Assume hallucination on error


# --- Hallucination Detector ---
class HallucinationDetector:
    def __init__(self):
        print("✅ HallucinationDetector initialized to use Grok-4-Fast for analysis.")

    async def check(self, prompt: str, response: str) -> bool:
        """Return True if hallucination suspected. Uses Grok to analyze a single response."""
        print("\n🔍 Initiating hallucination detection check...")
        try:
            result = await check_hallucination_with_grok(prompt, response)
            if result:
                print("⚠️  Hallucination check completed: HALLUCINATION DETECTED")
            else:
                print("✅ Hallucination check completed: NO HALLUCINATION")
            return result
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: Grok hallucination check failed")
            print(f"   Exception: {e}")
            print("⚠️  Defaulting to ASSUME HALLUCINATION for safety.")
            return True

# --- Global Instances ---
gemini_client = GeminiClient(api_key=settings.OPENROUTER_API_KEY)
hallucination_detector = HallucinationDetector()

print(f"Cloud Agent initialized with {GEMINI_MODEL} via OpenRouter and Grok-4-Fast hallucination detection.")


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
    print("\n" + "="*80)
    print("SECURITY TOOLKIT - PROCESSING PROMPT")
    print("="*80)
    print(f"📝 Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"📝 Prompt: {prompt}")
    print("\n🔐 Initial Security Flags:")
    print(f"   - PII Status: {pii_status}")
    print(f"   - SLM Flag: {slm_flag}")
    print(f"   - Malicious Flag: {malicious_flag}")
    
    initial_flags = {
        'pii_status': pii_status,
        'slm_flag': slm_flag,
        'malicious_flag': malicious_flag
    }

    # Part 1: Second Opinion
    print("\n" + "="*80)
    print("PHASE 1: GETTING EXPERT SECOND OPINION (Gemini)")
    print("="*80)
    try:
        expert_flags = await gemini_client.get_second_opinion(prompt, initial_flags)
        print("✅ Expert opinion received")
        print(f"   - PII Status: {expert_flags.get('pii_status')}")
        print(f"   - SLM Flag: {expert_flags.get('slm_flag')}")
        print(f"   - Malicious Flag: {expert_flags.get('malicious_flag')}")
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
    
    if has_discrepancy:
        print("\n⚠️  DISCREPANCY DETECTED between initial and expert flags:")
        if discrepancy_report.pii_discrepancy:
            print(f"   - PII: {initial_flags['pii_status']} → {expert_flags['pii_status']}")
        if discrepancy_report.slm_discrepancy:
            print(f"   - SLM: {initial_flags['slm_flag']} → {expert_flags['slm_flag']}")
        if discrepancy_report.malicious_discrepancy:
            print(f"   - Malicious: {initial_flags['malicious_flag']} → {expert_flags['malicious_flag']}")
    else:
        print("\n✅ No discrepancies found between initial and expert flags")

    # Part 2: Decision Logic
    print("\n" + "="*80)
    print("PHASE 2: DECISION LOGIC - EVALUATING FLAGS")
    print("="*80)
    
    all_flags = {**initial_flags, **expert_flags}

    if any(flag == 'BLOCK' for flag in all_flags.values()):
        print("🚫 DECISION: BLOCKED")
        print("   Reason: At least one BLOCK flag was issued")
        blocked_flags = [k for k, v in all_flags.items() if v == 'BLOCK']
        print(f"   Blocked by: {', '.join(blocked_flags)}")
        return ToolkitResponse(
            status="BLOCKED",
            details="A BLOCK flag was issued.",
            discrepancy_report=discrepancy_report if has_discrepancy else None
        )

    if any(flag == 'FLAG' for flag in all_flags.values()):
        print("⚠️  DECISION: FLAGGED")
        print("   Reason: At least one FLAG was issued")
        flagged_items = [k for k, v in all_flags.items() if v == 'FLAG']
        print(f"   Flagged by: {', '.join(flagged_items)}")
        return ToolkitResponse(
            status="FLAGGED",
            details="A FLAG was issued.",
            discrepancy_report=discrepancy_report if has_discrepancy else None
        )
    
    print("✅ All security flags passed (ACCEPT)")
    print("   Proceeding to hallucination check phase...")

    # Part 3: Generate Response and Check for Hallucinations
    try:
        print("\n" + "="*80)
        print("PHASE 3: GENERATING GEMINI RESPONSE")
        print("="*80)
        print(f"🔄 Generating response from {GEMINI_MODEL}...")
        
        gemini_response = await gemini_client.get_llm_response(prompt)
        
        # Check if response is valid
        if not gemini_response or gemini_response.startswith("Error:"):
            print("❌ ERROR: Gemini response failed")
            print(f"   Error: {gemini_response}")
            return ToolkitResponse(
                status="BLOCKED",
                details="Failed to generate response from Gemini.",
                discrepancy_report=discrepancy_report if has_discrepancy else None
            )
        
        print("✅ Gemini response generated successfully")
        print(f"   Response length: {len(gemini_response)} chars")

        # Check for hallucination using Grok
        is_hallucinated = await hallucination_detector.check(prompt, gemini_response)

        if is_hallucinated:
            print("\n⚠️  FINAL STATUS: POSSIBLE_HALLUCINATION")
            print("   Returning Gemini response with hallucination warning.")
            return ToolkitResponse(
                status="POSSIBLE_HALLUCINATION",
                details="Response may contain hallucinated information.",
                final_response=gemini_response,
                discrepancy_report=discrepancy_report if has_discrepancy else None
            )

        print("\n✅ FINAL STATUS: SUCCESS")
        print("   All checks passed. Response is valid.")
        return ToolkitResponse(
            status="SUCCESS",
            details="Prompt processed successfully.",
            final_response=gemini_response,
            discrepancy_report=discrepancy_report if has_discrepancy else None
        )

    except Exception as e:
        print(f"\n❌ ERROR: Exception during response generation")
        print(f"   Error: {e}")
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
