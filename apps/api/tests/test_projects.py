"""Basic ASGI smoke tests; database schema is created for local SQLite by app startup."""
from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.models.entities import AnalysisRun


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_register_project_crud_and_ownership():
    import uuid

    Base.metadata.create_all(engine)
    client = TestClient(app)
    suffix = uuid.uuid4().hex
    a = client.post("/api/v1/auth/register", json={"email": f"a-{suffix}@example.com", "password": "correct-horse-1"})
    b = client.post("/api/v1/auth/register", json={"email": f"b-{suffix}@example.com", "password": "correct-horse-2"})
    assert a.status_code == 201 and b.status_code == 201
    headers_a = {"Authorization": f"Bearer {a.json()['access_token']}"}
    headers_b = {"Authorization": f"Bearer {b.json()['access_token']}"}
    project = client.post("/api/v1/projects", headers=headers_a, json={"name": "Test planner", "description": "A planning app for community teams"})
    assert project.status_code == 201
    project_id = project.json()["id"]
    assert client.get(f"/api/v1/projects/{project_id}", headers=headers_a).status_code == 200
    assert client.get(f"/api/v1/projects/{project_id}", headers=headers_b).status_code == 403
    assert client.patch(f"/api/v1/projects/{project_id}", headers=headers_a, json={"name": "Updated"}).json()["name"] == "Updated"
    assert client.delete(f"/api/v1/projects/{project_id}", headers=headers_a).status_code == 204
    assert client.get("/api/v1/projects", headers=headers_a).json() == []


def test_analysis_exports():
    import uuid

    Base.metadata.create_all(engine)
    client = TestClient(app)
    email = f"export-{uuid.uuid4().hex}@example.com"
    token = client.post("/api/v1/auth/register", json={"email": email, "password": "correct-horse-3"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    project = client.post("/api/v1/projects", headers=headers, json={"name": "Export", "description": "Exportable blueprint example project"}).json()
    db = SessionLocal()
    run = AnalysisRun(project_id=uuid.UUID(project["id"]), status="completed", input_snapshot={"name": "Export"}, result={"summary": "A tested blueprint", "functional_requirements": ["Create records"], "non_functional_requirements": ["Stay available"], "assumptions": [], "stack": [], "architecture": "flowchart LR\n A-->B", "risks": [], "roadmap": [{"title": "Launch", "tasks": ["Ship"]}]})
    db.add(run)
    db.commit()
    run_id = run.id
    db.close()
    response = client.get(f"/api/v1/analyses/{run_id}/export?format=md", headers=headers)
    assert response.status_code == 200 and "A tested blueprint" in response.text
    assert client.get(f"/api/v1/analyses/{run_id}/export?format=json", headers=headers).json()["summary"] == "A tested blueprint"
