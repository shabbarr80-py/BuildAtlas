from app.integrations.github import RestGitHubClient


def test_github_metadata_normalization(monkeypatch):
    class Response:
        def __init__(self):
            self.status_code = 200
            self.headers = {}
            self.links = {}
            self.request = None

        def raise_for_status(self): pass
        def json(self):
            return {"items": [{"full_name": "a/b", "html_url": "https://github.com/a/b", "language": "Python", "stargazers_count": 12, "license": None, "description": None, "pushed_at": None}]}
    calls = []
    monkeypatch.setattr("app.integrations.github.httpx.get", lambda *a, **k: calls.append(k) or Response())
    client = RestGitHubClient()
    repo = client.search("test unique cache key")[0]
    client.search("test unique cache key")
    assert repo["stars"] == 12
    assert repo["license"] is None
    assert repo["retrieved_at"]
    assert len(calls) == 1
