"use client";

import Link from "next/link";
import mermaid from "mermaid";
import { useEffect, useState } from "react";
import { api, token } from "@/lib/api";

type StackItem = {
  category: string;
  name: string;
  rationale: string;
  alternatives: string[];
  is_estimate: boolean;
};
type Risk = { title: string; severity: string; mitigation: string };
type RoadmapTask = {
  id: string;
  title: string;
  status: "todo" | "in_progress" | "done";
  priority: "low" | "medium" | "high";
};
type Milestone = { title: string; tasks: Array<string | RoadmapTask> };
type Repository = {
  full_name: string;
  html_url: string;
  language: string | null;
  stars: number;
  license: string | null;
  description: string | null;
  retrieved_at: string;
};
type Source = { url: string; title: string; retrieved_at: string };
type Blueprint = {
  summary: string;
  confidence?: string;
  assumptions: string[];
  functional_requirements: string[];
  non_functional_requirements: string[];
  stack: StackItem[];
  architecture: string;
  risks: Risk[];
  roadmap: Milestone[];
};
type Analysis = {
  id: string;
  project_id: string;
  status: string;
  result: Blueprint | null;
  error?: string;
};
type Tab =
  | "Summary"
  | "Requirements"
  | "Stack"
  | "Architecture"
  | "Repositories"
  | "Risks"
  | "Roadmap"
  | "Sources";

const tabs: Tab[] = [
  "Summary",
  "Requirements",
  "Stack",
  "Architecture",
  "Repositories",
  "Risks",
  "Roadmap",
  "Sources",
];

