"""
CSV import/export helpers for batch generation.

Pure parsing/template helpers extracted from app/routes/batch.py so they can be
unit-tested without going through the HTTP layer (see
docs/REMEDIATION_PLAN.md P2.3).
"""

import csv
import io
from typing import List

from fastapi import HTTPException, status

from src.types.batch import BatchItemInput

# Maximum number of items accepted in a single CSV batch import.
MAX_BATCH_ITEMS = 100

# Downloadable template shown to users for batch CSV import.
CSV_TEMPLATE = """topic,keywords,tone,content_type,custom_instructions
"AI in Healthcare","AI,healthcare,medical,diagnosis",professional,blog,
"The Future of Remote Work","remote work,productivity,work from home",informative,blog,
"Sustainable Technology Trends","green tech,sustainability,environment",casual,blog,Focus on practical tips
"""


def parse_csv_to_items(content_str: str) -> List[BatchItemInput]:
    """
    Parse CSV content into a list of validated batch items.

    Expects a header row with at least a ``topic`` column; ``keywords`` (comma
    separated), ``tone``, ``content_type``, and ``custom_instructions`` are
    optional.

    Raises:
        HTTPException(400): on a row missing ``topic``, empty input, or more
            than ``MAX_BATCH_ITEMS`` rows.
    """
    reader = csv.DictReader(io.StringIO(content_str))

    items: List[BatchItemInput] = []
    for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
        if "topic" not in row or not row["topic"].strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Row {row_num}: Missing required 'topic' column",
            )

        # Parse keywords (comma-separated)
        keywords = []
        if row.get("keywords"):
            keywords = [k.strip() for k in row["keywords"].split(",") if k.strip()]

        items.append(
            BatchItemInput(
                topic=row["topic"].strip(),
                keywords=keywords,
                tone=row.get("tone", "professional").strip(),
                content_type=row.get("content_type", "blog").strip(),
                custom_instructions=row.get("custom_instructions", "").strip() or None,
            )
        )

    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty or has no valid rows",
        )

    if len(items) > MAX_BATCH_ITEMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_BATCH_ITEMS} items per batch. Found {len(items)}.",
        )

    return items
