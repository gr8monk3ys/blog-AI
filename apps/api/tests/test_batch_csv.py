"""
Unit tests for batch CSV parsing helpers.

Covers parse_csv_to_items across happy path, optional columns, and the
validation error cases (missing topic, empty file, over the item cap). These
were previously inline in the import endpoint with no direct test coverage
(docs/REMEDIATION_PLAN.md P2.3).
"""

import pytest
from fastapi import HTTPException

from app.routes.batch_csv import CSV_TEMPLATE, MAX_BATCH_ITEMS, parse_csv_to_items


def test_parses_full_row():
    csv_text = (
        "topic,keywords,tone,content_type,custom_instructions\n"
        '"AI in Healthcare","AI,healthcare",professional,blog,Focus on ROI\n'
    )
    items = parse_csv_to_items(csv_text)
    assert len(items) == 1
    item = items[0]
    assert item.topic == "AI in Healthcare"
    # BatchItemInput normalizes keywords to lowercase.
    assert item.keywords == ["ai", "healthcare"]
    assert item.tone == "professional"
    assert item.content_type == "blog"
    assert item.custom_instructions == "Focus on ROI"


def test_applies_defaults_for_optional_columns():
    items = parse_csv_to_items("topic\nJust a topic\n")
    assert len(items) == 1
    assert items[0].topic == "Just a topic"
    assert items[0].keywords == []
    assert items[0].tone == "professional"
    assert items[0].content_type == "blog"
    assert items[0].custom_instructions is None


def test_blank_custom_instructions_become_none():
    items = parse_csv_to_items("topic,custom_instructions\nA topic,\n")
    assert items[0].custom_instructions is None


def test_missing_topic_value_raises_400_with_row_number():
    csv_text = "topic,tone\nGood,casual\n,casual\n"
    with pytest.raises(HTTPException) as exc:
        parse_csv_to_items(csv_text)
    assert exc.value.status_code == 400
    assert "Row 3" in exc.value.detail


def test_empty_file_raises_400():
    with pytest.raises(HTTPException) as exc:
        parse_csv_to_items("topic\n")
    assert exc.value.status_code == 400
    assert "empty" in exc.value.detail.lower()


def test_over_item_cap_raises_400():
    rows = "\n".join(f"Topic {i}" for i in range(MAX_BATCH_ITEMS + 1))
    csv_text = "topic\n" + rows + "\n"
    with pytest.raises(HTTPException) as exc:
        parse_csv_to_items(csv_text)
    assert exc.value.status_code == 400
    assert str(MAX_BATCH_ITEMS) in exc.value.detail


def test_template_is_valid_and_round_trips():
    # The downloadable template must itself parse cleanly.
    items = parse_csv_to_items(CSV_TEMPLATE)
    assert len(items) == 3
    assert items[0].topic == "AI in Healthcare"
