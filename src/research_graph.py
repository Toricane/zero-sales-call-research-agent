import os
from datetime import date, timedelta
from typing import TypedDict
from urllib.parse import urlparse

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from tavily import TavilyClient

load_dotenv()


class ResearchState(TypedDict):
    company_row: dict[str, str | bool]
    next_query: str | None
    sources: list[dict[str, str]]
    tool_calls_used: int
    search_failed: bool
    briefing: str


def plan_next_search(state: ResearchState) -> dict[str, str | None]:
    company = state["company_row"]
    name = str(company["prospect_company_name"])
    domain = urlparse(str(company["website_url"])).netloc.removeprefix("www.")

    call_date = date.fromisoformat(str(company["first_call_date"]))
    window_start = call_date - timedelta(days=90)

    if state["tool_calls_used"] == 0:
        query = f"{name} official site {domain} about products"
    elif state["tool_calls_used"] == 1:
        query = (
            f"{name} news from {window_start.isoformat()} to {call_date.isoformat()}"
        )
    else:
        query = None

    return {"next_query": query}


def search_once(state: ResearchState) -> dict[str, object]:
    query = state["next_query"]
    if query is None:
        raise ValueError("The planner must provide a query before search_once runs")

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is missing")

    client = TavilyClient(api_key=api_key)
    new_count = state["tool_calls_used"] + 1

    try:
        search_options = {
            "query": query,
            "search_depth": "basic",
            "max_results": 5,
            "timeout": 10,
        }

        if state["tool_calls_used"] == 1:  # second search: recent news
            call_date = date.fromisoformat(str(state["company_row"]["first_call_date"]))
            search_options.update(
                {
                    "topic": "news",
                    "start_date": (call_date - timedelta(days=90)).isoformat(),
                    "end_date": call_date.isoformat(),
                    "filter_by_published_date": True,
                }
            )

        response = client.search(**search_options)
    except TimeoutError:
        return {
            "tool_calls_used": new_count,
            "search_failed": True,
        }

    new_sources = []
    for result in response.get("results", []):
        url = str(result.get("url") or "").strip()
        content = str(result.get("content") or "").strip()
        if url and content:
            company_name = str(state["company_row"]["prospect_company_name"]).casefold()
            official_domain = (
                urlparse(str(state["company_row"]["website_url"]))
                .netloc.removeprefix("www.")
                .casefold()
            )

            new_sources = []
            for result in response.get("results", []):
                url = str(result.get("url") or "").strip()
                title = str(result.get("title") or "").strip()
                content = str(result.get("content") or "").strip()
                if not url or not content:
                    continue

                result_domain = urlparse(url).netloc.removeprefix("www.").casefold()
                mentions_company = company_name in f"{title} {content}".casefold()
                if result_domain != official_domain and not mentions_company:
                    continue

                new_sources.append(
                    {
                        "url": url,
                        "title": title,
                        "content": content,
                        "published_date": str(result.get("published_date") or ""),
                    }
                )

    return {
        "tool_calls_used": new_count,
        "sources": state["sources"] + new_sources,
        "search_failed": len(new_sources) == 0,
    }


def writer_stub(state: ResearchState) -> dict[str, object]:
    if state["search_failed"]:
        stop_reason = "search returned no usable sources or timed out"
    elif state["next_query"] is None:
        stop_reason = "planner had no next query"
    else:
        stop_reason = "tool-call budget reached"

    print(
        "WRITER STUB REACHED — "
        f"calls={state['tool_calls_used']}, "
        f"sources={len(state['sources'])}, "
        f"search_failed={state['search_failed']}"
    )
    print(f"Stop reason: {stop_reason}")
    return {"briefing": ""}


def build_graph(max_calls: int):
    if max_calls < 1:
        raise ValueError("max_calls must be positive")

    def route_before_search(state: ResearchState) -> str:
        if state["search_failed"]:
            return "writer"
        if state["tool_calls_used"] >= max_calls:
            return "writer"
        if state["next_query"] is None:
            return "writer"
        return "search"

    def route_after_search(state: ResearchState) -> str:
        if state["search_failed"]:
            return "writer"
        if state["tool_calls_used"] >= max_calls:
            return "writer"
        return "planner"

    builder = StateGraph(ResearchState)
    builder.add_node("planner", plan_next_search)
    builder.add_node("search", search_once)
    builder.add_node("writer", writer_stub)

    builder.add_edge(START, "planner")
    builder.add_conditional_edges(
        "planner",
        route_before_search,
        {"search": "search", "writer": "writer"},
    )
    builder.add_conditional_edges(
        "search",
        route_after_search,
        {"planner": "planner", "writer": "writer"},
    )
    builder.add_edge("writer", END)

    return builder.compile()
