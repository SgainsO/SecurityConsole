## SecuritySLMUnsloth Integration

This repository now includes an inference-only Small Language Model (SLM) wrapper `SecuritySLMUnsloth` (`unsloth_slm.py`). It loads a base Llama model and attaches LoRA adapters stored under `lora_adapters/best/` to classify prompts into one of three categories: `ACCEPT`, `FLAG`, or `BLOCK`.

### Consensus Classification
The `/check-query` FastAPI endpoint (in `on_premise_agent.py`) now performs:
1. PII scan via Presidio.
2. Classification by the legacy `MisuseDetector` (sequence classification model).
3. Classification by `SecuritySLMUnsloth` (LoRA + Llama causal model) if available.
4. Conservative merge rule: `BLOCK > FLAG > ACCEPT` to produce `final_flag`.

Response JSON fields:
```json
{
  "pii_status": "ACCEPT|BLOCK",
  "slm_flag": "ACCEPT|FLAG|BLOCK|NOT_RUN|ERROR",
  "malicious_flag": "ACCEPT|FLAG|BLOCK|ERROR",
  "final_flag": "ACCEPT|FLAG|BLOCK|ERROR"
}
```

### macOS / CPU Notes
Running Llama models on macOS without a GPU will default to CPU or Apple Silicon MPS. Performance will be slower. If the base model or adapters cannot be loaded (e.g., missing access token), the SLM returns `NOT_AVAILABLE` and the endpoint falls back to the legacy classifier only.

### Deploying on Google Cloud (GCE / GPU)
1. Provision a GPU instance (e.g., A100 or L4) with sufficient VRAM.
2. Install system packages:
	```bash
	sudo apt update
	sudo apt install -y build-essential git python3-pip
	```
3. (Optional) Create a virtual environment.
4. Install Python dependencies:
	```bash
	pip install -r requirements.txt
	```
5. Set environment variables as needed (e.g., `UNSLOTH_BASE_MODEL`).
6. Run the API:
	```bash
	uvicorn on_premise_agent:app --host 0.0.0.0 --port 8000
	```
7. Test:
	```bash
	curl -X POST http://SERVER_IP:8000/check-query -H 'Content-Type: application/json' -d '{"query":"What is the capital of France?"}'
	```

### Future Enhancements
- Add lightweight health endpoint for adapter freshness.
- Optional periodic reloading of adapters for hot updates.
- Add retraining trigger endpoint once GPU fine-tuning pipeline is ready.

## Adaptive Fine-Tuning (On-the-fly)

When running on a GPU host with `unsloth` available, the API exposes an endpoint to retrain in place on a new labeled example and automatically promote/rollback based on accuracy:

Endpoint:
```
POST /adaptive-retrain
{
	"prompt": "...",
	"label": "ACCEPT|FLAG|BLOCK"
}
```

Behavior:
- Appends the example to `data/live_training_data.jsonl`.
- Fine-tunes the currently loaded LoRA adapters for a few steps.
- Evaluates against `data/test_eval_data_unsloth.json`.
- Promotes adapters if accuracy >= previous; otherwise rolls back.

Notes:
- Requires CUDA; on macOS CPU/MPS this endpoint is disabled.
- Make sure the base model (default `meta-llama/Llama-3.2-1B`) is accessible from Hugging Face.

# Sentry Firewall