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

Each required section must contain content or the exact gap line `Not found in sources`; a blank section is invalid. `Three talking points` must contain items numbered 1, 2, and 3, or the gap line when no talking points were found.

`Tool calls used: N` records the number of tool calls made to prepare the briefing. The budget is **8 calls maximum**; a briefing that reports more than 8 fails validation.

The validator checks the briefing format, citations, source content, intentional gap lines, and the tool-call budget. `expected_valid` is test metadata: pytest compares it with the validator's result. Tavily fetches claim-relevant page excerpts, retrying with advanced extraction when basic extraction returns no content. The selected classifier judges whether the retrieved page is a relevant place to investigate that kind of claim. A page can pass this citation-fit check without stating every detail of the claim; an unrelated page or one that explicitly disproves the same fact should fail. A missing excerpt fails validation. Jev's citation-fit score must be at least 0.66; OpenRouter must answer `YES`. **Passing this check does not verify every factual detail in the briefing.** Live results can change with page content, retrieval, and classifier judgment.

`validate_briefing(briefing)` returns a `ValidationResult` with `valid: bool` and `reasons: list[str]`. A valid briefing has an empty reasons list. For a rejected briefing, the list names the detected broken rules so a writer can revise the draft; validation continues after a broken rule to report other issues in the same briefing.

## Classifier choice

