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
    result = validate_briefing(row)
    assert result.valid is row["expected_valid"], result.reasons

    expected_reasons = {
        "SB-04": "Missing section: ## What changed in the last 90 days",
        "SB-05": "Sentence has no ending citation",
        "SB-06": "Citation URL is absent from fetched_urls",
    }
    if row["expected_valid"]:
        assert result.reasons == []
    else:
        assert any(expected_reasons[row["sample_id"]] in reason for reason in result.reasons)
