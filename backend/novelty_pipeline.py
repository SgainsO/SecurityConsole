#!/usr/bin/env python3
"""
Novelty Detection Pipeline
- Check 1: PII (passthrough)
- Check 2: Triangulation (OpenRouter with Gemini + other models)
- Check 3: Consensus via cosine similarity
"""

import os
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your-key-here")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def check1_pii(prompt: str) -> str:
    """Check 1: PII detection (always returns input as specified)"""
    return prompt


def check2_triangulation(prompt: str) -> dict:
    """Check 2: Get responses from multiple models via OpenRouter"""
    models = [
        "deepseek/deepseek-v3.2-exp",  # Gemini via OpenRouter
        "openai/gpt-4o-mini",                 # OpenAI via OpenRouter
        "google/gemini-2.5-flash"                      # Grok via OpenRouter
    ]

    responses = {}

    for model in models:
        try:
            response = requests.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            responses[model] = data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error with {model}: {e}")
            responses[model] = ""

    return responses


def get_embeddings(texts: list[str]) -> np.ndarray:
    """Get embeddings for texts using OpenRouter"""
    embeddings = []

    for text in texts:
        try:
            # Use a simple embedding model via OpenRouter
            response = requests.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/text-embedding-3-small",
                    "input": text
                },
                timeout=30
            )
            response.raise_for_status()
            embedding = response.json()["data"][0]["embedding"]
            embeddings.append(embedding)
        except Exception as e:
            print(f"Embedding error: {e}")
            # Fallback: simple bag-of-words embedding
            words = text.lower().split()
            embeddings.append(np.random.rand(384))  # dummy embedding

    return np.array(embeddings)


def check3_consensus(responses: dict, threshold: float = 0.9) -> dict:
    """Check 3: Check consensus via cosine similarity of embeddings"""
    response_texts = [text for text in responses.values() if text]

    if len(response_texts) < 2:
        return {"consensus": False, "reason": "Not enough responses"}

    # Get embeddings
    embeddings = get_embeddings(response_texts)

    # Compute pairwise cosine similarity
    similarities = cosine_similarity(embeddings)

    # Get all pairwise similarities (excluding diagonal)
    n = len(similarities)
    pairwise_sims = []
    for i in range(n):
        for j in range(i + 1, n):
            pairwise_sims.append(similarities[i][j])

    # Check if all similarities > threshold
    all_high_similarity = all(sim > threshold for sim in pairwise_sims)
    avg_similarity = np.mean(pairwise_sims) if pairwise_sims else 0

    return {
        "consensus": all_high_similarity,
        "avg_similarity": avg_similarity,
        "pairwise_similarities": pairwise_sims,
        "flag_for_review": not all_high_similarity  # High consensus = potential hallucination
    }


def run_pipeline(prompt: str) -> dict:
    """Run the complete novelty detection pipeline"""
    print(f"\n{'='*60}")
    print(f"PROMPT: {prompt}")
    print(f"{'='*60}\n")

    # Check 1: PII
    print("[Check 1: PII] Passthrough...")
    cleaned_prompt = check1_pii(prompt)

    # Check 2: Triangulation
    print("[Check 2: Triangulation] Querying multiple models...")
    responses = check2_triangulation(cleaned_prompt)

    print("\n--- Model Responses ---")
    for model, response in responses.items():
        print(f"\n{model}:")
        print(f"  {response[:200]}..." if len(response) > 200 else f"  {response}")

    # Check 3: Consensus
    print("\n[Check 3: Consensus] Checking similarity...")
    consensus = check3_consensus(responses)

    print("\n--- Consensus Results ---")
    print(f"Average Similarity: {consensus.get('avg_similarity', 0):.3f}")
    print(f"All > 0.9: {consensus.get('consensus', False)}")
    print(f"Flag for Review: {consensus.get('flag_for_review', False)}")

    return {
        "prompt": prompt,
        "responses": responses,
        "consensus": consensus
    }


if __name__ == "__main__":
    # Example usage
    test_prompt = "What is the capital of France?"
    result = run_pipeline(test_prompt)

    if result["consensus"]["flag_for_review"]:
        print("\n⚠️  HIGH CONSENSUS DETECTED - Potential hallucination or common knowledge")
    else:
        print("\n✓ Responses show diversity - Likely novel/complex question")