export default function AnalysisPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const [id, setId] = useState("");
  const [run, setRun] = useState<Analysis | null>(null);
  const [tab, setTab] = useState<Tab>("Summary");
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [recommendations, setRecommendations] = useState<StackItem[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    params.then((value) => setId(value.id));
  }, [params]);

  useEffect(() => {
    if (!id) return;
    const load = () =>
      api<Analysis>(`/analyses/${id}`)
        .then(setRun)
        .catch((reason: unknown) =>
          setError(
            reason instanceof Error
              ? reason.message
              : "Unable to load analysis",
          ),
        );
    void load();
    const timer = setInterval(() => {
      if (run?.status !== "completed" && run?.status !== "failed") void load();
    }, 1800);
    return () => clearInterval(timer);
  }, [id, run?.status]);

  useEffect(() => {
    if (!id) return;
    if (tab === "Repositories") {
      void api<Repository[]>(`/analyses/${id}/repositories`).then(
        setRepositories,
      );
    } else if (tab === "Sources") {
      void api<Source[]>(`/analyses/${id}/sources`).then(setSources);
    } else if (tab === "Stack") {
      void api<StackItem[]>(`/analyses/${id}/recommendations`).then(
        setRecommendations,
      );
    }
  }, [id, tab]);

  const blueprint = run?.result;
  useEffect(() => {
    if (!blueprint?.architecture) return;
    mermaid.initialize({
      startOnLoad: false,
      theme: "dark",
      securityLevel: "strict",
    });
    void mermaid.run({ querySelector: ".mermaid" }).catch(() => undefined);
  }, [blueprint?.architecture]);

  async function updateTask(taskId: string, status: string, priority: string) {
    try {
      await api(`/roadmap/tasks/${taskId}`, {
        method: "PATCH",
        body: JSON.stringify({ status, priority }),
      });
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Could not update task",
      );
    }
  }

  async function download(format: "md" | "json") {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/analyses/${id}/export?format=${format}`,
        { headers: { Authorization: `Bearer ${token()}` } },
      );
      if (!response.ok) throw new Error("Export unavailable");
      const content =
        format === "md"
          ? await response.text()
          : JSON.stringify(await response.json(), null, 2);
      const blob = new Blob([content], {
        type: format === "md" ? "text/markdown" : "application/json",
      });
      const anchor = document.createElement("a");
      anchor.href = URL.createObjectURL(blob);
      anchor.download = `buildatlas-blueprint.${format}`;
      anchor.click();
      URL.revokeObjectURL(anchor.href);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Export failed");
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-8">
      <Link
        href={`/projects/${run?.project_id ?? ""}`}
        className="text-sm text-muted"
      >
        Back to project
      </Link>
      <div className="mt-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[.18em] text-sunshine">
            Blueprint / {run?.status ?? "loading"}
          </p>
          <h1 className="mt-2 text-3xl font-semibold">Analysis</h1>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => void download("md")}
            className="border border-line px-3 py-2 text-sm"
          >
            Export Markdown
          </button>
          <button
            onClick={() => void download("json")}
            className="border border-line px-3 py-2 text-sm"
          >
            Export JSON
          </button>
        </div>
      </div>
      {error && (
        <p role="alert" className="mt-4 text-sm text-red-300">
          {error}
        </p>
      )}
      {!blueprint ? (
        <div className="mt-8 border border-line bg-panel p-8 text-muted">
          {run?.status === "failed"
            ? `Analysis failed: ${run.error ?? "Unknown error"}`
            : "Researching repositories and building your blueprint..."}
        </div>
      ) : (
        <>
          <nav
            aria-label="Blueprint sections"
            className="mt-8 flex gap-1 overflow-x-auto border-b border-line"
          >
            {tabs.map((item) => (
              <button
                key={item}
                onClick={() => setTab(item)}
                className={`whitespace-nowrap border-b-2 px-3 py-3 text-sm ${tab === item ? "border-sunshine text-cloud" : "border-transparent text-muted hover:text-cloud"}`}
              >
                {item}
              </button>
            ))}
          </nav>
          <section className="min-h-[360px] py-7">
            {tab === "Summary" && (
              <div>
                <Badge>
                  AI analysis - confidence {blueprint.confidence ?? "unrated"}
                </Badge>
                <h2 className="mt-4 text-2xl font-medium">Project overview</h2>
                <p className="mt-3 max-w-3xl leading-7 text-muted">
                  {blueprint.summary}
                </p>
                <div className="mt-8 grid gap-4 md:grid-cols-2">
                  <InfoList title="Assumptions" items={blueprint.assumptions} />
                  <InfoList
                    title="Risks"
                    items={blueprint.risks.map((risk) => risk.title)}
                  />
                </div>
              </div>
            )}
            {tab === "Requirements" && (
              <div className="grid gap-6 md:grid-cols-2">
                <InfoList
                  title="Functional"
                  items={blueprint.functional_requirements}
                />
                <InfoList
                  title="Non-functional"
                  items={blueprint.non_functional_requirements}
                />
              </div>
            )}
            {tab === "Stack" && (
              <div className="space-y-3">
                {(recommendations.length
                  ? recommendations
                  : blueprint.stack
                ).map((item) => (
                  <article
                    key={`${item.category}-${item.name}`}
                    className="border border-line bg-panel p-5"
                  >
                    <Badge>
                      {item.is_estimate ? "AI estimate" : "Verified"}
                    </Badge>
                    <h3 className="mt-3 text-lg">
                      {item.category}: {item.name}
                    </h3>
                    <p className="mt-2 text-sm text-muted">{item.rationale}</p>
                    <p className="mt-3 text-xs text-muted">
                      Alternatives: {item.alternatives.join(", ")}
                    </p>
                  </article>
                ))}
              </div>
            )}
            {tab === "Architecture" && (
              <div className="border border-line bg-panel p-5">
                <Badge>AI-generated - review before implementation</Badge>
                <div className="mermaid mt-5 overflow-auto">
                  {blueprint.architecture}
                </div>
              </div>
            )}
            {tab === "Repositories" && (
              <div className="space-y-3">
                {repositories.length === 0 ? (
                  <p className="text-muted">
                    No repository matches were found.
                  </p>
                ) : (
                  repositories.map((repo) => (
                    <article
                      key={repo.html_url}
                      className="border border-line bg-panel p-5"
                    >
                      <a
                        className="text-sunshine underline"
                        href={repo.html_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {repo.full_name}
                      </a>
                      <p className="mt-2 text-sm text-muted">
                        {repo.description ?? "No description"}
                      </p>
                      <p className="mt-3 text-xs text-muted">
                        GitHub API - {repo.stars.toLocaleString()} stars -{" "}
                        {repo.language ?? "Language unknown"} - License:{" "}
                        {repo.license ?? "Unknown"}
                      </p>
                      <Badge>
                        Repository metadata - retrieved{" "}
                        {new Date(repo.retrieved_at).toLocaleString()}
                      </Badge>
                    </article>
                  ))
                )}
              </div>
            )}
            {tab === "Risks" && (
              <div className="space-y-3">
                {blueprint.risks.map((risk, index) => (
                  <article
                    key={`${risk.title}-${index}`}
                    className="border border-line bg-panel p-5"
                  >
                    <Badge>AI estimate - {risk.severity}</Badge>
                    <h3 className="mt-3">{risk.title}</h3>
                    <p className="mt-2 text-sm text-muted">{risk.mitigation}</p>
                  </article>
                ))}
              </div>
            )}
            {tab === "Roadmap" && (
              <div className="space-y-5">
                {blueprint.roadmap.map((milestone, index) => (
                  <article
                    key={`${milestone.title}-${index}`}
                    className="border border-line bg-panel p-5"
                  >
                    <h3 className="text-lg">
                      {String(index + 1).padStart(2, "0")} / {milestone.title}
                    </h3>
                    {milestone.tasks.map((task, taskIndex) => {
                      const editable = typeof task === "string" ? null : task;
                      const title =
                        typeof task === "string" ? task : task.title;
                      return (
                        <div
                          key={editable?.id ?? taskIndex}
                          className="mt-3 flex flex-wrap items-center gap-3 border-t border-line pt-3"
                        >
                          <span className="flex-1 text-sm">{title}</span>
                          {editable?.id && (
                            <>
                              <select
                                defaultValue={editable.status}
                                onChange={(event) =>
                                  void updateTask(
                                    editable.id,
                                    event.target.value,
                                    editable.priority,
                                  )
                                }
                                className="border border-line bg-graphite p-2 text-xs"
                                aria-label="Task status"
                              >
                                <option value="todo">Todo</option>
                                <option value="in_progress">In progress</option>
                                <option value="done">Done</option>
                              </select>
                              <select
                                defaultValue={editable.priority}
                                onChange={(event) =>
                                  void updateTask(
                                    editable.id,
                                    editable.status,
                                    event.target.value,
                                  )
                                }
                                className="border border-line bg-graphite p-2 text-xs"
                                aria-label="Task priority"
                              >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                              </select>
                            </>
                          )}
                        </div>
                      );
                    })}
                  </article>
                ))}
              </div>
            )}
            {tab === "Sources" && (
              <div className="space-y-3">
                {sources.length === 0 ? (
                  <p className="text-muted">
                    No external sources were used for this blueprint.
                  </p>
                ) : (
                  sources.map((source) => (
                    <article
                      key={source.url}
                      className="border border-line bg-panel p-5"
                    >
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sunshine underline"
                      >
                        {source.title}
                      </a>
                      <p className="mt-2 text-xs text-muted">
                        Retrieved{" "}
                        {new Date(source.retrieved_at).toLocaleString()}
                      </p>
                    </article>
                  ))
                )}
              </div>
            )}
          </section>
        </>
      )}
    </main>
  );
}

function InfoList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="border border-line bg-panel p-5">
      <h2 className="text-lg">{title}</h2>
      {items.map((item, index) => (
        <p
          key={`${item}-${index}`}
          className="mt-4 border-t border-line pt-3 text-sm text-muted"
        >
          {item}
        </p>
      ))}
    </div>
  );
}

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-block border border-sunshine/40 px-2 py-1 text-[10px] uppercase tracking-wide text-sunshine">
      {children}
    </span>
  );
}
