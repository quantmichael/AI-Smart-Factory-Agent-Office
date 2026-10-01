import assert from "node:assert/strict";
import { afterEach, test } from "node:test";

import {
  ApiClientError,
  createAgentRun,
  fetchAgentRuns,
  fetchHealth,
  fetchKnowledgeDocument,
  fetchKnowledgeDocuments,
  fetchKnowledgeSummary,
  fetchCurrentModel,
  fetchSystemStatus,
  searchKnowledge,
} from "./api.ts";
import { currentTaskDisplay, executionStatusDisplay, measurementDisplayName, measurementReplayState } from "../features/agent-run/event-mapper.ts";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
});

test("maps a network failure to a user-facing backend connection error", async () => {
  globalThis.fetch = async () => {
    throw new TypeError("Failed to fetch");
  };

  await assert.rejects(fetchHealth(), (error: unknown) => {
    assert.ok(error instanceof ApiClientError);
    assert.equal(error.kind, "connection");
    assert.doesNotMatch(error.message, /Failed to fetch/);
    return true;
  });
});

test("maps a server failure to a user-facing request error", async () => {
  globalThis.fetch = async () => new Response("{}", {
    status: 503,
    headers: { "Content-Type": "application/json" },
  });

  await assert.rejects(fetchHealth(), (error: unknown) => {
    assert.ok(error instanceof ApiClientError);
    assert.equal(error.kind, "server");
    assert.equal(error.status, 503);
    assert.match(error.message, /서버가 요청을 처리하지 못했습니다/);
    return true;
  });
});

test("uses neutral sample names without changing their internal measurement IDs", () => {
  assert.equal(measurementDisplayName("paderborn:K001:N09_M07_F10:01"), "측정 데이터 A");
  assert.equal(measurementDisplayName("paderborn:KA01:N09_M07_F10:01"), "측정 데이터 B");
  assert.equal(measurementDisplayName("paderborn:KI01:N09_M07_F10:01"), "측정 데이터 C");
  assert.equal(
    measurementDisplayName("paderborn:KA01:N09_M07_F10:02", "HITL_CONTROLLED"),
    "측정 데이터 C · HITL 시연",
  );
});

test("sends the original measurement ID in the existing Agent Run request", async () => {
  const measurementId = "paderborn:KA01:N09_M07_F10:01";
  let requestBody = "";
  globalThis.fetch = async (_input, init) => {
    requestBody = String(init?.body ?? "");
    return new Response(JSON.stringify({ run_id: "run-test", events_url: "/events" }), {
      status: 201,
      headers: { "Content-Type": "application/json" },
    });
  };

  await createAgentRun("paderborn-bearing-test-rig", measurementId);

  assert.equal(JSON.parse(requestBody).measurement_id, measurementId);
});

test("sends the disclosed HITL demo condition only for measurement C", async () => {
  const measurementId = "paderborn:KA01:N09_M07_F10:02";
  let requestBody = "";
  globalThis.fetch = async (_input, init) => {
    requestBody = String(init?.body ?? "");
    return Response.json({ run_id: "run-hitl-demo", events_url: "/events" }, { status: 201 });
  };

  await createAgentRun(
    "paderborn-bearing-test-rig",
    measurementId,
    [],
    "HITL_CONTROLLED",
  );

  assert.deepEqual(JSON.parse(requestBody), {
    equipment_id: "paderborn-bearing-test-rig",
    measurement_id: measurementId,
    inspection_image_ids: [],
    demo_scenario: "HITL_CONTROLLED",
  });
});

test("shows terminal workflow states instead of stale run or node activity labels", () => {
  assert.equal(executionStatusDisplay("COMPLETED", true), "진단 완료");
  assert.equal(currentTaskDisplay("COMPLETED", "generate_report", true), "최종 진단 보고서 작성 완료");
  assert.equal(executionStatusDisplay("FAILED", true), "진단 실패");
  assert.equal(currentTaskDisplay("WAITING", "request_human_approval", true), "작업자 입력을 기다리는 중입니다");
  assert.equal(executionStatusDisplay("RUNNING", true), "진단 실행 중");
  assert.equal(currentTaskDisplay("RUNNING", "generate_report", true), "최종 진단 보고서를 작성하는 중…");
});

test("separates measurement replay from the existing diagnosis workflow state", () => {
  assert.equal(measurementReplayState(false, "IDLE"), "NO_DATA");
  assert.equal(measurementReplayState(true, "IDLE"), "REPLAYING");
  assert.equal(measurementReplayState(true, "RUNNING"), "DIAGNOSING");
  assert.equal(measurementReplayState(true, "WAITING"), "DIAGNOSING");
  assert.equal(measurementReplayState(true, "IDLE", true), "DIAGNOSING");
  assert.equal(measurementReplayState(true, "COMPLETED"), "COMPLETED");
  assert.equal(measurementReplayState(true, "FAILED"), "FAILED");
});

