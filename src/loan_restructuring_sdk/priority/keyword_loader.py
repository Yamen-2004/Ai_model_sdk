"""Loads the HIGH/MEDIUM/LOW keyword lists that drive `KeywordPriorityRule`.

Kept as its own class, separate from the rule's matching logic, so the
keyword *source* (today: a JSON file on disk) can be swapped -- a different
path, eventually a database or admin UI -- without touching
`KeywordPriorityRule` or `PriorityEngine` (docs/SDD.md Design Decision D8).
"""

from __future__ import annotations

import json
from pathlib import Path

from loan_restructuring_sdk.utils.exceptions import KeywordConfigurationError

DEFAULT_KEYWORDS_PATH = Path(__file__).resolve().parent / "data" / "priority_keywords.json"

_LEVELS = ("HIGH", "MEDIUM", "LOW")


class KeywordLoader:
    """Reads and validates the priority keyword configuration file."""

    def __init__(self, keywords_path: Path = DEFAULT_KEYWORDS_PATH) -> None:
        self._keywords_path = keywords_path

    def load(self) -> dict[str, list[str]]:
        """Return the HIGH/MEDIUM/LOW keyword lists, or raise `KeywordConfigurationError`."""
        if not self._keywords_path.is_file():
            raise KeywordConfigurationError(
                f"Priority keyword configuration file not found: {self._keywords_path}"
            )

        try:
            raw_text = self._keywords_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise KeywordConfigurationError(
                f"Could not read priority keyword configuration file: {self._keywords_path}"
            ) from exc

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise KeywordConfigurationError(
                f"Priority keyword configuration file is not valid JSON: {self._keywords_path}"
            ) from exc

        if not isinstance(data, dict):
            raise KeywordConfigurationError(
                f"Priority keyword configuration must be a JSON object, got {type(data).__name__}: "
                f"{self._keywords_path}"
            )

        keywords_by_level: dict[str, list[str]] = {}
        for level in _LEVELS:
            values = data.get(level, [])
            if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
                raise KeywordConfigurationError(
                    f"Priority keyword configuration key '{level}' must be a list of strings: "
                    f"{self._keywords_path}"
                )
            keywords_by_level[level] = values
        return keywords_by_level
