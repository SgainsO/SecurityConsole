from dotenv import load_dotenv
from local_agent import MisuseDetector
from unsloth_slm import SecuritySLMUnsloth, SecuritySLMUnslothFirewall, conservative_merge

# Load environment variables from .env file before anything else
load_dotenv()

import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from presidio_analyzer import AnalyzerEngine
import asyncio
import time

# --- Configuration ---
# Base model can be overridden via env var UNSLOTH_BASE_MODEL

# --- FastAPI App ---
app = FastAPI()

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    pii_status: str
    slm_flag: str
    malicious_flag: str
    final_flag: str

# --- Presidio Analyzer ---
# Lazily initialized on first use, but we create the engine instance here.
analyzer = AnalyzerEngine()

# --- Model singletons (initialized at startup) ---
misuse_detector = None            # MisuseDetector from local_agent.py
unsloth_slm = None               # Inference-only Unsloth wrapper
adaptive_firewall = None         # Full adaptive firewall (GPU + unsloth required)
_adaptive_lock = None            # Concurrency guard

@app.on_event("startup")
async def startup_event():
    """Log application startup events and initialize models."""
    global misuse_detector, unsloth_slm, adaptive_firewall, _adaptive_lock
    print("Starting up the Secure Query Filter application...")
    # analyzer.load_predefined_recognizers() # Can be uncommented to pre-load all models
    print("Presidio Analyzer engine is ready.")

    # Initialize the misuse detector model once at startup
    print("Initializing MisuseDetector model...")
    try:
        misuse_detector = MisuseDetector()
        print("MisuseDetector initialized.")
    except Exception as e:
        print(f"Failed to initialize MisuseDetector (will continue without it): {e}")
        misuse_detector = None

    # Initialize the Unsloth-backed SLM (LoRA adapters)
    try:
        print("Initializing SecuritySLMUnsloth (loading base model + adapters)...")
        unsloth_slm = SecuritySLMUnsloth()
        if not unsloth_slm.available:
            print("SecuritySLMUnsloth unavailable (base model or adapters missing). Will proceed without it.")
        else:
            print("SecuritySLMUnsloth initialized and ready.")
    except Exception as e:
        print(f"Failed to initialize SecuritySLMUnsloth: {e}")
        unsloth_slm = None

    # Attempt to initialize adaptive firewall (only if GPU + unsloth available)
    try:
        print("Initializing SecuritySLMUnslothFirewall (adaptive retraining)...")
        adaptive_firewall = SecuritySLMUnslothFirewall(initial_adapter_path="lora_adapters/best")
        if not adaptive_firewall.available:
            adaptive_firewall = None
            print("Adaptive firewall disabled (unsloth missing or no GPU).")
        else:
            print("Adaptive firewall ready for on-the-fly fine-tuning.")
    except Exception as e:
        print(f"Failed to initialize adaptive firewall: {e}")
        adaptive_firewall = None

    _adaptive_lock = asyncio.Lock()

    print("Application startup complete.")


@app.post("/check-query", response_model=QueryResponse)
async def check_query(request: QueryRequest):
    """
    Processes a query through a security pipeline: PII check, then LLM-based checks.
    """
    # --- Customizable PII Filter ---
    # Add or remove entity types from this list to control what is filtered.
    # Common entities: "PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD", 
    # "US_SSN", "PERSON", "LOCATION", "DATE_TIME"
    entities_to_filter = [
        "PHONE_NUMBER", 
        "EMAIL_ADDRESS", 
        "US_SSN",
        "CREDIT_CARD"
    ]

    # Module 1: PII Check
    pii_results = analyzer.analyze(
        text=request.query,
        entities=entities_to_filter,
        language='en'
    )
    if pii_results:
        print(f"PII detected: {pii_results}")
        return QueryResponse(
            pii_status="BLOCK",
            slm_flag="NOT_RUN",
            malicious_flag="NOT_RUN"
        )

    # Module 2 & 3: Local SLMs consensus (MisuseDetector + SecuritySLMUnsloth)
    #  - slm_flag    -> Unsloth-backed classifier (if available), else "NOT_RUN"
    #  - malicious_flag -> MisuseDetector classifier
    #  - final_flag  -> conservative merge of the two when both available; otherwise the one available

    # MisuseDetector returns a dict like {"data": {"TYPE": "STRING", "ENUM": "ACCEPT"}}
    misuse_raw = misuse_detector.classify(request.query) if misuse_detector else {"data": {"ENUM": "ERROR"}}
    misuse_label = misuse_raw.get("data", {}).get("ENUM", "ERROR")

    unsloth_label = "NOT_RUN"
    if unsloth_slm is not None:
        try:
            unsloth_label = unsloth_slm.classify(request.query)
        except Exception as e:
            print(f"Unsloth SLM classify error: {e}")
            unsloth_label = "ERROR"

    valid = {"ACCEPT", "FLAG", "BLOCK"}
    if unsloth_label in valid and misuse_label in valid:
        final_flag = conservative_merge(unsloth_label, misuse_label)
    elif misuse_label in valid:
        final_flag = misuse_label
    elif unsloth_label in valid:
        final_flag = unsloth_label
    else:
        final_flag = "ERROR"

    return QueryResponse(
        pii_status="ACCEPT",
        slm_flag=unsloth_label,
        malicious_flag=misuse_label,
        final_flag=final_flag,
    )


class RetrainRequest(BaseModel):
    prompt: str
    label: str  # EXPECTED one of ACCEPT | FLAG | BLOCK

@app.post("/adaptive-retrain")
async def adaptive_retrain(req: RetrainRequest):
    """Trigger single-example fine-tune + evaluation + rollback/promotion.
    Returns status JSON. Disabled if adaptive firewall not available.
    """
    global adaptive_firewall, _adaptive_lock
    if adaptive_firewall is None:
        return {"status": "error", "detail": "Adaptive firewall not available on this host."}

    if req.label not in {"ACCEPT", "FLAG", "BLOCK"}:
        return {"status": "error", "detail": "Invalid label."}

    async with _adaptive_lock:  # prevents overlapping training sessions
        status = adaptive_firewall.retrain_and_evaluate(req.prompt, req.label)
    return status

if __name__ == "__main__":
    import uvicorn
    print("Starting Uvicorn server for the Secure Query Filter.")
    # Use reload=True for development, consider removing it for production.
    uvicorn.run("on_premise_agent:app", host="0.0.0.0", port=8000, reload=True)
