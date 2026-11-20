import time
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
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
from app.schemas.api import (
    Login,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    TaskUpdate,
    Token,
    UserCreate,
)
from app.services.analysis import run_analysis

router = APIRouter()
oauth = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
password_hash = PasswordHash.recommended()
_rate: dict[str, list[float]] = {}


def current_user(token: str = Depends(oauth), db: Session = Depends(get_db)):
    try:
        uid = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"]).get("sub")
        user = db.get(User, uuid.UUID(uid))
    except (JWTError, ValueError, TypeError):
        user = None
    if user is None:
        raise HTTPException(
            401, detail={"error": {"code": "unauthorized", "message": "Invalid credentials"}}
        )
    return user


def owned_project(project_id: uuid.UUID, user: User, db: Session):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(
            404, detail={"error": {"code": "not_found", "message": "Project not found"}}
        )
    if project.user_id != user.id:
        raise HTTPException(
            403, detail={"error": {"code": "forbidden", "message": "Not project owner"}}
        )
    return project


def owned_analysis(analysis_id: uuid.UUID, user: User, db: Session):
    run = db.get(AnalysisRun, analysis_id)
    if not run:
        raise HTTPException(
            404, detail={"error": {"code": "not_found", "message": "Analysis not found"}}
        )
    owned_project(run.project_id, user, db)
    return run


