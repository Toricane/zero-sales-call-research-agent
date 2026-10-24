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

The validator checks the briefing format, citations, source content, intentional gap lines, and the tool-call budget. `expected_valid` is test metadata: pytest compares it with the validator's result. The source check asks Tavily for claim-relevant page excerpts, then asks Jev whether the excerpt supports the claim. A missing excerpt or a Jev support score below 0.66 fails the citation check. That result means the retrieved text did not provide sufficient support; it does not establish whether the claim is true or false in the wider world. These six tests call the real APIs, so the result depends on the current page content and Jev's judgment.

## Run record

2026-10-24, using Python 3.13.0 and pytest 9.1.1 with real Tavily and TypeSafe calls:

```text
python -m pytest -v --tb=line tests/test_validator.py
=================================================================================================== test session starts ====================================================================================================
platform win32 -- Python 3.13.0, pytest-9.1.1, pluggy-1.7.0 -- C:\Users\prajw\Desktop\Coding\Zero\zero-sales-call-research-agent\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\prajw\Desktop\Coding\Zero\zero-sales-call-research-agent
plugins: anyio-4.15.1, langsmith-0.14.12
collected 6 items                                                                                                                                                                                                           

tests/test_validator.py::test_briefing[SB-01] FAILED                                                                                                                                                                  [ 16%]
tests/test_validator.py::test_briefing[SB-02] FAILED                                                                                                                                                                  [ 33%]
tests/test_validator.py::test_briefing[SB-03] FAILED                                                                                                                                                                  [ 50%]
tests/test_validator.py::test_briefing[SB-04] PASSED                                                                                                                                                                  [ 66%]
tests/test_validator.py::test_briefing[SB-05] PASSED                                                                                                                                                                  [ 83%]
tests/test_validator.py::test_briefing[SB-06] PASSED                                                                                                                                                                  [100%]

========================================================================================================= FAILURES ========================================================================================================= 
E   assert False is True
     +  where False = validate_briefing({'sample_id': 'SB-01', 'company_name': 'Gusto', 'fetched_urls': ['https://gusto.com/', 'https://gusto.com/about', 'https://gusto.com/company-news', 'https://gusto.com/product/pricing', 'https://gusto.com/partners'], 'briefing_markdown': "## What the company does\nGusto provides payroll, benefits and HR software built for small businesses (https://gusto.com/about). The company was founded in 2011 and is headquartered in San Francisco (https://gusto.com/about). Its platform combines full-service payroll, health benefits, time tracking and hiring tools in one account (https://gusto.com/). Gusto runs a partner program for accountants and bookkeepers who manage payroll on behalf of their clients (https://gusto.com/partners).\n\n## What changed in the last 90 days\nGusto's company news page lists press releases published since December 2024 on product updates for small-business employers (https://gusto.com/company-news). The same page lists announcements about partner integrations and research on small-business hiring (https://gusto.com/company-news).\n\n## Three talking points\n1. Gusto sells Simple, Plus and Premium payroll plans, so ask which plan the prospect uses today and what would push them to upgrade (https://gusto.com/product/pricing).\n2. Gusto's partner program serves accounting firms, so ask whether an outside accountant currently runs their payroll (https://gusto.com/partners).\n3. Gusto bundles benefits administration with payroll, so ask how the team handles benefits enrollment for new hires today (https://gusto.com/).\n\nTool calls used: 6", ...})
---------------------------------------------------------------------------------------------------- Captured log call ----------------------------------------------------------------------------------------------------- 
WARNING  src.validator:validator.py:121 Claim lacks support in retrieved text from https://gusto.com/about (score=0.020, source_chars=2351): The company was founded in 2011 and is headquartered in San Francisco
C:\Users\prajw\Desktop\Coding\Zero\zero-sales-call-research-agent\tests\test_validator.py:18: assert False is True
E   assert False is True
     +  where False = validate_briefing({'sample_id': 'SB-02', 'company_name': 'Calendly', 'fetched_urls': ['https://calendly.com/', 'https://calendly.com/about', 'https://calendly.com/pricing', 'https://calendly.com/blog'], 'briefing_markdown': "## What the company does\nCalendly is a scheduling platform that lets people share a booking link so others can pick an open time on their calendar (https://calendly.com/). The company was founded by Tope Awotona in 2013 and is headquartered in Atlanta (https://calendly.com/about). Its pricing page lists a free plan alongside paid Standard, Teams and Enterprise tiers (https://calendly.com/pricing).\nNot found insources\nCalendly connects with Google Calendar, Microsoft Outlook and other calendar systems so bookings sync automatically (https://calendly.com/).\n\n## What changed in the last 90 days\nNot found in sources\n\n## Three talking points\n1. Calendly offers a free plan as well as paid tiers, so ask whether the team pays for scheduling today or relies on the free plan (https://calendly.com/pricing).\n2. Calendly's blog publishes scheduling guides for sales and recruiting teams, so ask which team in the company books the most external meetings (https://calendly.com/blog).\n3. Calendly syncs with Google and Microsoft calendars, so ask which calendar system the prospect's team runs on (https://calendly.com/).\n\nTool calls used: 5", ...})
---------------------------------------------------------------------------------------------------- Captured log call ----------------------------------------------------------------------------------------------------- 
WARNING  src.validator:validator.py:121 Claim lacks support in retrieved text from https://calendly.com/about (score=0.130, source_chars=1324): The company was founded by Tope Awotona in 2013 and is headquartered in Atlanta
C:\Users\prajw\Desktop\Coding\Zero\zero-sales-call-research-agent\tests\test_validator.py:18: assert False is True
E   assert False is True
     +  where False = validate_briefing({'sample_id': 'SB-03', 'company_name': 'Asana', 'fetched_urls': ['https://asana.com/', 'https://asana.com/company', 'https://asana.com/pricing', 'https://asana.com/press', 'https://asana.com/customers'], 'briefing_markdown': "## What the company does\nAsana is a work management platform that teams use to plan, track and coordinate projects and goals (https://asana.com/). The company was founded in 2008 by Dustin Moskovitz and Justin Rosenstein and is headquartered in San Francisco (https://asana.com/company). Asana's customer stories page features organizations across technology, healthcare, retail and the public sector (https://asana.com/customers).\n\n## What changed in the last 90 days\nNot found in sources\n\n## Three talking points\n1. Asana offers a free Personal plan plus paid Starter, Advanced and Enterprise tiers, so ask how many seats the prospect pays for today (https://asana.com/pricing).\n2. Asana's homepage promotes AI features built into its workflows, so ask whether the team has tried AI for project intake or status updates (https://asana.com/).\n3. Asana's customer stories describe rollouts that span several departments, so ask which teams outside the core group would need access (https://asana.com/customers).\n\nTool calls used: 8", ...})
---------------------------------------------------------------------------------------------------- Captured log call ----------------------------------------------------------------------------------------------------- 
WARNING  src.validator:validator.py:121 Claim lacks support in retrieved text from https://asana.com/company (score=0.170, source_chars=2188): The company was founded in 2008 by Dustin Moskovitz and Justin Rosenstein andis headquartered in San Francisco
C:\Users\prajw\Desktop\Coding\Zero\zero-sales-call-research-agent\tests\test_validator.py:18: assert False is True
================================================================================================= short test summary info ================================================================================================== 
FAILED tests/test_validator.py::test_briefing[SB-01] - assert False is True
FAILED tests/test_validator.py::test_briefing[SB-02] - assert False is True
FAILED tests/test_validator.py::test_briefing[SB-03] - assert False is True
=============================================================================================== 3 failed, 3 passed in 3.69s ================================================================================================
```

