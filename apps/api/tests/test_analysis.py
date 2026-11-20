from app.core.database import Base, SessionLocal, engine
from app.models.entities import AnalysisRun, Project, RepositoryCandidate, ResearchSource, User
from app.services.analysis import run_analysis


def test_mock_provider_is_deterministic():
    from app.integrations.llm import MockLLMProvider

    result = MockLLMProvider().analyze("A project idea", [])
    assert result["summary"] == "A build plan for: A project idea"
    assert result["roadmap"]
    assert "architecture" in result


def test_blueprint_schema_rejects_missing_sections():
    import pytest
    from pydantic import ValidationError

    from app.integrations.llm import BlueprintOutput

    with pytest.raises(ValidationError):
        BlueprintOutput.model_validate({"summary": "Incomplete"})


def test_llm_provider_retries_invalid_json(monkeypatch):
    from app.core.config import settings
    from app.integrations.llm import OpenAICompatibleProvider

    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    payload = {
        "summary": "Plan",
        "functional_requirements": [],
        "non_functional_requirements": [],
        "assumptions": [],
        "stack": [],
        "architecture": "flowchart LR",
        "risks": [],
        "roadmap": [],
        "confidence": "low",
    }
    contents = iter(["not-json", __import__("json").dumps(payload)])

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": next(contents)}}]}

    calls = []
    monkeypatch.setattr(
        "app.integrations.llm.httpx.post",
        lambda *args, **kwargs: calls.append(kwargs) or Response(),
    )
    result = OpenAICompatibleProvider().analyze("Idea", [])
    assert result["summary"] == "Plan"
    assert len(calls) == 2
    assert calls[0]["json"]["response_format"]["type"] == "json_schema"


def test_failed_analysis_preserves_existing_result(monkeypatch):
    import uuid

    Base.metadata.create_all(engine)
    db = SessionLocal()
    user = User(email=f"pipeline-{uuid.uuid4().hex}@example.com", password_hash="unused")
    db.add(user)
    db.flush()
    project = Project(
        user_id=user.id, name="Pipeline", description="A sufficiently long project description"
    )
    db.add(project)
    db.flush()
    run = AnalysisRun(
        project_id=project.id,
        status="running",
        input_snapshot={},
        result={"summary": "last good blueprint"},
    )
    db.add(run)
    db.commit()
    run_id = run.id
    db.close()

    class BadProvider:
        def analyze(self, idea, repositories):
            raise ValueError("provider unavailable")

    monkeypatch.setattr("app.services.analysis.RestGitHubClient.search", lambda self, query: [])
    monkeypatch.setattr("app.services.analysis.get_provider", lambda: BadProvider())
    run_analysis(run_id)
    db = SessionLocal()
    stored = db.get(AnalysisRun, run_id)
    assert stored.status == "failed"
    assert stored.result == {"summary": "last good blueprint"}
    db.close()


def test_analysis_persists_null_license_and_retrieved_evidence(monkeypatch):
    import uuid

    from app.integrations.llm import MockLLMProvider

    db = SessionLocal()
    user = User(email=f"evidence-{uuid.uuid4().hex}@example.com", password_hash="unused")
    db.add(user)
    db.flush()
    project = Project(
        user_id=user.id, name="Evidence", description="An idea with evidence from GitHub"
    )
    db.add(project)
    db.flush()
    run = AnalysisRun(project_id=project.id, input_snapshot={})
    db.add(run)
    db.commit()
    run_id = run.id
    db.close()

    repository = {
        "full_name": "example/repo",
        "html_url": "https://github.com/example/repo",
        "language": "Python",
        "stars": 8,
        "license": None,
        "description": "Repository info",
        "pushed_at": None,
        "retrieved_at": "2025-01-01T00:00:00+00:00",
    }
    monkeypatch.setattr(
        "app.services.analysis.RestGitHubClient.search", lambda self, query: [repository]
    )
    monkeypatch.setattr("app.services.analysis.get_provider", lambda: MockLLMProvider())
    run_analysis(run_id)

    db = SessionLocal()
    stored = db.get(AnalysisRun, run_id)
    candidate = db.query(RepositoryCandidate).filter_by(analysis_run_id=run_id).one()
    source = db.query(ResearchSource).filter_by(analysis_run_id=run_id).one()
    assert stored.status == "completed"
    assert candidate.license is None
    assert candidate.stars == 8
    assert source.url == repository["html_url"]
    assert source.retrieved_at is not None
    db.close()
