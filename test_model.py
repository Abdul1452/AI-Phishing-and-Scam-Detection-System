"""
Standalone validation of cybersectony/phishing-email-detection-distilbert_v2.4.1
Run this BEFORE building any infra around the model, to see how it actually behaves.
"""
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import time

MODEL_NAME = "cybersectony/phishing-email-detection-distilbert_v2.4.1"

print(f"Loading {MODEL_NAME} ...")
t0 = time.time()
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.eval()
print(f"Loaded in {time.time() - t0:.2f}s\n")


def predict_email(email_text: str) -> dict:
    inputs = tokenizer(email_text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
    probs = predictions[0].tolist()
    labels = {
        "legitimate_email": probs[0],
        "phishing_url": probs[1],
        "legitimate_url": probs[2],
        "phishing_url_alt": probs[3],
    }
    max_label = max(labels.items(), key=lambda x: x[1])
    return {"prediction": max_label[0], "confidence": max_label[1], "all_probabilities": labels}


# Test cases: mix of obvious, legit, and tricky ones
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

print("=" * 70)
for name, text in test_cases.items():
    result = predict_email(text)
    print(f"\n[{name}]")
    print(f"  -> prediction: {result['prediction']}  (confidence: {result['confidence']:.2%})")
    for label, prob in sorted(result["all_probabilities"].items(), key=lambda x: -x[1]):
        print(f"     {label:20s}: {prob:.2%}")
print("\n" + "=" * 70)
