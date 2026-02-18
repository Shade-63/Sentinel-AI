from inference import predict
import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
import os

# Load model directly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, "models", "sentinel_model")

tokenizer = DistilBertTokenizerFast.from_pretrained(model_path)
model = DistilBertForSequenceClassification.from_pretrained(model_path)
model.eval()

# Test with explicit examples
test_cases = [
    ("FBI warrant arrest immediate payment", "SCAM"),
    ("meeting agenda for tomorrow", "SAFE"),
    ("Hello, how are you?", "SAFE"),
    ("Click here to claim your prize", "SCAM")
]

print("="*70)
print("DETAILED MODEL DIAGNOSIS")
print("="*70)

for text, expected in test_cases:
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    logits = outputs.logits
    probabilities = torch.softmax(logits, dim=1)
    
    # Check raw logits and probabilities
    print(f"\nText: '{text}'")
    print(f"Expected: {expected}")
    print(f"Raw logits: {logits[0].tolist()}")
    print(f"Probabilities: [SAFE={probabilities[0][0].item():.4f}, SCAM={probabilities[0][1].item():.4f}]")
    
    # Current prediction logic
    scam_prob = probabilities[0][1].item()
    safe_prob = probabilities[0][0].item()
    label = "SCAM" if scam_prob > 0.5 else "SAFE"
    
    print(f"Predicted: {label}")
    print(f"Match: {'✓' if label == expected else '✗'}")

print("\n" + "="*70)
print("CHECKING MODEL CONFIG")
print("="*70)
print(f"Model config: {model.config}")
print(f"Number of labels: {model.config.num_labels}")
print(f"Label mapping: {model.config.id2label if hasattr(model.config, 'id2label') else 'Not set'}")
