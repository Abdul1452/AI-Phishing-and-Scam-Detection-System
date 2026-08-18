"""
Phishing detection model interface.

This module exposes ONE function, `predict_email`, with a fixed contract:

    predict_email(text: str) -> dict:
        {
            "prediction": str,            # "phishing" | "legitimate"
            "confidence": float,          # 0.0 - 1.0
            "all_probabilities": dict,    # {"phishing": p, "legitimate": p}
        }

Using: ElSlay/BERT-Phishing-Email-Model (binary BERT classifier).
Team decision: replaced the earlier cybersectony DistilBERT candidate after
comparing both on tests/compare_models.py — see project notes for rationale.

NOTE: model weights (~420MB) download from huggingface.co on first run and
are cached locally afterward (~/.cache/huggingface by default). First call
will be slow; subsequent calls are fast.
"""
from transformers import BertForSequenceClassification, BertTokenizer
import torch

MODEL_NAME = "ElSlay/BERT-Phishing-Email-Model"

print(f"[phishing_model] loading {MODEL_NAME} ...")
_tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
_model = BertForSequenceClassification.from_pretrained(MODEL_NAME)
_model.eval()
print("[phishing_model] model loaded.")


def predict_email(email_text: str) -> dict:
    inputs = _tokenizer(
        email_text,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=512,
    )
    with torch.no_grad():
        outputs = _model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=-1)[0].tolist()
        pred_idx = torch.argmax(logits, dim=-1).item()

    # model card: 1 = Phishing, 0 = Legitimate
    all_probabilities = {
        "legitimate": round(probs[0], 4),
        "phishing": round(probs[1], 4),
    }
    prediction = "phishing" if pred_idx == 1 else "legitimate"
    confidence = round(probs[pred_idx], 4)

    return {
        "prediction": prediction,
        "confidence": confidence,
        "all_probabilities": all_probabilities,
    }
