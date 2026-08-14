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

        if any(token in label_name for token in ("spam", "phishing", "positive", "label_1", "1")):
            malicious_score = score
        elif any(token in label_name for token in ("legit", "ham", "negative", "label_0", "0")):
            malicious_score = max(0.0, 1.0 - score)
        else:
            malicious_score = score

        signals = (
            ["model detected suspicious language patterns"]
            if malicious_score >= 0.5
            else ["no strong suspicious language patterns"]
        )
        return float(min(max(malicious_score, 0.0), 1.0)), signals


class ImageChecker:
    """Single-frame manipulation check. Low confidence by design."""

    def __init__(self, model_id: str | None = None) -> None:
        self.model_id = model_id or settings.image_model_id or "google/vit-base-patch16-224"
        self._pipeline: Any = None

    def load(self) -> None:
        try:
            from transformers import pipeline
        except ImportError:
            logger.warning(
                "transformers not installed; image model remains unloaded for offline test mode: model_id=%s",
                self.model_id,
            )
            self._pipeline = None
            return

        self._pipeline = pipeline("image-classification", model=self.model_id)
        logger.info("image checker loaded model_id=%s", self.model_id)

    def predict(self, image_bytes: bytes) -> tuple[float, list[str]]:
        if self._pipeline is None:
            raise RuntimeError("model not loaded")

        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        raw_output = self._pipeline(image)
        score, label = _max_score_and_label(raw_output)
        label_name = _normalise_label(label)

        suspicious_score = score
        if not any(token in label_name for token in ("manip", "edited", "fake", "tamper", "spoof", "anomaly", "suspicious")):
            suspicious_score = score * 0.65

        signals = (
            ["visual content appears suspicious or manipulated"]
            if suspicious_score >= 0.5
            else ["visual content appears consistent with a normal single frame"]
        )
        return float(min(max(suspicious_score, 0.0), 1.0)), signals


text_classifier = TextClassifier()
image_checker = ImageChecker()
