import os
import json
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

# --- FastAPI App ---
app = FastAPI(
    title="Security Toolkit Agent",
    description="A second-layer agent for expert review and hallucination detection."
)

# --- Pydantic Models ---
class ToolkitRequest(BaseModel):
    prompt: str
    pii_status: str
    slm_flag: str
    malicious_flag: str

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


# --- Gemini Client (Official SDK) ---
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

        # Gemini SDK call
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=system_prompt
        )

        # Try parsing response as JSON
        try:
            expert_json = json.loads(response.text)
            return expert_json
        except json.JSONDecodeError:
            print("Gemini did not return valid JSON. Defaulting to ACCEPT for safety.")
            return {"pii_status": "ACCEPT", "slm_flag": "ACCEPT", "malicious_flag": "ACCEPT"}

    async def get_llm_response(self, prompt: str) -> str:
        """Generate a normal LLM response."""
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                max_output_tokens=200,
            )
        )
        return response.text

    async def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for text using gemini-embedding-001."""
        embeddings = []
        for text in texts:
            result = self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=text
            )
            embeddings.append(result.embedding.values)
        return np.array(embeddings)


# --- Hallucination Detector ---
class HallucinationDetector:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        print("HallucinationDetector initialized with Gemini embeddings.")

    async def check(self, r0: str, r1: str, r2: str, threshold: float = 0.9) -> bool:
        """Return True if hallucination suspected."""
        try:
            embeddings = await self.gemini_client.get_embeddings([r0, r1, r2])
        except Exception as e:
            print(f"Embedding fetch failed ({e}); assuming hallucination.")
            return True

        sim_01 = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        sim_02 = cosine_similarity([embeddings[0]], [embeddings[2]])[0][0]
        print(f"Cosine Similarities: R0-R1={sim_01:.3f}, R0-R2={sim_02:.3f}")
        return not (sim_01 > threshold and sim_02 > threshold)


# --- Global Instances ---
gemini_client = GeminiClient(api_key=GEMINI_API_KEY)
hallucination_detector = HallucinationDetector(gemini_client=gemini_client)


@app.on_event("startup")
async def startup_event():
    print("Security Toolkit Agent ready with Gemini-2.5-flash backend.")


# --- Main Endpoint ---
@app.post("/process-prompt", response_model=ToolkitResponse)
async def process_prompt(request: ToolkitRequest):
    """Main endpoint for the security toolkit."""
    initial_flags = request.dict(include={'pii_status', 'slm_flag', 'malicious_flag'})

    # Part 1: Second Opinion
    try:
        expert_flags = await gemini_client.get_second_opinion(request.prompt, initial_flags)
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
        return ToolkitResponse(status="BLOCKED", details="A BLOCK flag was issued.", discrepancy_report=discrepancy_report if has_discrepancy else None)

    if any(flag == 'FLAG' for flag in all_flags.values()):
        return ToolkitResponse(status="FLAGGED", details="A FLAG was issued.", discrepancy_report=discrepancy_report if has_discrepancy else None)

    # Part 3: Generate and Check Hallucinations
    try:
        print("Generating responses for hallucination check...")
        r0, r1, r2 = await asyncio.gather(
            gemini_client.get_llm_response(request.prompt),
            gemini_client.get_llm_response(request.prompt),
            gemini_client.get_llm_response(request.prompt)
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("security_toolkit_agent:app", host="0.0.0.0", port=8001, reload=True)
