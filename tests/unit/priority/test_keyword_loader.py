"""Unit tests for `KeywordLoader` -- reading/validating priority_keywords.json."""

from pathlib import Path

import pytest

from loan_restructuring_sdk.priority.keyword_loader import DEFAULT_KEYWORDS_PATH, KeywordLoader
from loan_restructuring_sdk.utils.exceptions import KeywordConfigurationError


def _write(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "priority_keywords.json"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_returns_keyword_lists_by_level(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        '{"HIGH": ["فقدان الوظيفة"], "MEDIUM": ["مولود"], "LOW": ["استثمار"]}',
    )

    result = KeywordLoader(path).load()

    assert result == {
        "HIGH": ["فقدان الوظيفة"],
        "MEDIUM": ["مولود"],
        "LOW": ["استثمار"],
    }


def test_load_defaults_a_missing_level_to_an_empty_list(tmp_path: Path) -> None:
    path = _write(tmp_path, '{"HIGH": ["فصل"]}')

    result = KeywordLoader(path).load()

    assert result == {"HIGH": ["فصل"], "MEDIUM": [], "LOW": []}


def test_load_raises_when_file_does_not_exist(tmp_path: Path) -> None:
    missing_path = tmp_path / "does_not_exist.json"

    with pytest.raises(KeywordConfigurationError):
        KeywordLoader(missing_path).load()


def test_load_raises_on_invalid_json(tmp_path: Path) -> None:
    path = _write(tmp_path, "{not valid json")

    with pytest.raises(KeywordConfigurationError):
        KeywordLoader(path).load()


def test_load_raises_when_top_level_json_is_not_an_object(tmp_path: Path) -> None:
    path = _write(tmp_path, '["فصل", "مرض"]')

    with pytest.raises(KeywordConfigurationError):
        KeywordLoader(path).load()


def test_load_raises_when_a_level_is_not_a_list_of_strings(tmp_path: Path) -> None:
    path = _write(tmp_path, '{"HIGH": "فصل", "MEDIUM": [], "LOW": []}')

    with pytest.raises(KeywordConfigurationError):
        KeywordLoader(path).load()


def test_load_raises_when_a_level_list_contains_a_non_string_item(tmp_path: Path) -> None:
    path = _write(tmp_path, '{"HIGH": ["فصل", 123], "MEDIUM": [], "LOW": []}')

    with pytest.raises(KeywordConfigurationError):
        KeywordLoader(path).load()


def test_default_keywords_path_points_at_the_shipped_config_file() -> None:
    assert DEFAULT_KEYWORDS_PATH.name == "priority_keywords.json"
    assert DEFAULT_KEYWORDS_PATH.is_file()


def test_default_keywords_path_loads_successfully() -> None:
    result = KeywordLoader().load()

    assert set(result.keys()) == {"HIGH", "MEDIUM", "LOW"}
    assert "فقدان الوظيفة" in result["HIGH"]
