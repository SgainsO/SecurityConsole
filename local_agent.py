from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

options = {0: "ACCEPT", 1: "BLOCK", 2: "FLAG"}


def dertModel(input: str): 
    # Load the fine-tuned model
    model = AutoModelForSequenceClassification.from_pretrained("betModel")

    # Load the tokenizer
    tokenizer = AutoTokenizer.from_pretrained("betModel")

    text = input

    # tokenize
    inputs = tokenizer(text, return_tensors="pt")

    # forward pass
    with torch.no_grad():
        outputs = model(**inputs)

    # logits → probabilities
    probs = torch.softmax(outputs.logits, dim=1)

    # predicted label
    pred_label = torch.argmax(probs).item()

    print("Label:", pred_label)
    print("Probabilities:", probs)

    return {"data": {"TYPE": "STRING","ENUM": options[pred_label]}}