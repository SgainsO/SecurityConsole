"""Local Security Agent for on-premise security filtering."""

import os
from typing import Optional
from pydantic import BaseModel
from presidio_analyzer import AnalyzerEngine

from .misuse_detector import MisuseDetector, temp_return_sd_flag


# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    pii_status: str
    slm_flag: str
    malicious_flag: str


class LocalSecurityAgent:
    """
    On-premise security agent that performs PII detection and local model-based
    classification for sensitive data and malicious intent detection.
    """

    def __init__(self, model_path: str = "betModel"):
        """
        Initialize the local security agent.

        Args:
            model_path: Path to the fine-tuned misuse detection model
        """
        # Initialize Presidio Analyzer for PII detection
        self.analyzer = AnalyzerEngine()
        print("Presidio Analyzer engine initialized.")

        # Initialize misuse detector model
        print("Initializing MisuseDetector model...")
        self.misuse_detector = MisuseDetector(model_path=model_path)
        print("LocalSecurityAgent initialization complete.")

    async def check_query(
        self,
        query: str,
        entities_to_filter: Optional[list] = None
    ) -> QueryResponse:
        """
        Process a query through the security pipeline: PII check, then local model-based checks.

        Args:
            query: The user query to check
            entities_to_filter: List of PII entity types to detect. If None, uses default set.

        Returns:
            QueryResponse with security check results
        """
        # Default PII entities to filter
        if entities_to_filter is None:
            entities_to_filter = [
                "PHONE_NUMBER",
                "EMAIL_ADDRESS",
                "US_SSN",
                "CREDIT_CARD"
            ]

        # Module 1: PII Check
        pii_results = self.analyzer.analyze(
            text=query,
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

        # Module 2: Malicious Intent Detection (using local model)
        malicious_result = self.misuse_detector.classify(query)
        malicious_flag = malicious_result.get("data", "ERROR")

        # Module 3: Sensitive Data Flag (temporary implementation)
        # TODO: Replace with actual sensitive data detection model
        slm_result = temp_return_sd_flag()
        slm_flag = slm_result.get("data", "ERROR")

        return QueryResponse(
            pii_status="ACCEPT",
            slm_flag=slm_flag,
            malicious_flag=malicious_flag
        )

    def get_status(self) -> dict:
        """Get the current status of the local agent."""
        return {
            "service": "local_agent",
            "status": "operational",
            "components": {
                "presidio_analyzer": "active",
                "misuse_detector": "active"
            }
        }

