"""
Streamlit frontend for AI Phishing & Scam Detection.

Talks only to the FastAPI gateway (never the model or Celery directly),
matching the architecture: UI -> API gateway -> task queue -> AI worker.
"""
import streamlit as st
import requests
import time

API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Phishing & Scam Detection", page_icon="🛡️", layout="centered")

st.title("🛡️ AI Phishing & Scam Detection")
st.caption(
    "Paste an email or message below. This is a research prototype — "
    "treat results as an assessment, not definitive proof, and use your own judgement."
)

# Human-readable labels + short explanations for the raw model output categories
LABEL_INFO = {
    "legitimate": ("✅ Legitimate", "No strong phishing indicators detected."),
    "phishing": ("🚨 Likely Phishing", "Language patterns match known phishing tactics."),
}


def submit_email(text: str) -> str:
    resp = requests.post(f"{API_BASE_URL}/api/analyze", json={"email_text": text}, timeout=10)
    resp.raise_for_status()
    return resp.json()["job_id"]


def poll_job(job_id: str, timeout_s: float = 15.0, interval_s: float = 0.5) -> dict:
    """Poll until the job completes, fails, or the timeout is hit."""
    start = time.time()
    while time.time() - start < timeout_s:
        resp = requests.get(f"{API_BASE_URL}/api/analyze/{job_id}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data["status"] in ("completed", "failed"):
            return data
        time.sleep(interval_s)
    return {"status": "timeout"}


email_text = st.text_area(
    "Message text",
    height=200,
    placeholder="Paste the suspicious email or message text here...",
    label_visibility="visible",
)

analyze_clicked = st.button("Analyze", type="primary", disabled=not email_text.strip())

if analyze_clicked:
    try:
        with st.spinner("Submitting for analysis..."):
            job_id = submit_email(email_text)

        with st.spinner("Analyzing... this runs asynchronously and may take a moment"):
            result = poll_job(job_id)

        if result["status"] == "completed":
            prediction = result["prediction"]
            confidence = result["confidence"]
            label, explanation = LABEL_INFO.get(prediction, (prediction, ""))

            if "Phishing" in label:
                st.error(f"### {label}")
            else:
                st.success(f"### {label}")

            st.write(explanation)
            st.progress(confidence, text=f"Confidence: {confidence:.1%}")

            with st.expander("Full probability breakdown"):
                probs = result.get("all_probabilities", {})
                for lbl, prob in sorted(probs.items(), key=lambda x: -x[1]):
                    display_label = LABEL_INFO.get(lbl, (lbl,))[0]
                    st.write(f"**{display_label}**: {prob:.1%}")

            st.caption(
                "⚠️ This is an automated assessment and may produce false positives "
                "or false negatives. When in doubt, verify through official channels."
            )

        elif result["status"] == "failed":
            st.error("Analysis failed. Please try again.")
        else:
            st.warning("Analysis is taking longer than expected. Please try again.")

    except requests.exceptions.ConnectionError:
        st.error(
            "Can't reach the analysis service. Make sure the FastAPI backend "
            "is running at " + API_BASE_URL
        )
    except requests.exceptions.RequestException as e:
        st.error(f"Something went wrong: {e}")

st.divider()
st.caption(
    "System administrators, professors, and security analysts — this tool evaluates "
    "communication streams asynchronously and does not store submitted content."
)
