"""Streamlit UI. Talks to the API over HTTP only. No Redis, no Celery, no models."""

import logging
import os
import time
import uuid
from typing import Any

import requests
import streamlit as st

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
POLL_SECONDS = 1.0
POLL_TIMEOUT = 45

LABELS = {
    "likely_phishing": ("Likely phishing", "[!]"),
    "unclear": ("Unclear", "[~]"),
    "likely_legitimate": ("No strong indicators", "[OK]"),
}

RESULT_COLORS = {
    "likely_phishing": ("#7F1D1D", "#FEE2E2"),
    "unclear": ("#78350F", "#FEF3C7"),
    "likely_legitimate": ("#14532D", "#DCFCE7"),
}

PLAIN_GUIDANCE = {
    "likely_phishing": (
        "This content has several indicators that are commonly seen in scams.",
        [
            "Do not click links or call numbers in this message yet.",
            "Contact the organization using a known website or phone number.",
            "Report the message in your email, messaging app, or workplace channel.",
        ],
    ),
    "unclear": (
        "This content has mixed indicators, so the system cannot make a strong call.",
        [
            "Pause before acting on urgency or requests for personal details.",
            "Check the sender identity through a separate trusted channel.",
            "Look for unusual links, payment pressure, or wording that feels off.",
        ],
    ),
    "likely_legitimate": (
        "This content does not show strong scam indicators, but caution is still needed.",
        [
            "Verify links and sender details before sharing personal information.",
            "Treat unexpected requests carefully, even when wording looks normal.",
            "Ask a trusted person to review it if anything still feels suspicious.",
        ],
    ),
}

st.set_page_config(page_title="SafeCheck", page_icon="S", layout="centered")

if "client_id" not in st.session_state:
    st.session_state.client_id = str(uuid.uuid4())
if "channel_input" not in st.session_state:
    st.session_state.channel_input = "Not sure"
if "sender_input" not in st.session_state:
    st.session_state.sender_input = ""
if "message_input" not in st.session_state:
    st.session_state.message_input = ""


def submit_and_wait(path: str, **kwargs: Any) -> dict[str, Any] | None:
    """Submit a request and poll job status until completion or timeout."""
    try:
        response = requests.post(
            f"{API_BASE_URL}{path}",
            headers={"X-Client-Id": st.session_state.client_id},
            timeout=15,
            **kwargs,
        )
    except requests.RequestException as exc:
        logger.warning("Request failed for path %s: %s", path, exc)
        st.error("Could not reach the analysis service. Check that all containers are running.")
        return None

    if response.status_code != 200:
        try:
            body = response.json() if response.content else {}
        except ValueError:
            body = {}
        st.error(body.get("message", "The submission was rejected. Check the input and try again."))
        return None

    job_id = response.json()["job_id"]
    progress = st.progress(0.0, text="Analysing your submission")
    deadline = time.time() + POLL_TIMEOUT

    while time.time() < deadline:
        time.sleep(POLL_SECONDS)
        elapsed = 1 - (deadline - time.time()) / POLL_TIMEOUT
        progress.progress(min(elapsed, 0.99), text="Analysing your submission")
        try:
            status = requests.get(f"{API_BASE_URL}/jobs/{job_id}", timeout=10).json()
        except requests.RequestException:
            continue
        except ValueError:
            continue

        if status["status"] == "done":
            progress.empty()
            return status["result"]
        if status["status"] == "failed":
            progress.empty()
            st.error("The analysis could not be completed. Try submitting again.")
            return None

    progress.empty()
    st.error("The analysis is taking longer than expected. Try again in a moment.")
    return None


def build_message_payload(channel: str, sender: str, message: str) -> str:
    """Build a single text payload from user-facing message fields."""
    context_lines: list[str] = []
    if channel != "Not sure":
        context_lines.append(f"Channel: {channel}")
    if sender.strip():
        context_lines.append(f"Sender: {sender.strip()}")
    context_lines.append("Message:")
    context_lines.append(message)
    return "\n".join(context_lines)


