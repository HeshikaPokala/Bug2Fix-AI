import { useCallback, useMemo, useState, type ReactNode } from "react";
import type { RunResponse, TraceEvent } from "./types";

const AGENTS = [
  { key: "TriageAgent", label: "Triage", desc: "Symptoms & hypotheses" },
  { key: "LogAnalystAgent", label: "Log analyst", desc: "Evidence from logs" },
  { key: "ReproductionAgent", label: "Reproduction", desc: "Minimal failing repro" },
  { key: "FixPlannerAgent", label: "Fix planner", desc: "Root cause & patch" },
  { key: "ReviewerCriticAgent", label: "Critic", desc: "Safety & edge cases" },
] as const;

function agentCompleted(trace: TraceEvent[], agentKey: string): boolean {
  return trace.some(
    (e) =>
      e.event === "agent_end" &&
      (e.payload as { agent?: string }).agent === agentKey
  );
}

function ConfidenceRing({ value }: { value: number }) {
  const pct = Math.min(100, Math.max(0, value * 100));
  const r = 52;
  const c = 2 * Math.PI * r;
  const offset = c - (pct / 100) * c;
  return (
    <div className="relative flex h-36 w-36 items-center justify-center">
      <svg className="-rotate-90 transform" width="140" height="140" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={r} fill="none" stroke="#252a38" strokeWidth="10" />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          stroke="url(#gradConf)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          className="transition-all duration-700 ease-out"
        />
        <defs>
          <linearGradient id="gradConf" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#a78bfa" />
            <stop offset="100%" stopColor="#22d3ee" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono text-2xl font-semibold text-white">
          {(value * 100).toFixed(0)}%
        </span>
        <span className="text-xs text-zinc-500">confidence</span>
      </div>
    </div>
  );
}

function SectionCard({
  title,
  subtitle,
  children,
  accent = "violet",
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  accent?: "violet" | "cyan" | "amber";
}) {
  const border =
    accent === "cyan"
      ? "from-cyan-glow/20"
      : accent === "amber"
        ? "from-amber-400/20"
        : "from-violet-glow/20";
  return (
    <section
      className={`rounded-2xl border border-white/5 bg-ink-850/80 p-6 shadow-panel backdrop-blur-sm ${border} bg-gradient-to-br to-transparent`}
    >
      <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-white">{title}</h2>
          {subtitle ? <p className="mt-0.5 text-sm text-zinc-500">{subtitle}</p> : null}
        </div>
      </div>
      {children}
    </section>
  );
}