test("encodes diagnosis history filters without changing their values", async () => {
  let requestedUrl = "";
  globalThis.fetch = async (input) => {
    requestedUrl = String(input);
    return new Response(JSON.stringify({ items: [], page: 2, page_size: 20, total: 0, total_pages: 0 }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };

  await fetchAgentRuns({ page: 2, measurementId: "KA01:N09", workflowStatus: "COMPLETED", mlPrediction: "abnormal" });

  const url = new URL(requestedUrl);
  assert.equal(url.pathname, "/api/v1/agent/runs");
  assert.equal(url.searchParams.get("page"), "2");
  assert.equal(url.searchParams.get("measurement_id"), "KA01:N09");
  assert.equal(url.searchParams.get("workflow_status"), "COMPLETED");
  assert.equal(url.searchParams.get("ml_prediction"), "abnormal");
});

test("loads Knowledge Base summary, documents, and a paginated document detail", async () => {
  const requestedUrls: string[] = [];
  globalThis.fetch = async (input) => {
    const url = String(input);
    requestedUrls.push(url);
    if (url.endsWith("/knowledge/summary")) {
      return Response.json({ status: "READY", document_count: 15, chunk_count: 183 });
    }
    if (url.endsWith("/knowledge/documents")) {
      return Response.json({ documents: [{ document_id: "skf-guide" }], total: 1 });
    }
    return Response.json({ document: { document_id: "skf-guide" }, chunks: { items: [], page: 2 } });
  };

  const summary = await fetchKnowledgeSummary();
  const documents = await fetchKnowledgeDocuments();
  const detail = await fetchKnowledgeDocument("skf-guide", 2, 8);

  assert.equal(summary.document_count, 15);
  assert.equal(documents[0].document_id, "skf-guide");
  assert.equal(detail.chunks.page, 2);
  const detailUrl = new URL(requestedUrls[2]);
  assert.equal(detailUrl.pathname, "/api/v1/knowledge/documents/skf-guide");
  assert.equal(detailUrl.searchParams.get("page"), "2");
  assert.equal(detailUrl.searchParams.get("page_size"), "8");
});

test("loads the active model transparency view from the read-only endpoint", async () => {
  let requestedUrl = "";
  globalThis.fetch = async (input) => {
    requestedUrl = String(input);
    return Response.json({
      status: "READY",
      model: { model_id: "bearing_rf_binary_v1", feature_count: 36 },
      features: [],
      feature_importance: [],
      evaluation: { levels: {} },
      training_data: { train_bearing_ids: [], test_bearing_ids: [], shared_bearing_ids: [], diagnostic_channels: [] },
      artifact_limitations: [],
    });
  };

  const result = await fetchCurrentModel();

  assert.equal(result.model.model_id, "bearing_rf_binary_v1");
  assert.equal(result.model.feature_count, 36);
  assert.equal(new URL(requestedUrl).pathname, "/api/v1/models/current");
});

test("loads the sanitized read-only system status endpoint", async () => {
  let requestedUrl = "";
  globalThis.fetch = async (input) => {
    requestedUrl = String(input);
    return Response.json({
      overall_status: "READY",
      checked_at: "2026-09-30T00:00:00Z",
      application_version: "0.1.0",
      workflow_version: "diagnosis_core_v1",
      components: [{ component_id: "backend_api", status: "READY", details: [] }],
    });
  };

  const result = await fetchSystemStatus();

  assert.equal(result.overall_status, "READY");
  assert.equal(result.components[0].component_id, "backend_api");
  assert.equal(new URL(requestedUrl).pathname, "/api/v1/system/status");
});

test("reuses the existing knowledge search endpoint with the selected Top-K", async () => {
  let requestedUrl = "";
  let requestBody = "";
  globalThis.fetch = async (input, init) => {
    requestedUrl = String(input);
    requestBody = String(init?.body ?? "");
    return Response.json({ query: {}, evidence: [], stats: { returned: 0 } });
  };

  await searchKnowledge("외륜 손상 특징", 10, "DIAGNOSTIC_EVIDENCE");

  assert.equal(new URL(requestedUrl).pathname, "/api/v1/knowledge/search");
  assert.deepEqual(JSON.parse(requestBody), {
    query: "외륜 손상 특징",
    top_k: 10,
    purpose: "DIAGNOSTIC_EVIDENCE",
  });
});
