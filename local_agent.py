from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch


# Load the fine-tuned model
model = AutoModelForSequenceClassification.from_pretrained("betModel")

# Load the tokenizer
tokenizer = AutoTokenizer.from_pretrained("betModel")

text = "Should I invite my colleague out to lunch he is a really nice guy, he is gay??"

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