export default function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<RunResponse | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [form, setForm] = useState({
    bug_report: "inputs/bug_report.md",
    logs: "inputs/logs/app.log",
    repo_root: "mini_repo",
    output_dir: "artifacts",
  });

  const run = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setError((err as { detail?: string }).detail ?? res.statusText);
        return;
      }
      const json = (await res.json()) as RunResponse;
      setData(json);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }, [form]);

  const report = data?.report;
  const trace = data?.trace ?? [];

  const bugSummary = report?.bug_summary as Record<string, string> | undefined;
  const evidence = report?.evidence as Array<{
    type: string;
    lines?: string[];
    items?: Array<{ line: string; text: string }>;
    count?: number;
  }> | undefined;
  const repro = report?.repro as Record<string, unknown> | undefined;
  const reproResult = repro?.result as Record<string, unknown> | undefined;
  const hypothesis = report?.root_cause_hypothesis as Record<string, unknown> | undefined;
  const patchPlan = report?.patch_plan as Record<string, unknown> | undefined;
  const validation = report?.validation_plan as Record<string, unknown> | undefined;
  const findings = report?.reviewer_critic_findings as Array<{
    severity: string;
    issue: string;
  }> | undefined;
  const openQs = report?.open_questions as string[] | undefined;
  const confidence = typeof report?.confidence === "number" ? report.confidence : 0;

  const downloadJson = useCallback(() => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "Final Report.json";
    a.click();
    URL.revokeObjectURL(url);
  }, [report]);

  const pipelineState = useMemo(
    () => AGENTS.map((a) => ({ ...a, done: agentCompleted(trace, a.key) })),
    [trace]
  );

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 pb-24 sm:px-6 lg:px-8">
      <header className="mb-12 text-center sm:mb-16">
        <p className="mb-2 font-mono text-xs uppercase tracking-[0.2em] text-violet-glow/80">
          Multi-agent orchestration
        </p>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          <span className="text-gradient">Bug2Fix</span>
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-zinc-400">
          Bug report, logs, and repo snapshot flow through specialized agents. Watch the trace, read
          the verdict, and export structured JSON for your assessment submission.
        </p>
      </header>

      <div className="mb-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
        <button
          type="button"
          onClick={run}
          disabled={loading}
          className="group relative inline-flex items-center justify-center overflow-hidden rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 px-8 py-3.5 text-sm font-semibold text-white shadow-glow transition hover:from-violet-500 hover:to-fuchsia-500 disabled:opacity-50"
        >
          <span className="relative z-10">{loading ? "Running pipeline…" : "Run full analysis"}</span>
          <span
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/25 to-transparent opacity-0 transition group-hover:opacity-100"
            style={{ backgroundSize: "200% 100%", animation: "shimmer 2s linear infinite" }}
          />
        </button>
        <button
          type="button"
          onClick={() => setShowAdvanced((v) => !v)}
          className="text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline"
        >
          {showAdvanced ? "Hide" : "Show"} input paths
        </button>
        {data ? (
          <button
            type="button"
            onClick={downloadJson}
            className="text-sm font-medium text-cyan-glow hover:underline"
          >
            Download report JSON
          </button>
        ) : null}
      </div>

      {showAdvanced ? (
        <div className="mx-auto mb-10 grid max-w-3xl gap-3 rounded-2xl border border-white/5 bg-ink-900/50 p-5 sm:grid-cols-2">
          {(
            [
              ["bug_report", "Bug report"],
              ["logs", "Logs file"],
              ["repo_root", "Repo root"],
              ["output_dir", "Output dir"],
            ] as const
          ).map(([key, label]) => (
            <label key={key} className="block text-left">
              <span className="mb-1 block text-xs font-medium text-zinc-500">{label}</span>
              <input
                className="w-full rounded-lg border border-white/10 bg-ink-800 px-3 py-2 font-mono text-sm text-zinc-200 outline-none ring-violet-500/30 focus:ring-2"
                value={form[key]}
                onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
              />
            </label>
          ))}
        </div>
      ) : null}

      {error ? (
        <div className="mx-auto mb-8 max-w-2xl rounded-xl border border-red-500/30 bg-red-950/40 px-4 py-3 text-center text-sm text-red-200">
          {error}
        </div>
      ) : null}

      {data ? (
        <>
          <div className="mb-10 grid gap-6 lg:grid-cols-[1fr_auto] lg:items-start">
            <SectionCard title="Agent pipeline" subtitle="Deterministic handoffs — completed steps glow">
              <div className="flex flex-wrap gap-3">
                {pipelineState.map((step, i) => (
                  <div
                    key={step.key}
                    className={`flex min-w-[140px] flex-1 flex-col rounded-xl border px-4 py-3 transition ${
                      step.done
                        ? "border-violet-glow/40 bg-violet-950/30 shadow-[0_0_20px_-4px_rgba(167,139,250,0.4)]"
                        : "border-white/5 bg-ink-800/40 opacity-60"
                    }`}
                  >
                    <span className="font-mono text-[10px] text-zinc-500">Step {i + 1}</span>
                    <span className="font-semibold text-white">{step.label}</span>
                    <span className="text-xs text-zinc-500">{step.desc}</span>
                  </div>
                ))}
              </div>
            </SectionCard>
            <div className="flex justify-center lg:justify-end">
              <div className="rounded-2xl border border-white/5 bg-ink-850/80 p-4 shadow-panel">
                <ConfidenceRing value={confidence} />
              </div>
            </div>
          </div>

          <div className="mb-10 grid gap-6 lg:grid-cols-2">
            <SectionCard title="Bug summary" accent="cyan">
              {bugSummary ? (
                <dl className="space-y-3 text-sm">
                  <div>
                    <dt className="text-zinc-500">Title</dt>
                    <dd className="mt-0.5 font-medium text-white">{bugSummary.title}</dd>
                  </div>
                  <div>
                    <dt className="text-zinc-500">Severity</dt>
                    <dd className="mt-0.5 capitalize text-amber-200/90">{bugSummary.severity}</dd>
                  </div>
                  <div>
                    <dt className="text-zinc-500">Scope</dt>
                    <dd className="mt-0.5 text-zinc-300">{bugSummary.scope}</dd>
                  </div>
                  <div>
                    <dt className="text-zinc-500">Symptoms</dt>
                    <dd className="mt-0.5 text-zinc-300">{bugSummary.symptoms}</dd>
                  </div>
                </dl>
              ) : null}
            </SectionCard>

            <SectionCard title="Reproduction" subtitle="Generated artifact + execution result">
              {repro ? (
                <div className="space-y-3 text-sm">
                  <p className="font-mono text-xs text-cyan-glow/90 break-all">
                    {(repro.command as string) ?? ""}
                  </p>
                  <pre className="max-h-40 overflow-auto rounded-lg border border-white/5 bg-black/40 p-3 font-mono text-xs text-zinc-400">
                    {reproResult?.stderr
                      ? String(reproResult.stderr)
                      : reproResult?.stdout
                        ? String(reproResult.stdout)
                        : JSON.stringify(reproResult, null, 2)}
                  </pre>
                  <p className="text-xs text-zinc-500">
                    Artifact:{" "}
                    <span className="font-mono text-zinc-400">{String(repro.artifact_path ?? "")}</span>
                  </p>
                </div>
              ) : null}
            </SectionCard>
          </div>

          <div className="mb-10 grid gap-6 lg:grid-cols-2">
            <SectionCard title="Evidence from logs" accent="amber">
              <div className="space-y-4">
                {evidence?.map((block) => (
                  <div key={block.type}>
                    <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                      {block.type.replace(/_/g, " ")}
                    </h3>
                    {block.lines ? (
                      <pre className="max-h-48 overflow-auto rounded-lg border border-white/5 bg-black/50 p-3 font-mono text-xs leading-relaxed text-emerald-200/80">
                        {block.lines.join("\n")}
                      </pre>
                    ) : null}
                    {block.items ? (
                      <ul className="space-y-2 text-xs">
                        {block.items.map((item, idx) => (
                          <li
                            key={idx}
                            className="rounded-lg border border-white/5 bg-ink-800/50 px-3 py-2 font-mono text-zinc-400"
                          >
                            <span className="text-violet-glow/80">L{item.line}</span> {item.text}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                ))}
              </div>
            </SectionCard>

            <SectionCard title="Orchestration trace" subtitle="Agent starts, ends, and workflow events">
              <ul className="max-h-[28rem] space-y-2 overflow-auto pr-1">
                {trace.map((ev, i) => (
                  <li
                    key={i}
                    className="flex gap-3 rounded-lg border border-white/5 bg-ink-800/40 px-3 py-2 text-xs"
                  >
                    <span className="shrink-0 font-mono text-zinc-600">
                      {ev.ts.slice(11, 19)}
                    </span>
                    <span
                      className={`shrink-0 font-semibold ${
                        ev.event.includes("start")
                          ? "text-cyan-glow"
                          : ev.event.includes("end")
                            ? "text-violet-glow"
                            : "text-zinc-400"
                      }`}
                    >
                      {ev.event}
                    </span>
                    <span className="truncate font-mono text-zinc-500">
                      {JSON.stringify(ev.payload)}
                    </span>
                  </li>
                ))}
              </ul>
            </SectionCard>
          </div>

          <div className="mb-10 grid gap-6 lg:grid-cols-2">
            <SectionCard title="Root cause hypothesis">
              {hypothesis ? (
                <div className="space-y-3 text-sm">
                  <p className="leading-relaxed text-zinc-200">{String(hypothesis.statement ?? "")}</p>
                  <p className="text-xs text-zinc-500">
                    Model confidence:{" "}
                    <span className="font-mono text-violet-glow">
                      {typeof hypothesis.confidence === "number"
                        ? `${(hypothesis.confidence * 100).toFixed(0)}%`
                        : "—"}
                    </span>
                  </p>
                  <ul className="list-inside list-disc space-y-1 text-xs text-zinc-400">
                    {(hypothesis.supporting_evidence as string[] | undefined)?.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </SectionCard>

            <SectionCard title="Reviewer / critic" accent="amber">
              <ul className="space-y-2">
                {findings?.map((f, i) => (
                  <li
                    key={i}
                    className="rounded-lg border border-white/5 bg-ink-800/50 px-3 py-2 text-sm"
                  >
                    <span
                      className={`mr-2 inline-block rounded px-1.5 py-0.5 font-mono text-[10px] uppercase ${
                        f.severity === "high"
                          ? "bg-red-500/20 text-red-300"
                          : f.severity === "medium"
                            ? "bg-amber-500/20 text-amber-200"
                            : "bg-zinc-500/20 text-zinc-400"
                      }`}
                    >
                      {f.severity}
                    </span>
                    {f.issue}
                  </li>
                ))}
              </ul>
            </SectionCard>
          </div>

          <div className="mb-10 grid gap-6 lg:grid-cols-2">
            <SectionCard title="Patch plan">
              {patchPlan ? (
                <div className="space-y-4 text-sm">
                  <div>
                    <h3 className="mb-1 text-xs uppercase text-zinc-500">Files</h3>
                    <ul className="font-mono text-xs text-cyan-glow/90">
                      {(patchPlan.files_impacted as string[] | undefined)?.map((f) => (
                        <li key={f}>{f}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="mb-1 text-xs uppercase text-zinc-500">Approach</h3>
                    <ul className="list-inside list-decimal space-y-1 text-zinc-300">
                      {(patchPlan.approach as string[] | undefined)?.map((a, i) => (
                        <li key={i}>{a}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="mb-1 text-xs uppercase text-zinc-500">Risks</h3>
                    <ul className="list-inside list-disc space-y-1 text-zinc-400">
                      {(patchPlan.risks as string[] | undefined)?.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ) : null}
            </SectionCard>

            <SectionCard title="Validation plan" accent="cyan">
              {validation ? (
                <div className="space-y-4 text-sm">
                  <div>
                    <h3 className="mb-1 text-xs uppercase text-zinc-500">Tests to add</h3>
                    <ul className="space-y-1 font-mono text-xs text-zinc-300">
                      {(validation.tests_to_add as string[] | undefined)?.map((t) => (
                        <li key={t}>{t}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="mb-1 text-xs uppercase text-zinc-500">Regression checks</h3>
                    <ul className="list-inside list-disc space-y-1 text-zinc-400">
                      {(validation.regression_checks as string[] | undefined)?.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ) : null}
            </SectionCard>
          </div>

          {openQs?.length ? (
            <SectionCard title="Open questions">
              <ul className="list-inside list-disc space-y-2 text-sm text-zinc-400">
                {openQs.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </SectionCard>
          ) : null}

          {data.paths ? (
            <footer className="mt-12 border-t border-white/5 pt-8 text-center font-mono text-[11px] text-zinc-600">
              <p className="break-all">{data.paths.final_report_path}</p>
              <p className="mt-1 break-all">{data.paths.trace_path}</p>
            </footer>
          ) : null}
        </>
      ) : (
        <div className="rounded-2xl border border-dashed border-white/10 bg-ink-900/30 py-20 text-center text-sm text-zinc-500">
          Run the pipeline to populate the war room with agent traces and the structured report.
        </div>
      )}
    </div>
  );
}
