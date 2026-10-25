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

The validator checks the briefing format, citations, source content, intentional gap lines, and the tool-call budget. `expected_valid` is test metadata: pytest compares it with the validator's result. Tavily fetches claim-relevant page excerpts, retrying with advanced extraction when basic extraction returns no content. The selected classifier judges whether the retrieved page is a relevant place to investigate that kind of claim. A page can pass this citation-fit check without stating every detail of the claim; an unrelated page or one that explicitly disproves the same fact should fail. A missing excerpt fails validation. Jev's citation-fit score must be at least 0.66; OpenRouter must answer `YES`. **Passing this check does not verify every factual detail in the briefing.** Live results can change with page content, retrieval, and classifier judgment.

`validate_briefing(briefing)` returns a `ValidationResult` with `valid: bool` and `reasons: list[str]`. A valid briefing has an empty reasons list. For a rejected briefing, the list names the detected broken rules so a writer can revise the draft; validation continues after a broken rule to report other issues in the same briefing.

## Classifier choice

- **Jev is the default.** TypeSafe's `Noul` returns a value from 0 to 1 directly, so the validator can apply its threshold without parsing generated prose. The tests below use Jev. [TypeSafe's System One documentation](https://docs.typesafe.ai/concepts/system-one) describes its typed decisions and probabilities.
- **OpenRouter is optional.** Set `VALIDATOR_CLASSIFIER=openrouter` to route the same citation-fit question through an OpenRouter chat model. That path expects an exact `YES` or `NO` response; it does not produce a Jev score. The default `openrouter/free` route may select different free models over time. Set `OPENROUTER_MODEL` to a specific available model when repeatability matters. [OpenRouter's Python API example](https://openrouter.ai/developers) and [free-model router](https://openrouter.ai/collections/free-models) describe these options.
- The run below covers the six supplied rows and one additional citation-fit rejection case. It does **not** compare Jev's accuracy with an OpenRouter model. Such a comparison needs the same labeled examples and retrieved text for both systems, then a comparison of false accepts and false rejects.



## Run record

2026-10-24, using the default Jev classifier with real Tavily and TypeSafe calls:

Command: `python -m pytest -v --tb=line tests/test_validator.py`

```text
============================= test session starts =============================
platform win32 -- Python 3.13.0, pytest-9.1.1, pluggy-1.7.0 -- C:\Users\prajw\Desktop\Coding\Zero\zero-sales-call-research-agent\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\prajw\Desktop\Coding\Zero\zero-sales-call-research-agent
plugins: anyio-4.15.1, langsmith-0.14.12
collecting ... collected 7 items

tests/test_validator.py::test_briefing[SB-01] PASSED                     [ 14%]
tests/test_validator.py::test_briefing[SB-02] PASSED                     [ 28%]
tests/test_validator.py::test_briefing[SB-03] PASSED                     [ 42%]
tests/test_validator.py::test_briefing[SB-04] PASSED                     [ 57%]
tests/test_validator.py::test_briefing[SB-05] PASSED                     [ 71%]
tests/test_validator.py::test_briefing[SB-06] PASSED                     [ 85%]
tests/test_validator.py::test_fetched_but_unrelated_citation_is_rejected PASSED [100%]

============================= 7 passed in 15.62s ==============================
```

The additional test cites Asana's company page for a Gusto product claim and includes that page in `fetched_urls`. It passes only if the validator reports a citation-fit rejection based on the retrieved page content.

## Developer setup and tests

Install `requirements.txt` and copy `.env.example` to local `.env` (ignored by Git). Keep `VALIDATOR_CLASSIFIER=jev` or omit it to use the default; set real `TYPESAFE_API_KEY` and `TAVILY_API_KEY` values. To use OpenRouter instead, set `VALIDATOR_CLASSIFIER=openrouter`, `OPENROUTER_API_KEY`, and optionally `OPENROUTER_MODEL`; Tavily is still required, while a TypeSafe key is not. Set a real `LANGSMITH_API_KEY` if tracing is enabled. Run `python -m pytest -v` to test the six supplied rows and additional citation-fit case against live APIs. The run record above covers Jev; the OpenRouter path has not been run here because no OpenRouter key is configured.

## Rep usage instructions

