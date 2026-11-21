import logging
from typing import Any

import requests

from src.config import REQUEST_TIMEOUT, USER_AGENT
from src.exceptions import WikipediaError

logger = logging.getLogger(__name__)

_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"


def search_wikipedia(topic: str) -> str:
    logger.info("Wikipedia lookup topic=%r", topic)
    if not topic.strip():
        raise WikipediaError("Topic is empty.")

    title = topic.strip().replace(" ", "_")
    url = _SUMMARY_URL.format(title=title)

    try:
        response = requests.get(
            url,
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.Timeout as exc:
        raise WikipediaError(f"Wikipedia request timed out for topic: {topic!r}") from exc
    except requests.RequestException as exc:
        raise WikipediaError(f"Wikipedia network error: {exc}") from exc

    if response.status_code == 404:
        raise WikipediaError(f"No Wikipedia article found for: {topic!r}")
    if response.status_code == 429:
        raise WikipediaError("Wikipedia rate limit reached. Please try again later.")
    if not response.ok:
        raise WikipediaError(f"Wikipedia returned status {response.status_code}.")

    data = response.json()
    extract = data.get("extract", "").strip()
    page_title = data.get("title", topic)
    page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

    if not extract:
        raise WikipediaError(f"No summary available for: {topic!r}")

    result = f"Title: {page_title}\nURL: {page_url}\n\n{extract}"
    logger.info("Wikipedia result for %r: %d chars", topic, len(result))
    return result


SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "wikipedia_search",
        "description": (
            "Fetch a summary about a topic from Wikipedia. "
            "Use this when the user asks to look up, explain, or learn about a specific topic, "
            "person, place, event, or concept."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic or article title to look up, e.g. 'Python programming language'.",
                }
            },
            "required": ["topic"],
        },
    },
}


def handle(arguments: dict[str, Any]) -> str:
    topic = arguments.get("topic", "")
    try:
        return search_wikipedia(topic)
    except WikipediaError as exc:
        return f"error: {exc}"
