import csv
import os
from pathlib import Path

from src.research_graph import ResearchState, build_graph

CSV_PATH = (
    Path(__file__).resolve().parents[1] / "HubSpot First-Call Test Company List.csv"
)


def load_company(test_case_id: str) -> dict[str, str | bool]:
    with CSV_PATH.open(newline="", encoding="utf-8") as file:
        for raw_row in csv.DictReader(file):
            if raw_row["test_case_id"] == test_case_id:
                row = dict(raw_row)
                row["has_recent_news"] = row["has_recent_news"].lower() == "true"
                row["force_search_timeout"] = (
                    row["force_search_timeout"].lower() == "true"
                )
                return row

    raise ValueError(f"Test case not found: {test_case_id}")


def main() -> None:
    company = load_company("TC-02")

    initial_state: ResearchState = {
        "company_row": company,
        "next_query": None,
        "sources": [],
        "tool_calls_used": 0,
        "search_failed": False,
        "briefing": "",
    }

    print(f"Selected: {company['test_case_id']} — {company['prospect_company_name']}")
    print(f"Website: {company['website_url']}")
    print(f"First call: {company['first_call_date']}")
    print(f"Recent news expected: {company['has_recent_news']}")
    print(f"Forced timeout: {company['force_search_timeout']}")
    print(f"Initial tool calls: {initial_state['tool_calls_used']}")

    max_calls = int(os.environ["MAX_TOOL_CALLS"])
    graph = build_graph(max_calls)
    final_state = graph.invoke(initial_state)

    print(f"Final tool calls: {final_state['tool_calls_used']}")
    print(f"Final source count: {len(final_state['sources'])}")
    print(f"Search failed: {final_state['search_failed']}")
    print(f"Briefing generated: {bool(final_state['briefing'])}")

    for number, source in enumerate(final_state["sources"], start=1):
        print(
            f"Source {number}: {source['title']} | "
            f"{source.get('published_date') or 'undated'} | {source['url']}"
        )


if __name__ == "__main__":
    main()
