"""Basic ASGI smoke tests; database schema is created for local SQLite by app startup."""

from fastapi.testclient import TestClient
from sqlalchemy import UniqueConstraint

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.models.entities import (
    AnalysisRun,
    Project,
    Recommendation,
    RepositoryCandidate,
    ResearchSource,
    RoadmapMilestone,
    RoadmapTask,
    User,
)


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_schema_indexes_and_unique_constraints():
    project_indexes = {index.name for index in Project.__table__.indexes}
    analysis_indexes = {index.name for index in AnalysisRun.__table__.indexes}
    assert "ix_projects_user_id" in project_indexes
    assert "ix_analysis_runs_project_id" in analysis_indexes
    assert "ix_analysis_runs_status" in analysis_indexes
    assert any(index.unique and "email" in index.name for index in User.__table__.indexes)
    assert any(
        isinstance(constraint, UniqueConstraint)
        and {column.name for column in constraint.columns} == {"analysis_run_id", "html_url"}
        for constraint in RepositoryCandidate.__table__.constraints
    )
    assert {
        constraint.name for constraint in RoadmapTask.__table__.constraints if constraint.name
    } >= {
        "ck_roadmap_tasks_status",
        "ck_roadmap_tasks_priority",
    }


def test_status_codes_and_archive_is_soft_delete():
    import uuid

    client = TestClient(app)
    assert client.get("/api/v1/projects").status_code == 401
    suffix = uuid.uuid4().hex
    response = client.post(
        "/api/v1/auth/register",
        json={"email": f"archive-{suffix}@example.com", "password": "correct-horse-4"},
    )
    assert (
        client.post(
            "/api/v1/auth/register",
            json={"email": f"archive-{suffix}@example.com", "password": "correct-horse-4"},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": f"archive-{suffix}@example.com", "password": "wrong-password"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": f"archive-{suffix}@example.com", "password": "correct-horse-4"},
        ).status_code
        == 200
    )
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.post("/api/v1/projects", headers=headers, json={"name": "X"}).status_code == 422
    project = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Archive me", "description": "A project that can be archived later"},
    ).json()
    assert client.get(f"/api/v1/projects/{uuid.uuid4()}", headers=headers).status_code == 404
    assert (
        client.get(
            f"/api/v1/analyses/{uuid.uuid4()}/export?format=csv", headers=headers
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/projects/{project['id']}", headers=headers).status_code == 204
    assert client.get("/api/v1/projects", headers=headers).json() == []
    db = SessionLocal()
    assert db.get(Project, uuid.UUID(project["id"])).status == "archived"
    db.close()


def test_other_user_cannot_access_any_project_analysis_resource():
    import uuid

    client = TestClient(app)
    suffix = uuid.uuid4().hex
    owner = client.post(
        "/api/v1/auth/register",
        json={"email": f"owner-{suffix}@example.com", "password": "correct-horse-5"},
    )
    stranger = client.post(
        "/api/v1/auth/register",
        json={"email": f"stranger-{suffix}@example.com", "password": "correct-horse-6"},
    )
    owner_headers = {"Authorization": f"Bearer {owner.json()['access_token']}"}
    stranger_headers = {"Authorization": f"Bearer {stranger.json()['access_token']}"}
    project_response = client.post(
        "/api/v1/projects",
        headers=owner_headers,
        json={"name": "Private", "description": "An owner-only project with evidence"},
    )
    project = project_response.json()
    db = SessionLocal()
    run = AnalysisRun(
        project_id=uuid.UUID(project["id"]),
        status="completed",
        input_snapshot={"name": "Private"},
        result={
            "summary": "Private result",
            "functional_requirements": [],
            "non_functional_requirements": [],
            "assumptions": [],
            "stack": [],
            "architecture": "flowchart LR",
            "risks": [],
            "roadmap": [],
        },
    )
    db.add(run)
    db.flush()
    source = ResearchSource(
        analysis_run_id=run.id,
        source_type="github_repository",
        url="https://github.com/example/project",
        title="example/project",
    )
    repository = RepositoryCandidate(
        analysis_run_id=run.id,
        full_name="example/project",
        html_url="https://github.com/example/project",
        language="Python",
        stars=12,
        license=None,
        description="Community project",
    )
    recommendation = Recommendation(
        analysis_run_id=run.id,
        category="API",
        name="FastAPI",
        rationale="Typed API",
        alternatives=[],
        is_estimate=True,
    )
    milestone = RoadmapMilestone(project_id=uuid.UUID(project["id"]), title="First", position=0)
    db.add_all([source, repository, recommendation, milestone])
    db.flush()
    task = RoadmapTask(milestone_id=milestone.id, title="Private task")
    db.add(task)
    db.commit()
    run_id, task_id = run.id, task.id
    db.close()

    paths = [
        f"/api/v1/projects/{project['id']}",
        f"/api/v1/projects/{project['id']}/analyses",
        f"/api/v1/projects/{project['id']}/roadmap",
        f"/api/v1/analyses/{run_id}",
        f"/api/v1/analyses/{run_id}/sources",
        f"/api/v1/analyses/{run_id}/repositories",
        f"/api/v1/analyses/{run_id}/recommendations",
        f"/api/v1/analyses/{run_id}/export?format=json",
        f"/api/v1/analyses/{run_id}/export?format=md",
    ]
    assert [client.get(path, headers=stranger_headers).status_code for path in paths] == [
        403
    ] * len(paths)
    assert (
        client.patch(
            f"/api/v1/roadmap/tasks/{task_id}", headers=stranger_headers, json={"status": "done"}
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/api/v1/roadmap/tasks/{task_id}", headers=owner_headers, json={"status": "invalid"}
        ).status_code
        == 422
    )
    repositories = client.get(
        f"/api/v1/analyses/{run_id}/repositories", headers=owner_headers
    ).json()
    assert repositories[0]["license"] is None
    assert "open_source" not in repositories[0]
    sources = client.get(f"/api/v1/analyses/{run_id}/sources", headers=owner_headers).json()
    assert sources[0]["retrieved_at"]
    updated_task = client.patch(
        f"/api/v1/roadmap/tasks/{task_id}",
        headers=owner_headers,
        json={"status": "done", "priority": "high"},
    )
    assert updated_task.json()["status"] == "done"
    assert updated_task.json()["priority"] == "high"


def test_register_project_crud_and_ownership():
    import uuid

    Base.metadata.create_all(engine)
    client = TestClient(app)
    suffix = uuid.uuid4().hex
    a = client.post(
        "/api/v1/auth/register",
        json={"email": f"a-{suffix}@example.com", "password": "correct-horse-1"},
    )
    b = client.post(
        "/api/v1/auth/register",
        json={"email": f"b-{suffix}@example.com", "password": "correct-horse-2"},
    )
    assert a.status_code == 201 and b.status_code == 201
    headers_a = {"Authorization": f"Bearer {a.json()['access_token']}"}
    headers_b = {"Authorization": f"Bearer {b.json()['access_token']}"}
    project = client.post(
        "/api/v1/projects",
        headers=headers_a,
        json={"name": "Test planner", "description": "A planning app for community teams"},
    )
    assert project.status_code == 201
    project_id = project.json()["id"]
    assert client.get(f"/api/v1/projects/{project_id}", headers=headers_a).status_code == 200
    assert client.get(f"/api/v1/projects/{project_id}", headers=headers_b).status_code == 403
    assert (
        client.patch(
            f"/api/v1/projects/{project_id}", headers=headers_a, json={"name": "Updated"}
        ).json()["name"]
        == "Updated"
    )
    assert client.delete(f"/api/v1/projects/{project_id}", headers=headers_a).status_code == 204
    assert client.get("/api/v1/projects", headers=headers_a).json() == []


def test_analysis_exports():
    import uuid

    Base.metadata.create_all(engine)
    client = TestClient(app)
    email = f"export-{uuid.uuid4().hex}@example.com"
    token = client.post(
        "/api/v1/auth/register", json={"email": email, "password": "correct-horse-3"}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    project = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Export", "description": "Exportable blueprint example project"},
    ).json()
    db = SessionLocal()
    run = AnalysisRun(
        project_id=uuid.UUID(project["id"]),
        status="completed",
        input_snapshot={"name": "Export"},
        result={
            "summary": "A tested blueprint",
            "functional_requirements": ["Create records"],
            "non_functional_requirements": ["Stay available"],
            "assumptions": [],
            "stack": [],
            "architecture": "flowchart LR\n A-->B",
            "risks": [],
            "roadmap": [{"title": "Launch", "tasks": ["Ship"]}],
        },
    )
    db.add(run)
    db.flush()
    db.add(
        ResearchSource(
            analysis_run_id=run.id,
            source_type="github_repository",
            url="https://github.com/example/source",
            title="example/source",
        )
    )
    db.commit()
    run_id = run.id
    db.close()
    response = client.get(f"/api/v1/analyses/{run_id}/export?format=md", headers=headers)
    assert response.status_code == 200 and "A tested blueprint" in response.text
    assert response.headers["content-type"].startswith("text/markdown")
    assert "https://github.com/example/source" in response.text and "retrieved" in response.text
    exported_json = client.get(f"/api/v1/analyses/{run_id}/export?format=json", headers=headers)
    assert exported_json.headers["content-type"].startswith("application/json")
    assert exported_json.json()["summary"] == "A tested blueprint"
    assert exported_json.json()["sources"][0]["url"] == "https://github.com/example/source"
    assert exported_json.json()["sources"][0]["retrieved_at"]
    assert (
        client.get(f"/api/v1/analyses/{run_id}/export?format=csv", headers=headers).status_code
        == 422
    )


def test_analysis_creation_rate_limit(monkeypatch):
    import uuid

    from app.api.v1 import routes

    monkeypatch.setattr(routes, "run_analysis", lambda _analysis_id: None)
    client = TestClient(app)
    suffix = uuid.uuid4().hex
    auth = client.post(
        "/api/v1/auth/register",
        json={"email": f"ratelimit-{suffix}@example.com", "password": "correct-horse-7"},
    )
    headers = {"Authorization": f"Bearer {auth.json()['access_token']}"}
    project = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Rate limited", "description": "Used to verify analysis rate limiting"},
    ).json()
    statuses = [
        client.post(f"/api/v1/projects/{project['id']}/analyses", headers=headers).status_code
        for _ in range(11)
    ]
    assert statuses == [202] * 10 + [429]
