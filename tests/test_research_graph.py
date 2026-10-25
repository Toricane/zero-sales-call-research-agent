from tavily import TavilyClient

from src.research_graph import ResearchState, build_graph
from src.run_research import load_company


def test_first_search_timeout_goes_to_writer(monkeypatch, capsys):
    company = load_company("TC-07")
    assert company["force_search_timeout"] is True

    search_calls = 0

    def raise_timeout(self, *args, **kwargs):
        nonlocal search_calls
        search_calls += 1
        raise TimeoutError("Forced timeout for this test")

    monkeypatch.setattr(TavilyClient, "search", raise_timeout)

    initial_state: ResearchState = {
        "company_row": company,
        "next_query": None,
        "sources": [],
        "tool_calls_used": 0,
        "search_failed": False,
        "briefing": "",
    }

    final_state = build_graph(max_calls=8).invoke(initial_state)
    output = capsys.readouterr().out

    assert search_calls == 1
    assert final_state["tool_calls_used"] == 1
    assert final_state["search_failed"] is True
    assert final_state["sources"] == []
    assert final_state["briefing"] == ""
    assert "WRITER STUB REACHED" in output
    assert "Stop reason: search returned no usable sources or timed out" in output


def test_empty_news_search_keeps_sources_and_goes_to_writer(monkeypatch, capsys):
    company = load_company("TC-04")  # Present & Correct: no recent news
    assert company["has_recent_news"] is False

    queries = []

    def return_results_then_empty(self, query, **kwargs):
        queries.append(query)

        if len(queries) == 1:
            return {
                "results": [
                    {
                        "url": company["website_url"],
                        "title": "Present & Correct",
                        "content": "Design goods and stationery.",
                    }
                ]
            }

        return {"results": []}

    monkeypatch.setattr(TavilyClient, "search", return_results_then_empty)

    initial_state: ResearchState = {
        "company_row": company,
        "next_query": None,
        "sources": [],
        "tool_calls_used": 0,
        "search_failed": False,
        "briefing": "",
    }

    final_state = build_graph(max_calls=8).invoke(initial_state)
    output = capsys.readouterr().out

    assert len(queries) == 2
    assert "Present & Correct" in queries[0]
    assert final_state["tool_calls_used"] == 2
    assert final_state["search_failed"] is True
    assert len(final_state["sources"]) == 1
    assert final_state["briefing"] == ""
    assert "WRITER STUB REACHED" in output
    assert "Stop reason: search returned no usable sources or timed out" in output


def test_budget_stops_before_second_search(monkeypatch, capsys):
    company = load_company("TC-02")
    queries = []

    def successful_search(self, query, **kwargs):
        queries.append(query)
        return {
            "results": [
                {
                    "url": company["website_url"],
                    "title": "Gymshark",
                    "content": "Gymshark sells fitness apparel.",
                }
            ]
        }

    monkeypatch.setattr(TavilyClient, "search", successful_search)

    initial_state: ResearchState = {
        "company_row": company,
        "next_query": None,
        "sources": [],
        "tool_calls_used": 0,
        "search_failed": False,
        "briefing": "",
    }

    final_state = build_graph(max_calls=1).invoke(initial_state)
    output = capsys.readouterr().out

    assert len(queries) == 1
    assert final_state["tool_calls_used"] == 1
    assert final_state["search_failed"] is False
    assert len(final_state["sources"]) == 1
    assert final_state["briefing"] == ""
    assert "WRITER STUB REACHED" in output
    assert "Stop reason: tool-call budget reached" in output


def test_planner_exhaustion_goes_to_writer(monkeypatch, capsys):
    company = load_company("TC-02")
    queries = []

    def successful_search(self, query, **kwargs):
        queries.append(query)
        return {
            "results": [
                {
                    "url": company["website_url"],
                    "title": "Gymshark",
                    "content": "Gymshark sells fitness apparel.",
                }
            ]
        }

    monkeypatch.setattr(TavilyClient, "search", successful_search)

    initial_state: ResearchState = {
        "company_row": company,
        "next_query": None,
        "sources": [],
        "tool_calls_used": 0,
        "search_failed": False,
        "briefing": "",
    }

    final_state = build_graph(max_calls=8).invoke(initial_state)
    output = capsys.readouterr().out

    assert len(queries) == 2
    assert final_state["tool_calls_used"] == 2
    assert final_state["next_query"] is None
    assert final_state["search_failed"] is False
    assert final_state["briefing"] == ""
    assert "Stop reason: planner had no next query" in output