The first claim lacking sufficient support from its retrieved citation in each failing row was:

- **SB-01:** Jev scored the claim that Gusto was founded in 2011 and is headquartered in San Francisco **0.020**. The cited [Gusto about page](https://gusto.com/about) says it launched in 2012 but does not state the claimed 2011 founding year, leaving the full sentence unsupported by that citation.
- **SB-02:** Jev scored the claim that Calendly was founded by Tope Awotona in 2013 and is headquartered in Atlanta **0.120**. The cited [Calendly about page](https://calendly.com/about) supports the founder and year but does not mention Atlanta.
- **SB-03:** Jev scored the claim that Asana was founded in 2008 by Dustin Moskovitz and Justin Rosenstein and is headquartered in San Francisco **0.160**. The cited [Asana company page](https://asana.com/company) names the founders and San Francisco HQ but does not state 2008.

The source file marks SB-01 through SB-03 `expected_valid: true`. Their current citations did not sufficiently support these complete sentences in the live run. The validator does not distinguish missing evidence from explicit contradiction; both produce `False`. The labels have not been changed, and the test-file owner should confirm whether the fixtures or source citations need updating.

## Rep usage instructions

Install `requirements.txt` and set real `TYPESAFE_API_KEY` and `TAVILY_API_KEY` values in local `.env` (ignored by Git). Run `python -m pytest -v` to test the six supplied rows against the live APIs.
