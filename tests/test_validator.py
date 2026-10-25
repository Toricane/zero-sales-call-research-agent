import json
from copy import deepcopy
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


def test_fetched_but_unrelated_citation_is_rejected():
    briefing = deepcopy(rows[0])
    unrelated_url = rows[2]["fetched_urls"][1]  # Asana's company page
    briefing["fetched_urls"].append(unrelated_url)
    briefing["briefing_markdown"] = briefing["briefing_markdown"].replace(
        "Gusto provides payroll, benefits and HR software built for small businesses "
        "(https://gusto.com/about).",
        "Gusto provides payroll, benefits and HR software built for small businesses "
        f"({unrelated_url}).",
        1,
    )

    result = validate_briefing(briefing)

    assert result.valid is False
    assert any(
        reason.startswith(f"Citation does not fit retrieved content from {unrelated_url}")
        and "Gusto provides payroll" in reason
        for reason in result.reasons
    ), result.reasons
