export type TraceEvent = {
  ts: string;
  event: string;
  payload: Record<string, unknown>;
};

export type RunResponse = {
  paths: {
    final_report_path: string;
    trace_path: string;
    repro_artifact_path: string;
  };
  report: Record<string, unknown>;
  trace: TraceEvent[];
};
