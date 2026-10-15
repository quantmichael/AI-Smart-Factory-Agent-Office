import assert from "node:assert/strict";
import test from "node:test";

import { initialAgentRunState } from "./reducer.ts";
import { resultOverview } from "./result-overview.ts";
import type { AnalysisResult, FinalReport } from "./types.ts";

const analysis = (status: "normal" | "abnormal"): AnalysisResult => ({
  analysis_id: "analysis-test", measurement_id: "measurement-test", model_id: "model-test",
  status, predicted_class: status === "normal" ? "healthy" : "damaged",
  confidence: 0.9, signal_features: {}, metadata: {},
});

test("selection and running state never invent an ML result", () => {
  const idle = resultOverview(initialAgentRunState, false);
  const selected = resultOverview(initialAgentRunState, true);
  const running = resultOverview({ ...initialAgentRunState, runId: "run-test", workflowStatus: "RUNNING" }, true);
  assert.equal(idle.phase, "idle");
  assert.match(selected.workflowDescription, /진단 시작/);
  assert.equal(running.phase, "running");
  assert.equal(running.prediction, null);
  assert.equal(running.predictionTitle, "판정 전");
  const starting = resultOverview(initialAgentRunState, true, true);
  assert.equal(starting.phase, "starting");
  assert.equal(starting.prediction, null);
});

test("ML prediction stays distinct from a waiting approval", () => {
  const view = resultOverview({
    ...initialAgentRunState, runId: "run-test", workflowStatus: "WAITING", analysisSummary: analysis("abnormal"),
    pendingHumanRequest: { run_id: "run-test", request_id: "request-test", request_type: "APPROVAL", question: "승인?", reason: "중요 조치", requested_fields: [] },
  }, true);
  assert.equal(view.phase, "waiting");
  assert.equal(view.predictionTitle, "이상 감지");
  assert.match(view.workflowDescription, /승인/);
});

test("a completed normal result does not claim that maintenance finished", () => {
  const view = resultOverview({
    ...initialAgentRunState, runId: "run-test", workflowStatus: "COMPLETED", analysisSummary: analysis("normal"), reportReady: true,
  }, true);
  assert.equal(view.phase, "completed");
  assert.equal(view.predictionTitle, "정상");
  assert.match(view.workflowDescription, /정비가 완료되었다는 뜻은 아닙니다/);
  assert.equal(view.reportAvailable, true);
});

test("report recommendations are shown only after workflow completion", () => {
  const report: FinalReport = {
    run_id: "run-test", equipment_id: "equipment-test", measurement_id: "measurement-test",
    analysis_summary: {}, diagnosis_candidates: [{ candidate_id: "candidate-test", fault_type: "bearing", summary: "베어링 손상 가능성", supporting_evidence_ids: [], contradicting_evidence_ids: [], supporting_visual_observation_ids: [], supporting_memory_ids: [], confidence_level: "medium", uncertainties: [] }], inspection_plan: [],
    recommended_actions: [{ action_id: "action-test", action_type: "INSPECT", priority: "medium", summary: "베어링 상태를 점검하세요", reason: "근거 검토", supporting_evidence_ids: [], requires_human_approval: false, limitations: [] }],
    human_interactions: [], limitations: [], citations: [], historical_context_used: [],
    visual_observations: [], visual_context_used: [],
    version_trace: { application_version: "test", model_id: "model-test", model_version: "test", knowledge_pack_id: "test", knowledge_manifest_version: "test", workflow_version: "test" },
    created_at: "2026-10-15T00:00:00Z",
  };
  const running = resultOverview({ ...initialAgentRunState, runId: "run-test", workflowStatus: "RUNNING", report }, true);
  const completed = resultOverview({ ...initialAgentRunState, runId: "run-test", workflowStatus: "COMPLETED", report }, true);
  assert.equal(running.recommendation, null);
  assert.equal(running.diagnosisSummary, null);
  assert.equal(completed.recommendation, "베어링 상태를 점검하세요");
  assert.equal(completed.diagnosisSummary, "베어링 손상 가능성");
  assert.equal(completed.actionAvailable, true);
});

test("failed workflow preserves the known ML result without marking success", () => {
  const view = resultOverview({
    ...initialAgentRunState, runId: "run-test", workflowStatus: "FAILED", analysisSummary: analysis("abnormal"),
    connectionStatus: "error",
  }, true);
  assert.equal(view.phase, "failed");
  assert.equal(view.prediction, "abnormal");
  assert.equal(view.reportAvailable, false);
});
