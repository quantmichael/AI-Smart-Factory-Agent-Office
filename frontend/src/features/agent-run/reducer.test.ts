import assert from "node:assert/strict";
import test from "node:test";

import { agentRunReducer, initialAgentRunState } from "./reducer.ts";
import type { AgentEvent, AgentRun } from "./types.ts";

const event = (sequence: number, eventType: string, node: string, agentRole: string, payload: Record<string, unknown> = {}): AgentEvent => ({
  event_id: `event-${sequence}`,
  sequence,
  run_id: "run-test",
  event_type: eventType,
  node,
  agent_role: agentRole,
  message: eventType,
  payload,
  created_at: new Date(sequence * 1000).toISOString(),
});

const run: AgentRun = {
  run_id: "run-test",
  equipment_id: "rig",
  measurement_id: "measurement",
  workflow_status: "COMPLETED",
  current_node: "generate_report",
  analysis_result: null,
  evidence_status: "SUFFICIENT",
  evidence_count: 2,
  retrieval_retry_count: 0,
  diagnosis_candidates: [],
  inspection_plan: [],
  recommended_actions: [],
  memory_used_ids: [],
  inspection_image_ids: [],
  visual_observations: [],
  version_trace: { application_version: "test", model_id: "model", model_version: "1", knowledge_pack_id: "bearing_v1", knowledge_manifest_version: "1", workflow_version: "test" },
  pending_human_request: null,
  final_report_available: true,
  created_at: new Date(0).toISOString(),
  updated_at: new Date(1).toISOString(),
};

test("deduplicates and sequence-sorts persisted events", () => {
  const state = agentRunReducer(initialAgentRunState, {
    type: "HYDRATE",
    run,
    events: [event(2, "node_completed", "run_detection", "DETECTION_AGENT"), event(1, "node_started", "run_detection", "DETECTION_AGENT"), event(2, "node_completed", "run_detection", "DETECTION_AGENT")],
  });
  assert.deepEqual(state.timeline.map((item) => item.sequence), [1, 2]);
});

test("normal route skips RAG and diagnosis nodes", () => {
  let state = agentRunReducer(initialAgentRunState, { type: "EVENT", event: event(1, "detection_normal", "run_detection", "DETECTION_AGENT") });
  state = agentRunReducer(state, { type: "EVENT", event: event(2, "node_started", "generate_normal_report", "DETECTION_AGENT") });
  state = agentRunReducer(state, { type: "EVENT", event: event(3, "node_completed", "generate_normal_report", "DETECTION_AGENT") });
  assert.equal(state.selectedEdge, "NORMAL");
  assert.equal(state.graphNodeStates.retrieve_knowledge, "SKIPPED");
  assert.equal(state.graphNodeStates.generate_report, "COMPLETED");
  assert.equal(state.equipmentStatus, "NORMAL");
});

test("abnormal retrieval maps evidence and diagnosis state", () => {
  let state = agentRunReducer(initialAgentRunState, { type: "EVENT", event: event(1, "detection_abnormal", "run_detection", "DETECTION_AGENT") });
  state = agentRunReducer(state, { type: "EVENT", event: event(2, "retrieval_completed", "retrieve_knowledge", "RAG_AGENT", { evidence_count: 5 }) });
  assert.equal(state.selectedEdge, "ABNORMAL");
  assert.equal(state.evidenceCount, 5);
  assert.equal(state.equipmentStatus, "DIAGNOSING");
});

test("partial evidence exposes the retry UI state", () => {
  const state = agentRunReducer(initialAgentRunState, { type: "EVENT", event: event(1, "evidence_status_changed", "verify_evidence", "DIAGNOSIS_AGENT", { evidence_status: "PARTIAL", retry_count: 1 }) });
  assert.equal(state.retryCount, 1);
  assert.equal(state.agentStates.RAG_AGENT, "RETRYING");
  assert.equal(state.graphNodeStates.retrieve_knowledge, "RETRYING");
});

test("HITL event pauses the UI and resume event continues it", () => {
  let state = agentRunReducer(initialAgentRunState, { type: "EVENT", event: event(1, "human_input_required", "request_human_approval", "MAINTENANCE_AGENT") });
  assert.equal(state.workflowStatus, "WAITING");
  assert.equal(state.agentStates.MAINTENANCE_AGENT, "NEEDS_HUMAN");
  state = agentRunReducer(state, { type: "EVENT", event: event(2, "workflow_resumed", "await_human_input", "DIAGNOSIS_AGENT") });
  assert.equal(state.workflowStatus, "RUNNING");
});

test("report payload marks the report ready", () => {
  const report = {
    run_id: "run-test", equipment_id: "rig", measurement_id: "measurement", analysis_summary: {}, diagnosis_candidates: [], evidence_status: null,
    inspection_plan: [], recommended_actions: [], human_interactions: [], limitations: ["Decision support only"], citations: [], historical_context_used: [], visual_observations: [], visual_context_used: [], version_trace: run.version_trace, created_at: new Date().toISOString(),
  };
  const state = agentRunReducer(initialAgentRunState, { type: "REPORT", report });
  assert.equal(state.reportReady, true);
  assert.equal(state.report?.limitations[0], "Decision support only");
});

test("clears a transient connection error without resetting the active run", () => {
  const failed = agentRunReducer(initialAgentRunState, { type: "ERROR", message: "연결 오류" });
  const cleared = agentRunReducer(failed, { type: "CLEAR_ERROR" });

  assert.equal(failed.error, "연결 오류");
  assert.equal(cleared.error, undefined);
  assert.equal(cleared.workflowStatus, failed.workflowStatus);
});
