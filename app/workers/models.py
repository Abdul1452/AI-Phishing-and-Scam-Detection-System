"""Model wrappers. Tests mock these classes, so no inference call belongs elsewhere."""

import io
import logging
from typing import Any

from app.common.config import settings

logger = logging.getLogger(__name__)


def _normalise_label(label: Any) -> str:
    return str(label or "").strip().lower().replace(" ", "_")


def _max_score_and_label(result: Any) -> tuple[float, str]:
    if isinstance(result, dict):
        candidates = [result]
    elif isinstance(result, list):
        if result and isinstance(result[0], list):
            candidates = result[0]
        else:
            candidates = result
    else:
        return 0.5, "unknown"

    best_score = 0.5
    best_label = "unknown"
    for item in candidates:
        if not isinstance(item, dict):
            continue
        score = float(item.get("score", 0.0))
        label = str(item.get("label", "unknown"))
        if score > best_score:
            best_score = score
            best_label = label
    return best_score, best_label


class TextClassifier:
    """Phishing indicators in a text message."""

    def __init__(self, model_id: str | None = None) -> None:
        self.model_id = model_id or settings.text_model_id
        self._pipeline: Any = None
        logger.info("text classifier constructed model_id=%s", self.model_id)

    def load(self) -> None:
        """Load the text-classification pipeline once at worker startup."""
        try:
            from transformers import pipeline
        except ImportError:
            logger.warning(
                "transformers not installed; text model remains unloaded for offline test mode: model_id=%s",
                self.model_id,
            )
            self._pipeline = None
            return

        self._pipeline = pipeline("text-classification", model=self.model_id, truncation=True)
        logger.info("text classifier loaded model_id=%s", self.model_id)

    def predict(self, message: str) -> tuple[float, list[str]]:
        """Return a score between 0 and 1 and human-readable signals."""
        if self._pipeline is None:
            raise RuntimeError("model not loaded")

        raw_output = self._pipeline(message, truncation=True)
        score, label = _max_score_and_label(raw_output)
        label_name = _normalise_label(label)

        malicious_labels = {"label_1"}
        legitimate_labels = {"label_0"}

        if label_name in malicious_labels:
            malicious_score = score
        elif label_name in legitimate_labels:
            malicious_score = max(0.0, 1.0 - score)
        else:
            logger.warning("unrecognized label from text model: %r", label_name)
            malicious_score = score

        signals = (
            ["model detected suspicious language patterns"]
            if malicious_score >= 0.5
            else ["no strong suspicious language patterns"]
        )
        return float(min(max(malicious_score, 0.0), 1.0)), signals


class ImageChecker:
    """OCR-based phishing check using the existing text classifier."""

    def __init__(self, model_id: str | None = None) -> None:
        # Kept for compatibility with the existing model wrapper/tests.
        self.model_id = model_id or settings.image_model_id
        self._reader: Any = None

    def load(self) -> None:
        """Load the OCR reader once at worker startup."""
        try:
            import easyocr
        except ImportError:
            logger.warning(
                "easyocr not installed; image checker remains unloaded for offline test mode"
            )
            self._reader = None
            return

        self._reader = easyocr.Reader(["en"], gpu=False)
        logger.info("image OCR reader loaded")

    def predict(self, image_bytes: bytes) -> tuple[float, list[str]]:
        """Extract text from an image and classify it with the phishing text model."""
        if self._reader is None:
            raise RuntimeError("image OCR reader not loaded")

        import numpy as np
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_array = np.array(image)

        results = self._reader.readtext(image_array)

        extracted_text = " ".join(
            text.strip()
            for _, text, confidence in results
            if text.strip() and confidence >= 0.30
        ).strip()

        if not extracted_text:
            return 0.5, ["no readable text detected in image"]

        try:
            score, text_signals = text_classifier.predict(extracted_text)
        except Exception:
            logger.exception("OCR text classification failed")
            return 0.5, ["image text could not be classified"]

        signals = [
            "OCR extracted text from the image",
            *text_signals,
        ]

        return float(min(max(score, 0.0), 1.0)), signals


text_classifier = TextClassifier()
image_checker = ImageChecker()
