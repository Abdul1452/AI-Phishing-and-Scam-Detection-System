"""Submission guards: size, type, and repeated near-identical inputs."""

import logging

from rapidfuzz.fuzz import ratio

from app.common.config import settings

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg"}


class SimilarityGuard:
    """Blocks a client that submits the same input over and over with small edits.

    This stops a naive mutation script hammering one client session. It does not
    stop an attacker who varies inputs meaningfully or rotates sessions.
    """

    def __init__(self) -> None:
        self._history: dict[str, list[str]] = {}
        self._strikes: dict[str, int] = {}

    def check(self, client_id: str, payload: str) -> bool:
        """Return True if the submission should be blocked."""
        recent = self._history.setdefault(client_id, [])
        near_duplicate = any(
            ratio(payload, seen) / 100.0 >= settings.similarity_threshold for seen in recent
        )
        if near_duplicate:
            self._strikes[client_id] = self._strikes.get(client_id, 0) + 1
        else:
            self._strikes[client_id] = 0

        recent.append(payload)
        del recent[: max(0, len(recent) - settings.similarity_window)]

        blocked = self._strikes.get(client_id, 0) >= settings.similarity_strikes
        if blocked:
            logger.warning("similarity guard blocked client=%s", client_id)
        return blocked

    def reset(self) -> None:
        self._history.clear()
        self._strikes.clear()


similarity_guard = SimilarityGuard()
