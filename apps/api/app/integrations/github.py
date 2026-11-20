import time
from datetime import UTC, datetime
from typing import Protocol

import httpx

from app.core.config import settings

_search_cache: dict[str, tuple[float, list[dict]]] = {}
_CACHE_SECONDS = 600


class GitHubClient(Protocol):
    def search(self, query: str) -> list[dict]: ...


class RestGitHubClient:
    def search(self, query: str) -> list[dict]:
        cached = _search_cache.get(query)
        if cached and time.monotonic() - cached[0] < _CACHE_SECONDS:
            return cached[1]
        for key, (created, _) in list(_search_cache.items()):
            if time.monotonic() - created >= _CACHE_SECONDS:
                del _search_cache[key]
        headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        now = datetime.now(UTC).isoformat()
        output = []
        url = "https://api.github.com/search/repositories"
        params = {"q": query, "per_page": 30, "page": 1}
        for _ in range(2):
            response = httpx.get(url, params=params, headers=headers, timeout=15)
            if response.status_code in (403, 429) and response.headers.get("X-RateLimit-Remaining") == "0":
                raise httpx.HTTPStatusError("GitHub API rate limit reached", request=response.request, response=response)
            response.raise_for_status()
            for item in response.json().get("items", []):
                output.append({"full_name": item["full_name"], "html_url": item["html_url"], "language": item.get("language"), "stars": item["stargazers_count"], "license": (item.get("license") or {}).get("spdx_id"), "description": item.get("description"), "pushed_at": item.get("pushed_at"), "retrieved_at": now})
            next_link = response.links.get("next", {}).get("url")
            if not next_link:
                break
            url, params = next_link, None
        if len(_search_cache) >= 100:
            _search_cache.pop(next(iter(_search_cache)))
        _search_cache[query] = (time.monotonic(), output)
        return output
