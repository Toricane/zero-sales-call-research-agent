# Sales call briefing contract

The input is a JSON file containing briefings, where each briefing has the following structure:
```json
{
  "sample_id": "SB-##",
  "company_name": "Example",
  "fetched_urls": [
    "https://example.com/",
    "https://example.com/about",
    "https://example.com/company-news",
    "https://example.com/product/pricing",
    "https://example.com/partners"
  ],
  "briefing_markdown": "See below for the format for the output which is shown within the code block.",
  "expected_valid": true
}
```

- `sample_id: string`: The sample ID of the company.
- `company_name: string`: The name of the company.
- `fetched_urls: string[]`: The URLs of the company's website that were fetched.
- `briefing_markdown: string`: The briefing markdown that is expected to be generated.
- `expected_valid: boolean`: Whether the briefing is expected to be valid.

Below is the format for the output which is shown within the code block.

```markdown
## What the company does

Factual sentence (source URL). Can have multiple sentences (must end with source URL in brackets).

Gap line: "Not found in sources" (exactly as shown) when no information is found about this section from the sources.

## What changed in the last 90 days

Factual sentence (source URL). Can have multiple sentences (must end with source URL in brackets).

Gap line: "Not found in sources" (exactly as shown) when no information is found about this section from the sources.

## Three talking points

1. Sentence 1 (source URL).
2. Sentence 2 (source URL).
3. Sentence 3 (source URL).

Tool calls used: N
```

The validator checks the briefing format, citations, source content, intentional gap lines, and the tool-call budget. `expected_valid` is test metadata: pytest compares it with the validator's result. The source check asks Tavily for claim-relevant page excerpts, then asks Jev whether the excerpt supports the claim. A missing excerpt fails validation; a Jev score below 0.66 fails validation. These six tests call the real APIs, so the result depends on the current page content and Jev's judgment.

## Run record

2026-10-24, using Python 3.13.0 and pytest 9.1.1 with real Tavily and TypeSafe calls:

```text
.\.venv\Scripts\python.exe -m pytest -v --tb=line tests/test_validator.py
tests/test_validator.py::test_briefing[SB-01] FAILED
tests/test_validator.py::test_briefing[SB-02] FAILED
tests/test_validator.py::test_briefing[SB-03] FAILED
tests/test_validator.py::test_briefing[SB-04] PASSED
tests/test_validator.py::test_briefing[SB-05] PASSED
tests/test_validator.py::test_briefing[SB-06] PASSED
========================= 3 failed, 3 passed in 3.99s =========================
```

The first rejected claim in each failing row was:

- **SB-01:** Jev scored the claim that Gusto was founded in 2011 and is headquartered in San Francisco **0.020**. The cited [Gusto about page](https://gusto.com/about) says it launched in 2012 but does not state the claimed 2011 founding year. This does not establish that the claim is false; the cited page does not support the full sentence.
- **SB-02:** Jev scored the claim that Calendly was founded by Tope Awotona in 2013 and is headquartered in Atlanta **0.120**. The cited [Calendly about page](https://calendly.com/about) supports the founder and year but does not mention Atlanta.
- **SB-03:** Jev scored the claim that Asana was founded in 2008 by Dustin Moskovitz and Justin Rosenstein and is headquartered in San Francisco **0.160**. The cited [Asana company page](https://asana.com/company) names the founders and San Francisco HQ but does not state 2008.

The source file marks SB-01 through SB-03 `expected_valid: true`. These live source checks conflict with those labels for the cited sentences. The labels have not been changed; the test-file owner should confirm whether the fixtures or source citations need updating.

## Rep usage instructions

Install `requirements.txt` and set real `TYPESAFE_API_KEY` and `TAVILY_API_KEY` values in local `.env` (ignored by Git). Run `python -m pytest -v` to test the six supplied rows against the live APIs.
