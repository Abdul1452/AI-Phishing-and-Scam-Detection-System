"""Streamlit UI. Talks to the API over HTTP only. No Redis, no Celery, no models."""

import os
import time
import uuid

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
POLL_SECONDS = 1.0
POLL_TIMEOUT = 45

LABELS = {
    "likely_phishing": ("Likely phishing", "▲"),
    "unclear": ("Unclear", "■"),
    "likely_legitimate": ("No strong indicators", "●"),
}

st.set_page_config(page_title="Phishing and scam assessment", layout="centered")

if "client_id" not in st.session_state:
    st.session_state.client_id = str(uuid.uuid4())


def submit_and_wait(path: str, **kwargs) -> dict | None:
    try:
        response = requests.post(
            f"{API_BASE_URL}{path}",
            headers={"X-Client-Id": st.session_state.client_id},
            timeout=15,
            **kwargs,
        )
    except requests.RequestException:
        st.error("Could not reach the analysis service. Check that all containers are running.")
        return None

    if response.status_code != 200:
        body = response.json() if response.content else {}
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


def render(result: dict) -> None:
    name, mark = LABELS[result["label"]]
    st.subheader(f"{mark} {name}")
    st.write(f"Model score: {result['score']:.2f} out of 1.00")

    if result["signals"]:
        st.write("What the model reacted to:")
        for signal in result["signals"]:
            st.write(f"- {signal}")

    st.warning(result["caveat"])


st.title("Phishing and scam assessment")
st.write(
    "Submit a suspicious message or image. The system returns an assessment you should "
    "judge for yourself, not a decision about whether something is safe."
)

text_tab, image_tab = st.tabs(["Message text", "Image"])

with text_tab:
    message = st.text_area(
        "Message to check",
        height=180,
        help="Paste the full text of the message, including any links.",
    )
    if st.button("Check this message", key="submit_text"):
        if not message.strip():
            st.error("Enter a message before submitting.")
        else:
            result = submit_and_wait("/analyze/text", json={"message": message})
            if result:
                render(result)

with image_tab:
    st.info(
        "The image check is a single-frame, low-confidence prototype. It does not analyse "
        "video or audio, and it has not been evaluated on real-world data."
    )
    upload = st.file_uploader("Image to check", type=["png", "jpg", "jpeg"])
    if st.button("Check this image", key="submit_image"):
        if upload is None:
            st.error("Choose a PNG or JPEG image before submitting.")
        else:
            result = submit_and_wait(
                "/analyze/image",
                files={"file": (upload.name, upload.getvalue(), upload.type)},
            )
            if result:
                render(result)
