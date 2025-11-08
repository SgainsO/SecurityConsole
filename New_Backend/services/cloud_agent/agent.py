import sys
import json
import asyncio
import httpx
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from google import genai
from google.genai import types

# Add parent directories to path for imports
current_dir = Path(__file__).resolve().parent
new_backend_dir = current_dir.parent.parent
sys.path.insert(0, str(new_backend_dir))

from config.config import settings

# --- Configuration ---
OPENROUTER_MODEL_1 = "openai/gpt-4.1-nano"
OPENROUTER_MODEL_2 = "anthropic/claude-3-haiku"
OPENROUTER_EMBEDDING_MODEL = "qwen/qwen3-embedding-0.6b"
CONSENSUS_SIMILARITY_TOLERANCE = 0.1


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
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        print("GeminiClient initialized with official Google SDK.")

    async def get_second_opinion(self, prompt: str, initial_flags: Dict[str, str]) -> Dict[str, str]:
        """Ask Gemini-2.5-flash for a second opinion with structured JSON response."""
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
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=system_prompt
        )

        raw_text = response.text
        try:
            # Find the start and end of the JSON object to strip markdown
            json_start = raw_text.find('{')
            json_end = raw_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise json.JSONDecodeError("No JSON object found in response", raw_text, 0)

            json_str = raw_text[json_start:json_end]
            
            # Use a local Pydantic model for validation as you suggested
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
        """Generate a normal LLM response."""
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=200,
            )
        )
        return response.text

async def get_openrouter_response(prompt: str, model: str) -> str:
    if not settings.OPENAI_API_KEY:
        print(f"Warning: OPENAI_API_KEY not set. Cannot call model {model}.")
        return f"Error: OpenRouter API key not configured."
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                timeout=90.0
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError) as e:
            print(f"Error calling OpenRouter for model {model}: {e}")
            return f"Error: Could not get response from {model}."

async def get_openrouter_embeddings(texts: List[str], model: str) -> np.ndarray:
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenRouter API key not configured for embeddings.")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url="https://openrouter.ai/api/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "input": texts,
                    "encoding_format": "float"
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            sorted_embeddings = sorted(data['data'], key=lambda e: e['index'])
            return np.array([item['embedding'] for item in sorted_embeddings])
        except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError) as e:
            print(f"Error calling OpenRouter for embeddings model {model}: {e}")
            raise


# --- Hallucination Detector ---
class HallucinationDetector:
    def __init__(self):
        print("HallucinationDetector initialized to use OpenRouter embeddings.")

    async def check(self, r0: str, r1: str, r2: str, threshold: float = 0.75) -> bool:
        """Return True if hallucination suspected."""
        try:
            embeddings = await get_openrouter_embeddings(
                [r0, r1, r2],
                model=OPENROUTER_EMBEDDING_MODEL
            )
        except Exception as e:
            print(f"Embedding fetch failed ({e}); assuming hallucination.")
            return True

        sim_01 = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        sim_02 = cosine_similarity([embeddings[0]], [embeddings[2]])[0][0]
        print(f"Cosine Similarities: R0-R1={sim_01:.3f}, R0-R2={sim_02:.3f}")
        
        # Flag as hallucination if the difference between the two scores is too large.
        if abs(sim_01 - sim_02) > CONSENSUS_SIMILARITY_TOLERANCE:
            print(f"Flagging hallucination due to lack of consensus (score difference > {CONSENSUS_SIMILARITY_TOLERANCE})")
            return True

        return False

# --- Global Instances ---
gemini_client = GeminiClient(api_key=settings.GEMINI_API_KEY)
hallucination_detector = HallucinationDetector()

print("Cloud Agent initialized with Gemini-2.5-flash backend.")


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

    # Part 3: Generate and Check Hallucinations
    try:
        print("Generating responses for hallucination check...")
        r0, r1, r2 = await asyncio.gather(
            gemini_client.get_llm_response(prompt),
            get_openrouter_response(prompt, model=OPENROUTER_MODEL_1),
            get_openrouter_response(prompt, model=OPENROUTER_MODEL_2)
        )

        is_hallucinated = await hallucination_detector.check(r0, r1, r2)

        if is_hallucinated:
            return ToolkitResponse(
                status="POSSIBLE_HALLUCINATION",
                details="Response consistency was low.",
                final_response=r0,
                discrepancy_report=discrepancy_report if has_discrepancy else None
            )

        return ToolkitResponse(
            status="SUCCESS",
            details="Prompt processed successfully.",
            final_response=r0,
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
