from datetime import UTC, datetime

from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.integrations.github import RestGitHubClient
from app.integrations.llm import get_provider
from app.models.entities import (
    AnalysisRun,
    Project,
    Recommendation,
    RepositoryCandidate,
    ResearchSource,
    RoadmapMilestone,
    RoadmapTask,
)


def run_analysis(analysis_id):
    db = SessionLocal()
    run = db.get(AnalysisRun, analysis_id)
    if not run:
        db.close()
        return
    run.status, run.started_at = "running", datetime.now(UTC)
    db.commit()
    try:
        project = db.get(Project, run.project_id)
        keywords = " ".join(project.description.split()[:8])
        repositories = []
        try:
            repositories = RestGitHubClient().search(f"{keywords} in:name,description")
        except Exception:
            # GitHub is optional evidence; the run can proceed with no repository results.
            repositories = []
        result = get_provider().analyze(project.description, repositories)
        required = {"summary", "functional_requirements", "non_functional_requirements", "assumptions", "stack", "architecture", "risks", "roadmap"}
        if not isinstance(result, dict) or not required.issubset(result):
            raise ValueError("Provider returned an incomplete blueprint")
        for repo in repositories:
            db.add(RepositoryCandidate(analysis_run_id=run.id, **{k: repo[k] for k in ("full_name", "html_url", "language", "stars", "license", "description")}, pushed_at=datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00")) if repo.get("pushed_at") else None))
            db.add(ResearchSource(analysis_run_id=run.id, source_type="github_repository", url=repo["html_url"], title=repo["full_name"]))
        for item in result["stack"]:
            db.add(Recommendation(analysis_run_id=run.id, category=item.get("category", "stack"), name=item["name"], rationale=item["rationale"], alternatives=item.get("alternatives", []), is_estimate=item.get("is_estimate", True)))
        # Keep prior successful milestones intact; each analysis gets its own roadmap rows.
        max_position = db.scalar(select(func.max(RoadmapMilestone.position)).where(RoadmapMilestone.project_id == project.id))
        base_position = max_position + 1 if max_position is not None else 0
        for pos, milestone in enumerate(result["roadmap"]):
            row = RoadmapMilestone(project_id=project.id, title=milestone["title"], position=base_position + pos)
            db.add(row)
            db.flush()
            for title in milestone.get("tasks", []):
                db.add(RoadmapTask(milestone_id=row.id, title=title))
        run.result = result
        run.provider = "openai-compatible" if settings.llm_api_key else "mock"
        run.model = settings.llm_model if settings.llm_api_key else "deterministic"
        run.status = "completed"
    except Exception as exc:
        run.status, run.error = "failed", str(exc)[:1000]
    finally:
        run.completed_at = datetime.now(UTC)
        db.commit()
        db.close()
