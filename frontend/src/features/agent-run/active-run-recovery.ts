type RestorableRun = { workflow_status: string };

type RestorePersistedRunOptions<T extends RestorableRun> = {
  runId: string;
  load: (runId: string) => Promise<T>;
  connect: (runId: string) => void;
  markClosed: () => void;
  clearStale: () => void;
};

export type PersistedRunRestoreResult<T> =
  | { status: "restored"; run: T }
  | { status: "stale" };

export function isMissingAgentRun(error: unknown): boolean {
  if (typeof error !== "object" || error === null) return false;
  const candidate = error as { status?: unknown; code?: unknown };
  return candidate.status === 404 && candidate.code === "RUN_NOT_FOUND";
}

export async function restorePersistedAgentRun<T extends RestorableRun>({
  runId,
  load,
  connect,
  markClosed,
  clearStale,
}: RestorePersistedRunOptions<T>): Promise<PersistedRunRestoreResult<T>> {
  try {
    const run = await load(runId);
    if (run.workflow_status === "RUNNING" || run.workflow_status === "CREATED") {
      connect(runId);
    } else {
      markClosed();
    }
    return { status: "restored", run };
  } catch (error: unknown) {
    if (!isMissingAgentRun(error)) throw error;
    clearStale();
    return { status: "stale" };
  }
}
