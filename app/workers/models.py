"""Model wrappers. Tests mock these classes, so no inference call belongs elsewhere.

Both wrappers are stubs. Replacing the body of predict() with a real Hugging Face
pipeline is the only change needed; nothing outside this file should move.
"""

import logging

from app.common.config import settings

logger = logging.getLogger(__name__)


class TextClassifier:
    """Phishing indicators in a text message."""

    def __init__(self, model_id: str | None = None) -> None:
        self.model_id = model_id or settings.text_model_id
        self._pipeline = None
        logger.info("text classifier constructed model_id=%s", self.model_id)

    def load(self) -> None:
        """Load once at worker start. Raise loudly here rather than at first request."""
        # TODO(implementer): replace with transformers.pipeline("text-classification", ...)
        self._pipeline = "stub"
        logger.info("text classifier loaded model_id=%s", self.model_id)

    def predict(self, message: str) -> tuple[float, list[str]]:
        """Return a score between 0 and 1 and human-readable signals."""
        if self._pipeline is None:
            raise RuntimeError("model not loaded")
        # Stub scoring so the pipeline is demonstrable before the real model lands.
        lowered = message.lower()
        signals: list[str] = []
        for phrase, note in (
            ("verify your account", "asks the reader to verify an account"),
            ("urgent", "uses urgency phrasing"),
            ("suspended", "threatens account suspension"),
            ("click here", "uses a non-descriptive link label"),
            ("password", "requests credentials"),
        ):
            if phrase in lowered:
                signals.append(note)
        score = min(0.15 + 0.2 * len(signals), 0.97)
        return score, signals


class ImageChecker:
    """Single-frame manipulation check. Low confidence by design."""

    def __init__(self, model_id: str | None = None) -> None:
        self.model_id = model_id or settings.image_model_id
        self._pipeline = None

    def load(self) -> None:
        # TODO(implementer): replace with a pretrained image-classification pipeline.
        self._pipeline = "stub"
        logger.info("image checker loaded model_id=%s", self.model_id or "<unset>")

    def predict(self, image_bytes: bytes) -> tuple[float, list[str]]:
        if self._pipeline is None:
            raise RuntimeError("model not loaded")
        return 0.5, ["single-frame check only, no manipulation signal available yet"]


text_classifier = TextClassifier()
image_checker = ImageChecker()
