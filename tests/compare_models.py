"""
Side-by-side comparison of two candidate phishing detection models:
  1. cybersectony/phishing-email-detection-distilbert_v2.4.1  (4-way multilabel)
  2. ElSlay/BERT-Phishing-Email-Model                          (binary phishing/legit)

Run this AFTER test_model.py has already validated model #1 individually.
This lets you compare predictions + confidence calibration on identical inputs.
"""
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    BertForSequenceClassification,
    BertTokenizer,
)
import torch
import time

# ---------------------------------------------------------------------------
# Model 1: cybersectony DistilBERT (4-way multilabel)
# ---------------------------------------------------------------------------
MODEL_1_NAME = "cybersectony/phishing-email-detection-distilbert_v2.4.1"

print(f"Loading model 1: {MODEL_1_NAME} ...")
t0 = time.time()
tok1 = AutoTokenizer.from_pretrained(MODEL_1_NAME)
model1 = AutoModelForSequenceClassification.from_pretrained(MODEL_1_NAME)
model1.eval()
print(f"  loaded in {time.time() - t0:.2f}s")


def predict_model1(email_text: str) -> dict:
    inputs = tok1(email_text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model1(**inputs)
        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
    probs = predictions[0].tolist()
    labels = {
        "legitimate_email": probs[0],
        "phishing_url": probs[1],
        "legitimate_url": probs[2],
        "phishing_url_alt": probs[3],
    }
    max_label = max(labels.items(), key=lambda x: x[1])
    # normalize to a simple phishing/legit verdict for comparison purposes
    is_phishing = "phishing" in max_label[0]
    return {
        "raw_label": max_label[0],
        "verdict": "PHISHING" if is_phishing else "LEGITIMATE",
        "confidence": max_label[1],
    }


# ---------------------------------------------------------------------------
# Model 2: ElSlay BERT (binary)
# ---------------------------------------------------------------------------
MODEL_2_NAME = "ElSlay/BERT-Phishing-Email-Model"

print(f"\nLoading model 2: {MODEL_2_NAME} ...")
t0 = time.time()
tok2 = BertTokenizer.from_pretrained(MODEL_2_NAME)
model2 = BertForSequenceClassification.from_pretrained(MODEL_2_NAME)
model2.eval()
print(f"  loaded in {time.time() - t0:.2f}s\n")


def predict_model2(email_text: str) -> dict:
    inputs = tok2(email_text, return_tensors="pt", truncation=True, padding="max_length", max_length=512)
    with torch.no_grad():
        outputs = model2(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=-1)[0].tolist()
        prediction = torch.argmax(logits, dim=-1).item()
    is_phishing = prediction == 1
    confidence = probs[prediction]
    return {
        "raw_label": "Phishing" if is_phishing else "Legitimate",
        "verdict": "PHISHING" if is_phishing else "LEGITIMATE",
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Test cases — same ones used in test_model.py for a fair comparison
# ---------------------------------------------------------------------------
test_cases = {
    "obvious_phishing": """
Dear Customer,
Your account has been suspended due to unusual activity. Verify your identity
immediately by clicking the link below or your account will be permanently closed.
http://secure-bankverify-login.tk/reset
""",
    "obvious_legit": """
Hi team,
Just a reminder that the sprint planning meeting is moved to 2pm tomorrow.
Please review the backlog beforehand. Thanks!
Sarah
""",
    "phishing_no_url": """
URGENT: This is your final notice. Your payroll deposit has failed and HR needs
you to confirm your bank details today by replying to this email with your
account number and routing number, or your next paycheck will be delayed.
""",
    "legit_with_url": """
Hey, here's the link to the shared doc we discussed in standup:
https://docs.google.com/document/d/abc123/edit
Let me know if you can't access it.
""",
    "subtle_phishing": """
Hi, this is IT support. We noticed your password hasn't been updated in a while
and company policy requires a refresh. Please log in here to update it:
http://it-portal-update.com/login
""",
    "short_ambiguous": "Please review and sign the attached document by EOD.",
}

# expected verdicts, for a quick agreement/accuracy readout on this small sample
expected = {
    "obvious_phishing": "PHISHING",
    "obvious_legit": "LEGITIMATE",
    "phishing_no_url": "PHISHING",
    "legit_with_url": "LEGITIMATE",
    "subtle_phishing": "PHISHING",
    "short_ambiguous": "LEGITIMATE",
}

print("=" * 90)
print(f"{'case':20s} | {'expected':11s} | {'model1 (DistilBERT)':28s} | {'model2 (BERT)':28s}")
print("=" * 90)

m1_correct = 0
m2_correct = 0
agree_count = 0

for name, text in test_cases.items():
    r1 = predict_model1(text)
    r2 = predict_model2(text)

    exp = expected[name]
    m1_ok = "✓" if r1["verdict"] == exp else "✗"
    m2_ok = "✓" if r2["verdict"] == exp else "✗"
    agree = r1["verdict"] == r2["verdict"]

    if r1["verdict"] == exp:
        m1_correct += 1
    if r2["verdict"] == exp:
        m2_correct += 1
    if agree:
        agree_count += 1

    m1_str = f"{r1['verdict']} {m1_ok} ({r1['confidence']:.1%})"
    m2_str = f"{r2['verdict']} {m2_ok} ({r2['confidence']:.1%})"

    print(f"{name:20s} | {exp:11s} | {m1_str:28s} | {m2_str:28s}")

print("=" * 90)
print(f"\nModel 1 (DistilBERT) correct: {m1_correct}/{len(test_cases)}")
print(f"Model 2 (BERT):        correct: {m2_correct}/{len(test_cases)}")
print(f"Models agreed on:              {agree_count}/{len(test_cases)} cases")
print("\nNote: this is a tiny, hand-picked sample — not a real accuracy benchmark.")
print("Use it to sanity-check behavior and calibration, not to declare a 'winner'.")