- **Jev is the default.** TypeSafe's `Noul` returns a value from 0 to 1 directly, so the validator can apply its threshold without parsing generated prose. The tests below use Jev. [TypeSafe's System One documentation](https://docs.typesafe.ai/concepts/system-one) describes its typed decisions and probabilities.
- **OpenRouter is optional.** Set `VALIDATOR_CLASSIFIER=openrouter` to route the same citation-fit question through an OpenRouter chat model. That path expects an exact `YES` or `NO` response; it does not produce a Jev score. The default `openrouter/free` route may select different free models over time. Set `OPENROUTER_MODEL` to a specific available model when repeatability matters. [OpenRouter's Python API example](https://openrouter.ai/developers) and [free-model router](https://openrouter.ai/collections/free-models) describe these options.
- The run below covers the six supplied rows, one additional citation-fit rejection case, and format-rule cases. It does **not** compare Jev's accuracy with an OpenRouter model. Such a comparison needs the same labeled examples and retrieved text for both systems, then a comparison of false accepts and false rejects.



## Run record

2026-10-24, using the default Jev classifier with real Tavily and TypeSafe calls:

Command: `python -m pytest -v -s --tb=line tests/test_validator.py`

```text
============================= test session starts =============================
platform win32 -- Python 3.13.0, pytest-9.1.1, pluggy-1.7.0 -- C:\Users\prajw\Desktop\Coding\Zero\zero-sales-call-research-agent\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\prajw\Desktop\Coding\Zero\zero-sales-call-research-agent
plugins: anyio-4.15.1, langsmith-0.14.12
collecting ... collected 10 items

tests/test_validator.py::test_briefing[SB-01] PASSED
tests/test_validator.py::test_briefing[SB-02] PASSED
tests/test_validator.py::test_briefing[SB-03] PASSED
tests/test_validator.py::test_briefing[SB-04] SB-04 rejected: Missing section: ## What changed in the last 90 days
PASSED
tests/test_validator.py::test_briefing[SB-05] SB-05 rejected: Sentence has no ending citation: Mailchimp has been part of Intuit since its acquisition in 2021.
PASSED
tests/test_validator.py::test_briefing[SB-06] SB-06 rejected: Citation URL is absent from fetched_urls: https://www.canva.com/enterprise/
PASSED
tests/test_validator.py::test_fetched_but_unrelated_citation_is_rejected PASSED
tests/test_validator.py::test_tool_call_budget_is_enforced PASSED
tests/test_validator.py::test_empty_section_requires_gap_line PASSED
tests/test_validator.py::test_three_talking_points_are_required PASSED

============================= 10 passed in 20.37s =============================
```

The additional citation test cites Asana's company page for a Gusto product claim and includes that page in `fetched_urls`. It passes only if the validator reports a citation-fit rejection based on the retrieved page content. The other added tests confirm that 9 tool calls, an empty section, and a section with only two talking points are rejected.

## Research graph run record

The LangGraph research run selected TC-02 (Gymshark), a standard first-call case with recent news expected and no forced timeout. The graph reached the writer stub after two Tavily search calls, with eight retained sources and `search_failed=False`. [View the LangSmith trace](https://smith.langchain.com/public/120dac3d-0cc5-42f0-8447-c2d7daa73863/r/01a170b7-ecfd-7335-a48b-49814d798109?start_time=2026-10-25T01%3A41%3A04.381058Z).

Commands: `.\.venv\Scripts\python.exe -m pytest -q` and `.\.venv\Scripts\python.exe -m src.run_research`

```text
..............                                                                                                                                                                                                        [100%]
14 passed in 39.76s
Selected: TC-02 — Gymshark
Website: https://www.gymshark.com
First call: 2025-03-13
Recent news expected: True
Forced timeout: False
Initial tool calls: 0
WRITER STUB REACHED — calls=2, sources=8, search_failed=False
Stop reason: planner had no next query
Final tool calls: 2
Final source count: 8
Search failed: False
Briefing generated: False
Source 1: Gymshark - Wikipedia | undated | https://en.wikipedia.org/wiki/Gymshark
Source 2: All Products | Women's Gym Clothes | Gymshark | undated | https://www.gymshark.com/collections/all-products/womens
Source 3: About us | Gymshark | undated | https://www.gymshark.com/pages/about-us
Source 4: Gymshark Official Store | Gym Clothes & Workout Wear | Gymshark | undated | https://www.gymshark.com/pages/home_variant_b
Source 5: Gymshark Company Overview, Contact Details & Competitors | LeadIQ | undated | https://leadiq.com/c/gymshark/5a1d98ba2300005200875c72
Source 6: Best of 2024: Gymshark’s Ben Francis – ‘I want to be a globally iconic brand’ - Retail Gazette | Tue, 24 Dec 2024 06:30:45 GMT | https://www.retailgazette.co.uk/blog/2024/12/interview-gymsharks-stratford/
Source 7: Gymshark names chief commerical officer - Retail Dive | Tue, 04 Mar 2025 17:50:39 GMT | https://www.retaildive.com/news/gymshark-chief-commerical-officer-kim-dolder/741388/
Source 8: Gymshark names new chief commercial officer amid US expansion - Retail Gazette | Tue, 25 Feb 2025 09:21:55 GMT | https://www.retailgazette.co.uk/blog/2025/02/gymshark-cco/
```

The trace shows planner → search → planner → search → planner → writer, with a final state of two tool calls, eight sources, and no search failure. On its third visit, the planner returned `next_query=None` because it had planned both searches; the route sent the state to the writer. The run stopped because the planner had no next query, not because the eight-call budget was reached. The run demonstrates source gathering and routing; the writer is still a stub and leaves the shared `briefing` string empty.

## Developer setup and tests

Install `requirements.txt` and copy `.env.example` to local `.env` (ignored by Git). Keep `VALIDATOR_CLASSIFIER=jev` or omit it to use the default; set real `TYPESAFE_API_KEY` and `TAVILY_API_KEY` values. To use OpenRouter instead, set `VALIDATOR_CLASSIFIER=openrouter`, `OPENROUTER_API_KEY`, and optionally `OPENROUTER_MODEL`; Tavily is still required, while a TypeSafe key is not. Set a real `LANGSMITH_API_KEY` if tracing is enabled. Run `python -m pytest -v -s` to test the six supplied rows and added cases against live APIs and print the rejection reasons. The validator run record covers Jev; the OpenRouter path has not been run here because no OpenRouter key is configured.

## Rep usage instructions

