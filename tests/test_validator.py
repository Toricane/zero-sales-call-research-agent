import json
from pathlib import Path

import pytest

from src.validator import validate_briefing


rows = json.loads(
    (Path(__file__).parent / "Briefings for Validator Tests.json").read_text(
        encoding="utf-8"
    )
)


@pytest.mark.parametrize("row", rows, ids=lambda row: row["sample_id"])
def test_briefing(row):
    assert validate_briefing(row) is row["expected_valid"]
