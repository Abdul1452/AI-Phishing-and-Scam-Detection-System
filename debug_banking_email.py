"""
Debug script: trace the exact banking-phishing email through the real,
deployed phishing_model.predict_email() — no FastAPI, no Celery, no UI,
no threshold banding. This isolates whether the "Unclear" / 0.58 result
comes from the model itself or from the label-bucketing logic downstream.

Run this from the project root, inside the venv:
    python debug_banking_email.py
"""

# Adjust this import path if phishing_model.py doesn't live at app/models/
from app.models.phishing_model import predict_email

banking_phishing_email = """Dear account holder,
There has been a recent login to your bank account from a new divice:
I P  address: 192.168.0.1
Location: Miami, Florida
4 new transactions have been made with this account since your last login.

If this was not you, please reset your password immediately with this link:
https://trust.ameribank7.com/reset-password
Thank you,
Bank America"""

# A couple of comparison cases for context — same style, more/less obvious
comparison_cases = {
    "your_banking_email": banking_phishing_email,
    "generic_template_phishing": (
        "Dear Customer, your account has been suspended due to unusual "
        "activity. Verify your identity immediately by clicking the link "
        "below or your account will be permanently closed. "
        "http://secure-bankverify-login.tk/reset"
    ),
    "obvious_legit": (
        "Hi team, just a reminder that the sprint planning meeting is "
        "moved to 2pm tomorrow. Please review the backlog beforehand. Thanks!"
    ),
}

print("=" * 78)
for name, text in comparison_cases.items():
    result = predict_email(text)
    print(f"\n[{name}]")
    print(f"  raw prediction : {result['prediction']}")
    print(f"  raw confidence : {result['confidence']:.4f}")
    print(f"  probabilities  : {result['all_probabilities']}")
print("\n" + "=" * 78)
print(
    "\nIf 'your_banking_email' shows phishing probability well above 0.58 here,\n"
    "the model itself is fairly confident and something in the pipeline\n"
    "(threshold banding, score field mapping, or the request payload sent to\n"
    "the API) is losing signal before it reaches the UI.\n"
    "\nIf phishing probability is genuinely close to 0.58 here too, the model\n"
    "itself is the source of the uncertainty on this specific style of email."
)