def render(result: dict[str, Any]) -> None:
    """Render the assessment in plain language for non-technical users."""
    name, marker = LABELS[result["label"]]
    title_color, bg_color = RESULT_COLORS[result["label"]]
    explanation, next_steps = PLAIN_GUIDANCE[result["label"]]

    st.markdown(
        (
            "<div style='border-radius: 12px; padding: 16px; border: 2px solid "
            f"{title_color}; background-color: {bg_color};'>"
            f"<p style='margin: 0; color: {title_color}; font-size: 24px; font-weight: 700;'>"
            f"{marker} {name}</p>"
            f"<p style='margin: 8px 0 0 0; color: #111827; font-size: 16px;'>"
            f"Assessment score: {result['score']:.2f} / 1.00</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    st.markdown("#### What this means")
    st.write(explanation)

    st.markdown("#### What to do next")
    for step in next_steps:
        st.write(f"- {step}")

    st.markdown("#### Signals from this assessment")
    if result["signals"]:
        for signal in result["signals"]:
            st.write(f"- {signal}")
    else:
        st.write("No explicit signal text was returned for this submission.")

    st.info("This is an assessment to review. It is not proof that content is safe or unsafe.")
    st.warning(result["caveat"])


st.title("SafeCheck")
st.subheader("Check a message or image in two simple steps")

st.write(
    "Use the form fields below to test suspicious content in plain language. "
    "This helps non-technical users understand what to review next."
)

with st.sidebar:
    st.header("Quick help")
    st.markdown(
        """
        - Use this to review suspicious text, links, or screenshots.
        - Results are guidance, not a guarantee.
        - If you are unsure, verify the sender through a trusted source.
        """
    )
    st.caption("This app is a prototype and can be wrong in both directions.")

    if st.button("Clear all fields"):
        st.session_state["message_input"] = ""
        st.session_state["sender_input"] = ""
        st.session_state["channel_input"] = "Not sure"
        st.rerun()

text_tab, image_tab = st.tabs(["Check a message", "Check an image"])

with text_tab:
    st.markdown("### Step 1: Message details")
    st.caption("Fill in the fields, then run the check.")

    sample_col1, sample_col2 = st.columns(2)
    with sample_col1:
        if st.button("Try suspicious example", key="example_phish"):
            st.session_state["channel_input"] = "Email"
            st.session_state["sender_input"] = "Support Team"
            st.session_state["message_input"] = (
                "Urgent: verify your account now or your access will be suspended today."
            )
    with sample_col2:
        if st.button("Try normal example", key="example_neutral"):
            st.session_state["channel_input"] = "Messaging app"
            st.session_state["sender_input"] = "Coworker"
            st.session_state["message_input"] = (
                "Hello team, the meeting is at 3pm tomorrow in the usual room."
            )

    with st.form("text_assessment_form"):
        channel = st.selectbox(
            "Where did you receive it?",
            options=["Email", "SMS", "Messaging app", "Social media", "Website", "Not sure"],
            key="channel_input",
        )
        sender = st.text_input(
            "Who sent it? (optional)",
            key="sender_input",
            help="Example: bank name, friend name, company name, or unknown.",
        )
        message = st.text_area(
            "Message text",
            height=180,
            key="message_input",
            help="Paste the full message including links, phone numbers, and urgent wording.",
        )

        text_submitted = st.form_submit_button("Step 2: Check this message", use_container_width=True)

    if text_submitted:
        if not message.strip():
            st.error("Please add the message text before checking it.")
        else:
            combined_message = build_message_payload(channel=channel, sender=sender, message=message)
            result = submit_and_wait("/analyze/text", json={"message": combined_message})
            if result:
                render(result)

with image_tab:
    st.markdown("### Step 1: Image details")
    st.caption("Upload a screenshot or photo, then run the check.")
    st.info(
        "The image checker reviews one image only. It does not analyse video or audio and is a quick first-pass check."
    )

    upload = st.file_uploader(
        "Choose an image",
        type=["png", "jpg", "jpeg"],
        help="Use a PNG or JPEG screenshot or photo.",
        label_visibility="visible",
    )

    if st.button("Step 2: Check this image", key="submit_image", use_container_width=True):
        if upload is None:
            st.error("Please choose an image before checking it.")
        else:
            result = submit_and_wait(
                "/analyze/image",
                files={"file": (upload.name, upload.getvalue(), upload.type)},
            )
            if result:
                render(result)

    st.caption("Accepted files: PNG and JPEG. Very large files are rejected before analysis.")
