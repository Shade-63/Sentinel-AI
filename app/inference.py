import torch
import os
import re
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, "models", "sentinel_model")

tokenizer = DistilBertTokenizerFast.from_pretrained(model_path)
model = DistilBertForSequenceClassification.from_pretrained(model_path)

model.eval()

# Rule-based scam indicators (high confidence patterns)
SCAM_SIGNAL_LABELS = [
    ("arrest or legal authority threat", r'\b(arrest|warrant|fbi|cbi|irs|enforcement|legal action)\b'),
    ("urgency / time pressure",          r'\b(urgent|immediate|now|today|within \d+ (hours?|minutes?))\b'),
    ("payment demand with urgency",      r'\b(pay|payment|transfer|wire|funds?|money)\b.*\b(immediate|now|urgent)\b'),
    ("phishing link / click-bait",       r'\b(click|verify|confirm).*\b(link|here|now)\b'),
    ("account suspension threat",        r'\b(suspended|blocked|frozen|invalid).*\b(account|card|number)\b'),
    ("prize / lottery scam",             r'\b(won|prize|lottery|claim)\b'),
    ("credential / remote access request", r'\b(otp|password|remote access|teamviewer|anydesk)\b'),
    ("digital arrest pattern",           r'\b(digital arrest|stay on (the )?line)\b'),
    ("isolation / secrecy demand",       r'\b(do not (disconnect|tell|go to))\b'),
    ("document / ID fraud",              r'\b(aadhaar|sim|passport|visa).*\b(illegal|invalid|blocked)\b'),
]

SAFE_KEYWORDS = [
    r'\b(official public advisory|government agencies do not)\b',
    r'\b(legitimate authority|verifiable credentials)\b',
    r'\b(official portal|registered mail|written documentation)\b',
    r'\b(meeting|agenda|schedule|call|project)\b',
    r'\b(hello|hi|how are you)\b',
]


def predict(text):
    text_lower = text.lower()


    # Rule-based scoring
    scam_score = 0
    safe_score = 0
    matched_signals = []

    for label, pattern in SCAM_SIGNAL_LABELS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            scam_score += 1
            matched_signals.append(label.capitalize())

    for pattern in SAFE_KEYWORDS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            safe_score += 1

    # If strong rule-based signal, use it
    if scam_score >= 2:
        scam_prob = min(0.85 + (scam_score * 0.05), 0.99)
        safe_prob = max(0.15 - (scam_score * 0.05), 0.01)
        return {
            "label": "SCAM",
            "scam_probability": round(scam_prob, 4),
            "safe_probability": round(safe_prob, 4),
            "risk_level": "HIGH",
            "signals": matched_signals,
        }
    elif safe_score >= 1 and scam_score == 0:
        return {
            "label": "SAFE",
            "scam_probability": 0.15,
            "safe_probability": 0.85,
            "risk_level": "LOW",
            "signals": [],
        }

    # Otherwise, use model prediction
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    probabilities = torch.softmax(logits, dim=1)

    scam_prob = probabilities[0][1].item()
    safe_prob = probabilities[0][0].item()

    # Adjust probabilities based on rule scores
    if scam_score > 0:
        scam_prob = min(scam_prob + (scam_score * 0.1), 0.95)
        safe_prob = 1 - scam_prob
    elif safe_score > 0:
        safe_prob = min(safe_prob + (safe_score * 0.1), 0.95)
        scam_prob = 1 - safe_prob

    label = "SCAM" if scam_prob > 0.5 else "SAFE"

    if label == "SCAM":
        risk_level = "HIGH" if scam_prob >= 0.75 else "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "label": label,
        "scam_probability": round(scam_prob, 4),
        "safe_probability": round(safe_prob, 4),
        "risk_level": risk_level,
        "signals": matched_signals,
    }