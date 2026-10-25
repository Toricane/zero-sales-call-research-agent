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

`Tool calls used: N` records the number of tool calls made to prepare the briefing. The budget is **8 calls maximum**; a briefing that reports more than 8 fails validation.

The validator checks the briefing format, citations, source content, intentional gap lines, and the tool-call budget. `expected_valid` is test metadata: pytest compares it with the validator's result. Tavily fetches claim-relevant page excerpts, retrying with advanced extraction when basic extraction returns no content. Jev scores whether the retrieved page is a relevant place to investigate that kind of claim. A page can pass this citation-fit check without stating every detail of the claim; an unrelated page or one that explicitly disproves the same fact should fail. A missing excerpt or citation-fit score below 0.66 fails validation. **Passing this check does not verify every factual detail in the briefing.** These six tests call the real APIs, so results can change with page content, retrieval, and Jev's judgment.

`validate_briefing(briefing)` returns a `ValidationResult` with `valid: bool` and `reasons: list[str]`. A valid briefing has an empty reasons list. For a rejected briefing, the list names the detected broken rules so a writer can revise the draft; validation continues after a broken rule to report other issues in the same briefing.

## Why Jev for citation classification

- This step needs a yes/no classification score. TypeSafe's Jev `Noul` returns a numeric value from 0 to 1 directly, so the validator can apply its threshold without parsing generated prose. [TypeSafe's System One documentation](https://docs.typesafe.ai/concepts/system-one) describes the typed decisions and probabilities.
- Calling Jev through TypeSafe keeps the model and API fixed for the six test cases and uses the project's TypeSafe credentials. OpenRouter is a gateway to multiple models and providers, with structured-output support; it is a useful alternative when model choice or provider fallback is needed. [OpenRouter's developer documentation](https://openrouter.ai/developers) describes that routing role.
- The six-row run below shows how this Jev configuration behaves on these fixtures. It does **not** prove Jev classifies more accurately than a model reached through OpenRouter. An effectiveness comparison would require the same labeled examples and retrieved text for both systems, then a comparison of false accepts and false rejects.



## Run record

2026-10-24, using the citation-fit rule with real Tavily and TypeSafe calls:

Command: `python -m pytest -v --tb=line tests/test_validator.py`

```text
============================= test session starts =============================
platform win32 -- Python 3.13.0, pytest-9.1.1, pluggy-1.7.0 -- C:\Users\prajw\Desktop\Coding\Zero\zero-sales-call-research-agent\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\prajw\Desktop\Coding\Zero\zero-sales-call-research-agent
plugins: anyio-4.15.1, langsmith-0.14.12
collecting ... collected 6 items

tests/test_validator.py::test_briefing[SB-01] PASSED                     [ 16%]
tests/test_validator.py::test_briefing[SB-02] PASSED                     [ 33%]
tests/test_validator.py::test_briefing[SB-03] PASSED                     [ 50%]
tests/test_validator.py::test_briefing[SB-04] PASSED                     [ 66%]
tests/test_validator.py::test_briefing[SB-05] PASSED                     [ 83%]
tests/test_validator.py::test_briefing[SB-06] PASSED                     [100%]

============================= 6 passed in 11.36s ==============================
```



## Developer setup and tests

Install `requirements.txt` and set real `TYPESAFE_API_KEY` and `TAVILY_API_KEY` values in local `.env` (ignored by Git). Run `python -m pytest -v` to test the six supplied rows against the live APIs.

## Rep usage instructions
