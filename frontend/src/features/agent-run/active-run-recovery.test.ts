import assert from "node:assert/strict";
import test from "node:test";

import { restorePersistedAgentRun } from "./active-run-recovery.ts";

test("restores a valid saved run and connects SSE only while it is active", async () => {
  const connected: string[] = [];
  let cleared = false;
  let closed = false;

  const result = await restorePersistedAgentRun({
    runId: "run-valid",
    load: async () => ({ workflow_status: "RUNNING" }),
    connect: (runId) => connected.push(runId),
    markClosed: () => { closed = true; },
    clearStale: () => { cleared = true; },
  });

  assert.equal(result.status, "restored");
  assert.deepEqual(connected, ["run-valid"]);
  assert.equal(closed, false);
  assert.equal(cleared, false);
});

test("restores a valid completed run without reconnecting SSE", async () => {
  let connected = false;
  let closed = false;

  const result = await restorePersistedAgentRun({
    runId: "run-completed",
    load: async () => ({ workflow_status: "COMPLETED" }),
    connect: () => { connected = true; },
    markClosed: () => { closed = true; },
    clearStale: () => undefined,
  });

  assert.equal(result.status, "restored");
  assert.equal(connected, false);
  assert.equal(closed, true);
});

test("clears a missing saved run, returns to initial state, and never starts SSE", async () => {
  let storageValue: string | null = "run-stale";
  let uiState = "error";
  let connected = false;

  const result = await restorePersistedAgentRun({
    runId: storageValue,
    load: async () => {
      throw Object.assign(new Error("Agent run was not found."), {
        status: 404,
        code: "RUN_NOT_FOUND",
      });
    },
    connect: () => { connected = true; },
    markClosed: () => undefined,
    clearStale: () => {
      storageValue = null;
      uiState = "initial";
    },
  });

  assert.equal(result.status, "stale");
  assert.equal(storageValue, null);
  assert.equal(uiState, "initial");
  assert.equal(connected, false);
});

test("does not clear a saved run for network, timeout, or server failures", async () => {
  for (const failure of [
    { kind: "connection" },
    { kind: "timeout" },
    { kind: "server", status: 500, code: "SERVER_ERROR" },
  ]) {
    let cleared = false;
    let connected = false;
    await assert.rejects(
      restorePersistedAgentRun({
        runId: "run-preserved",
        load: async () => {
          throw Object.assign(new Error("temporary failure"), failure);
        },
        connect: () => { connected = true; },
        markClosed: () => undefined,
        clearStale: () => { cleared = true; },
      }),
    );
    assert.equal(cleared, false);
    assert.equal(connected, false);
  }
});
