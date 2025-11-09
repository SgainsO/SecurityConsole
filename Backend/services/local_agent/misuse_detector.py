"""Misuse detection model for identifying malicious intents in queries."""

from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
from typing import Dict


class MisuseDetector:
    """
    Optimized misuse detection model that loads once and can be reused for multiple predictions.
    This avoids reloading the model from disk on every inference call.
    """

    def __init__(self, model_path: str = "betModel"):
        """
        Initialize the detector by loading the model and tokenizer once.

        Args:
            model_path: Path to the fine-tuned model directory
        """
        print(f"Loading MisuseDetector model from {model_path}...")
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.options = {0: "ACCEPT", 1: "BLOCK", 2: "FLAG"}
        self.model.eval()  # Set to evaluation mode
        print("MisuseDetector model loaded successfully.")

    def classify(self, text: str) -> Dict[str, str]:
        """
        Classify the input text using the loaded model.

        Args:
            text: Input text to classify

        Returns:
            Dictionary with classification result: {"data": "ACCEPT"|"BLOCK"|"FLAG"}
        """
        # Tokenize
        inputs = self.tokenizer(text, return_tensors="pt")

        # Forward pass
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Logits → probabilities
        probs = torch.softmax(outputs.logits, dim=1)

        # Predicted label
        pred_label = torch.argmax(probs).item()

        print(f"Label: {pred_label} ({self.options[pred_label]})")
        print(f"Probabilities: {probs}")

        return {"data": self.options[pred_label]}


def temp_return_sd_flag() -> Dict[str, str]:
    """Temporary function that returns ACCEPT for sensitive data flag."""
    return {"data": "ACCEPT"}

