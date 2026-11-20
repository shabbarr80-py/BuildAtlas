import httpx
import pytest

from app.integrations.github import RestGitHubClient


def test_github_metadata_normalization(monkeypatch):
    class Response:
        def __init__(self):
            self.status_code = 200
            self.headers = {}
            self.links = {}
            self.request = None

        def raise_for_status(self):
            pass

        def json(self):
            return {
                "items": [
                    {
                        "full_name": "a/b",
                        "html_url": "https://github.com/a/b",
                        "language": "Python",
                        "stargazers_count": 12,
                        "license": None,
                        "description": None,
                        "pushed_at": None,
                    }
                ]
            }

    calls = []
    monkeypatch.setattr(
        "app.integrations.github.httpx.get", lambda *a, **k: calls.append(k) or Response()
    )
    client = RestGitHubClient()
    repo = client.search("test unique cache key")[0]
    client.search("test unique cache key")
    assert repo["stars"] == 12
    assert repo["license"] is None
    assert repo["retrieved_at"]
    assert len(calls) == 1


def test_github_client_follows_bounded_next_page(monkeypatch):
    class Response:
        def __init__(self, name, next_url=None):
            self.status_code = 200
            self.headers = {}
            self.request = None
            self.links = {"next": {"url": next_url}} if next_url else {}
            self.item = {
                "full_name": name,
                "html_url": f"https://github.com/{name}",
                "language": None,
                "stargazers_count": 0,
                "license": None,
                "description": None,
                "pushed_at": None,
            }

        def raise_for_status(self):
            pass

        def json(self):
            return {"items": [self.item]}

    responses = iter(
        [
            Response("one/two", "https://api.github.com/search/repositories?page=2"),
            Response("three/four"),
        ]
    )
    monkeypatch.setattr("app.integrations.github.httpx.get", lambda *a, **k: next(responses))
    repositories = RestGitHubClient().search("pagination test query")
    assert [repo["full_name"] for repo in repositories] == ["one/two", "three/four"]


def test_github_rate_limit_is_reported(monkeypatch):
    class Response:
        def __init__(self):
            self.status_code = 403
            self.headers = {"X-RateLimit-Remaining": "0"}
            self.request = httpx.Request("GET", "https://api.github.com/search/repositories")

        def raise_for_status(self):
            raise AssertionError("The rate limit should be detected first")

    monkeypatch.setattr("app.integrations.github.httpx.get", lambda *a, **k: Response())
    with pytest.raises(httpx.HTTPStatusError, match="rate limit"):
        RestGitHubClient().search("rate limited unique query")


@pytest.mark.parametrize(
    "failure", [httpx.TimeoutException("timeout"), httpx.ConnectError("offline")]
)
def test_github_timeout_and_transport_errors_propagate(monkeypatch, failure):
    def fail(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr("app.integrations.github.httpx.get", fail)
    with pytest.raises((httpx.TimeoutException, httpx.ConnectError)):
        RestGitHubClient().search(f"failure-{type(failure).__name__}-query")