@router.post("/auth/register", response_model=Token, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == data.email.lower())):
        raise HTTPException(
            400, detail={"error": {"code": "email_exists", "message": "Email already registered"}}
        )
    user = User(email=data.email.lower(), password_hash=password_hash.hash(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = jwt.encode(
        {"sub": str(user.id), "exp": datetime.now(UTC) + timedelta(days=7)},
        settings.jwt_secret,
        algorithm="HS256",
    )
    return {"access_token": token}


@router.post("/auth/login", response_model=Token)
def login(data: Login, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not password_hash.verify(data.password, user.password_hash):
        raise HTTPException(
            401, detail={"error": {"code": "unauthorized", "message": "Invalid email or password"}}
        )
    token = jwt.encode(
        {"sub": str(user.id), "exp": datetime.now(UTC) + timedelta(days=7)},
        settings.jwt_secret,
        algorithm="HS256",
    )
    return {"access_token": token}


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return list(
        db.scalars(
            select(Project)
            .where(Project.user_id == user.id, Project.status != "archived")
            .order_by(Project.created_at.desc())
        )
    )


@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(
    data: ProjectCreate, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    project = Project(user_id=user.id, **data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    return owned_project(project_id, user, db)


@router.patch("/projects/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    project = owned_project(project_id, user, db)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/projects/{project_id}", status_code=204)
def archive_project(
    project_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    project = owned_project(project_id, user, db)
    project.status = "archived"
    db.commit()
    return Response(status_code=204)


@router.post("/projects/{project_id}/analyses", status_code=202)
def create_analysis(
    project_id: uuid.UUID,
    background: BackgroundTasks,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    project = owned_project(project_id, user, db)
    now = time.monotonic()
    key = str(user.id)
    _rate[key] = [t for t in _rate.get(key, []) if now - t < 3600]
    if len(_rate[key]) >= 10:
        raise HTTPException(
            429, detail={"error": {"code": "rate_limited", "message": "Analysis limit reached"}}
        )
    _rate[key].append(now)
    run = AnalysisRun(
        project_id=project.id,
        input_snapshot={
            "name": project.name,
            "description": project.description,
            "constraints": project.constraints,
        },
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    background.add_task(run_analysis, run.id)
    return {"analysis_id": run.id, "status": "queued", "message": "Analysis queued"}


@router.get("/projects/{project_id}/analyses")
def list_analyses(
    project_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    owned_project(project_id, user, db)
    runs = db.scalars(
        select(AnalysisRun)
        .where(AnalysisRun.project_id == project_id)
        .order_by(AnalysisRun.created_at.desc())
    )
    return [
        {
            "id": run.id,
            "status": run.status,
            "result": run.result,
            "error": run.error,
            "created_at": run.created_at,
        }
        for run in runs
    ]


@router.get("/analyses/{analysis_id}")
def get_analysis(
    analysis_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    run = owned_analysis(analysis_id, user, db)
    result = run.result
    if result and result.get("roadmap"):
        milestones = db.scalars(
            select(RoadmapMilestone)
            .where(RoadmapMilestone.project_id == run.project_id)
            .order_by(RoadmapMilestone.position.desc())
            .limit(len(result["roadmap"]))
        ).all()
        milestones.reverse()
        for output, row in zip(result["roadmap"], milestones):
            output["tasks"] = [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                }
                for task in row.tasks
            ]
    return {
        "id": run.id,
        "project_id": run.project_id,
        "status": run.status,
        "result": result,
        "error": run.error,
        "provider": run.provider,
        "model": run.model,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
    }


@router.get("/analyses/{analysis_id}/sources")
def sources(
    analysis_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    owned_analysis(analysis_id, user, db)
    return [
        {
            "source_type": x.source_type,
            "url": x.url,
            "title": x.title,
            "retrieved_at": x.retrieved_at,
        }
        for x in db.scalars(
            select(ResearchSource).where(ResearchSource.analysis_run_id == analysis_id)
        )
    ]


@router.get("/analyses/{analysis_id}/repositories")
def repositories(
    analysis_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    owned_analysis(analysis_id, user, db)
    rows = db.scalars(
        select(RepositoryCandidate).where(RepositoryCandidate.analysis_run_id == analysis_id)
    )
    return [
        {
            "full_name": x.full_name,
            "html_url": x.html_url,
            "language": x.language,
            "stars": x.stars,
            "license": x.license,
            "description": x.description,
            "retrieved_at": x.retrieved_at,
        }
        for x in rows
    ]


@router.get("/analyses/{analysis_id}/recommendations")
def recommendations(
    analysis_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    owned_analysis(analysis_id, user, db)
    return [
        {
            "category": x.category,
            "name": x.name,
            "rationale": x.rationale,
            "alternatives": x.alternatives,
            "is_estimate": x.is_estimate,
        }
        for x in db.scalars(
            select(Recommendation).where(Recommendation.analysis_run_id == analysis_id)
        )
    ]


@router.get("/projects/{project_id}/roadmap")
def roadmap(
    project_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    owned_project(project_id, user, db)
    rows = db.scalars(
        select(RoadmapMilestone)
        .where(RoadmapMilestone.project_id == project_id)
        .order_by(RoadmapMilestone.position)
    ).all()
    return [
        {
            "id": m.id,
            "title": m.title,
            "position": m.position,
            "tasks": [
                {"id": t.id, "title": t.title, "status": t.status, "priority": t.priority}
                for t in m.tasks
            ],
        }
        for m in rows
    ]


@router.patch("/roadmap/tasks/{task_id}")
def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    task = db.get(RoadmapTask, task_id)
    if not task:
        raise HTTPException(
            404, detail={"error": {"code": "not_found", "message": "Task not found"}}
        )
    milestone = db.get(RoadmapMilestone, task.milestone_id)
    owned_project(milestone.project_id, user, db)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    return {"id": task.id, "title": task.title, "status": task.status, "priority": task.priority}


@router.get("/analyses/{analysis_id}/export")
def export_analysis(
    analysis_id: uuid.UUID,
    format: str = "json",
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    run = owned_analysis(analysis_id, user, db)
    if run.status != "completed" or not run.result:
        raise HTTPException(
            400, detail={"error": {"code": "not_ready", "message": "Analysis is not complete"}}
        )
    if format not in {"md", "json"}:
        raise HTTPException(
            422,
            detail={"error": {"code": "invalid_format", "message": "Format must be md or json"}},
        )
    result = run.result
    source_rows = db.scalars(
        select(ResearchSource).where(ResearchSource.analysis_run_id == analysis_id)
    ).all()
    source_data = [
        {
            "source_type": source.source_type,
            "url": source.url,
            "title": source.title,
            "retrieved_at": source.retrieved_at,
        }
        for source in source_rows
    ]
    if format == "json":
        return {**result, "sources": source_data}
    md = (
        f"# {run.input_snapshot.get('name', 'BuildAtlas Blueprint')}\n\n{result['summary']}\n\n## Requirements\n\n"
        + "\n".join(
            f"- {x}"
            for x in result["functional_requirements"] + result["non_functional_requirements"]
        )
    )
    md += "\n\n## Architecture\n\n```mermaid\n" + result["architecture"] + "\n```\n\n## Roadmap\n\n"
    md += "\n".join(
        f"### {m['title']}\n" + "\n".join(f"- [ ] {t}" for t in m.get("tasks", []))
        for m in result["roadmap"]
    )
    md += "\n\n## Sources\n\n" + (
        "\n".join(
            f"- [{source['title']}]({source['url']}) (retrieved {source['retrieved_at'].isoformat()})"
            for source in source_data
        )
        if source_rows
        else "No external sources were used."
    )
    return Response(
        md,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=buildatlas-blueprint.md"},
    )
