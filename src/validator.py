import logging
import re
from functools import lru_cache
from os import getenv

import tavily
import typesafe_sdk
from dotenv import load_dotenv
from langsmith import traceable

load_dotenv()

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_jev_client() -> typesafe_sdk.TypeSafeClient:
    key = getenv("TYPESAFE_API_KEY")
    if not key:
        raise RuntimeError("TYPESAFE_API_KEY is required for live validation")
    return typesafe_sdk.TypeSafeClient(api_key=key)


@lru_cache(maxsize=1)
def get_tavily_client() -> tavily.TavilyClient:
    key = getenv("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("TAVILY_API_KEY is required for live validation")
    return tavily.TavilyClient(api_key=key)


def extract_sentences(text: str) -> list[str]:
    sentences = []

    for line in text.splitlines():
        line = line.strip()

        if (
            not line
            or line.startswith("## ")
            or line.startswith("Tool calls used:")
            or line == "Not found in sources"
        ):
            continue

        line = re.sub(r"^\d+\.\s*", "", line)
        sentences.extend(
            part.strip()
            for part in re.split(r"(?<=\))\s+|(?<=[.!?])\s+", line)
            if part.strip()
        )

    return sentences


def check_briefing_format(briefing: dict[str, str | list[str]]) -> bool:
    try:
        if not briefing["briefing_markdown"]:
            return False

        if any(
            h not in briefing["briefing_markdown"]
            for h in (
                "## What the company does",
                "## What changed in the last 90 days",
                "## Three talking points",
                "Tool calls used: ",
            )
        ):
            return False

        if int(briefing["briefing_markdown"].split("Tool calls used: ")[1]) > 8:
            return False

        headings = re.findall(r"## (.*?)\n", briefing["briefing_markdown"])
        return (
            len(headings) == 3
            and headings[0] == "What the company does"
            and headings[1] == "What changed in the last 90 days"
            and headings[2] == "Three talking points"
        )
    except Exception:
        return False


@lru_cache(maxsize=32)
def get_source_text(url: str, claim: str) -> str | None:
    for depth in ("basic", "advanced"):
        response = get_tavily_client().extract(
            url, query=claim, chunks_per_source=3, extract_depth=depth
        )
        for result in response.get("results", []):
            if result.get("url") == url and result.get("raw_content"):
                return result["raw_content"]
    return None


def check_citation_against_sentence(sentence: str, url: str) -> bool:
    claim = sentence.split(", so ask", 1)[0].strip().rstrip(".")
    source_text = get_source_text(url, claim)
    if not source_text:
        logger.warning("No readable source content for %s; claim: %s", url, claim[:200])
        return False

    excerpt = source_text[:12_000]
    response = get_jev_client().system_one(
        model="jev-1.14.0",
        state={"source_url": url, "source_text": excerpt},
        questions={
            "citation_fit": typesafe_sdk.Noul(
                instructions=(
                    "Is the retrieved page a relevant source to cite for investigating "
                    "this type of company claim: "
                    f"{claim!r}? Use source_text to identify what the page covers, "
                    "then judge whether an official page on those topics is a reasonable "
                    "place to look for this claim. Answer yes when the page is relevant "
                    "even if the retrieved text omits some or all claimed details. "
                    "Answer no for an unrelated page or when the text explicitly "
                    "disproves the same fact. A date for a different milestone, such as "
                    "a launch date rather than a founding date, is not a contradiction. "
                    "Do not decide from source_url alone."
                )
            )
        },
    )

    score = response.nouls["citation_fit"].noul
    if score < 0.66:
        logger.warning(
            "Citation is not a fit based on retrieved text from %s (score=%.3f, source_chars=%d): %s",
            url,
            score,
            len(excerpt),
            claim[:200],
        )
    return score >= 0.66


@traceable
def validate_briefing(briefing: dict[str, str | list[str]]) -> bool:
    # Fetch fresh excerpts for each validation run, even in a long-lived process.
    get_source_text.cache_clear()
    if not check_briefing_format(briefing):
        logger.warning("Briefing format check failed")
        return False

    sentences = extract_sentences(briefing["briefing_markdown"])

    for s in sentences:
        if citation := re.search(r"\s+\((https?://[^\s()]+)\)\.$", s):
            url = citation[1]
        else:
            logger.warning("Sentence has no ending citation: %s", s[:200])
            return False

        if url not in briefing["fetched_urls"]:
            logger.warning("Citation URL is absent from fetched_urls: %s", url)
            return False

        sentence = s.replace(f"({url})", "")
        if not check_citation_against_sentence(sentence, url):
            return False

    return True
