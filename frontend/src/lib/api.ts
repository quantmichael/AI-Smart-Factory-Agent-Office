import type {
  AgentEvent,
  AgentRunList,
  AgentRun,
  Evidence,
  FinalReport,
  MeasurementPreview,
  MemoryHistory,
} from "@/features/agent-run/types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
export const API_V1 = `${API_BASE_URL}/api/v1`;

export type HealthResponse = { status: "ok"; service: string; version: string };
export type RunCreated = { run_id: string; status: "RUNNING"; current_node: string; created_at: string };
export type HumanInputPayload = {
  request_id: string;
  response: Record<string, unknown>;
  comment?: string;
  actor?: string;
};

export type KnowledgeSummary = {
  knowledge_pack: string;
  knowledge_version: string;
  vector_store: string;
  collection: string;
  document_count: number;
  chunk_count: number;
  embedding_count: number;
  embedding_method: string;
  embedding_dimension: number;
  distance_metric: string;
  status: string;
};

export type KnowledgeDocument = {
  document_id: string;
  title: string;
  publisher: string;
  document_type: string;
  source: string;
  version: string;
  license: string;
  license_status: string;
  official_url?: string | null;
  indexed_pages: number[];
  chunk_count: number;
};

export type KnowledgeChunk = {
  chunk_id: string;
  page?: number | null;
  section?: string | null;
  content: string;
};

export type KnowledgeDocumentDetail = {
  document: KnowledgeDocument;
  chunks: {
    items: KnowledgeChunk[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
};

export type KnowledgeSearchResult = {
  query: { query_id: string; query_text: string; purpose: string; top_k: number };
  evidence: Array<Evidence & { document_id: string; chunk_id: string; source_id: string; document_type: string }>;
  stats: { returned: number; latency_ms: number; retrieved_chunk_ids: string[]; scores: number[] };
};

export type ModelFeature = { name: string; channel: string; statistic: string };
export type ModelFeatureImportance = { rank: number; feature: string; importance: number };
export type ModelMetricLevel = {
  sample_count: number;
  accuracy?: number | null;
  precision?: number | null;
  recall?: number | null;
  f1?: number | null;
  roc_auc?: number | null;
  damaged_recall?: number | null;
  confusion_matrix: number[][];
};
export type CurrentModel = {
  status: string;
  model: {
    model_id: string;
    model_type: string;
    version: string;
    task: string;
    classes: string[];
    trained_at: string;
    dataset: string;
    feature_version: string;
    feature_count: number;
  };
  features: ModelFeature[];
  feature_importance: ModelFeatureImportance[];
  evaluation: {
    aggregation_rule?: string | null;
    levels: Record<string, ModelMetricLevel>;
  };
  training_data: {
    dataset: string;
    is_local_subset: boolean;
    split_method?: string | null;
    group_key?: string | null;
    test_ratio?: number | null;
    random_seed?: number | null;
    train_measurement_count?: number | null;
    test_measurement_count?: number | null;
    train_window_count?: number | null;
    test_window_count?: number | null;
    train_bearing_ids: string[];
    test_bearing_ids: string[];
    shared_bearing_ids: string[];
    measurement_overlap_count?: number | null;
    leakage_check_passed?: boolean | null;
    diagnostic_channels: string[];
    window_duration_sec?: number | null;
    overlap_percent?: number | null;
    sampling_rate_hz?: number | null;
    known_limitation?: string | null;
  };
  artifact_limitations: string[];
};

export type SystemComponentStatus = "READY" | "DEGRADED" | "UNAVAILABLE" | "UNKNOWN";
export type SystemComponentGroup = "CORE_AI" | "KNOWLEDGE_AGENT" | "DATA_STATE" | "VERSION_RUNTIME";
export type SystemComponent = {
  component_id: string;
  name: string;
  group: SystemComponentGroup;
  status: SystemComponentStatus;
  summary: string;
  verification: string;
  details: Array<{ label: string; value: string }>;
};
export type SystemStatusView = {
  overall_status: SystemComponentStatus;
  checked_at: string;
  application_version: string;
  workflow_version: string;
  components: SystemComponent[];
};

export type ApiErrorKind = "connection" | "timeout" | "server" | "request";

export class ApiClientError extends Error {
  readonly kind: ApiErrorKind;
  readonly status?: number;
  readonly code?: string;

  constructor(
    message: string,
    kind: ApiErrorKind,
    status?: number,
    code?: string,
  ) {
    super(message);
    this.name = "ApiClientError";
    this.kind = kind;
    this.status = status;
    this.code = code;
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_V1}${path}`, { cache: "no-store", ...init });
  } catch (error: unknown) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiClientError("백엔드 서버의 응답 시간이 초과되었습니다.", "timeout");
    }
    throw new ApiClientError(
      "백엔드 서버에 연결할 수 없습니다. 잠시 후 자동으로 다시 확인합니다.",
      "connection",
    );
  }

  const body = (await response.json().catch(() => ({}))) as T & {
    error?: { code?: string; message?: string };
  };
  if (!response.ok) {
    const message = body.error?.message
      ?? (response.status >= 500
        ? "서버가 요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요."
        : "요청을 처리하지 못했습니다. 입력과 실행 상태를 확인해 주세요.");
    throw new ApiClientError(
      message,
      response.status >= 500 ? "server" : "request",
      response.status,
      body.error?.code,
    );
  }
  return body;
}

export function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health", { signal });
}

export function createAgentRun(equipmentId: string, measurementId: string, inspectionImageIds: string[] = [], demoScenario?: "HITL_CONTROLLED"): Promise<RunCreated> {
  return requestJson<RunCreated>("/agent/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ equipment_id: equipmentId, measurement_id: measurementId, inspection_image_ids: inspectionImageIds, ...(demoScenario ? { demo_scenario: demoScenario } : {}) }),
  });
}

export function stageInspectionImage(equipmentId: string, file: File) {
  return requestJson<{ image_id: string }>(
    `/agent/inspection-images?equipment_id=${encodeURIComponent(equipmentId)}`,
    { method: "POST", headers: { "Content-Type": file.type, "X-Filename": file.name }, body: file },
  );
}

export function uploadRunInspectionImage(runId: string, file: File) {
  return requestJson<{ image_id: string }>(
    `/agent/runs/${encodeURIComponent(runId)}/inspection-images`,
    { method: "POST", headers: { "Content-Type": file.type, "X-Filename": file.name }, body: file },
  );
}

export function inspectionImageUrl(imageId: string) {
  return `${API_V1}/agent/inspection-images/${encodeURIComponent(imageId)}`;
}

export function fetchAgentRun(runId: string): Promise<AgentRun> {
  return requestJson<AgentRun>(`/agent/runs/${encodeURIComponent(runId)}`);
}

export type AgentRunFilters = {
  page?: number;
  pageSize?: number;
  workflowStatus?: string;
  measurementId?: string;
  equipmentId?: string;
  mlPrediction?: string;
};

export function fetchAgentRuns(filters: AgentRunFilters = {}): Promise<AgentRunList> {
  const params = new URLSearchParams();
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? 20));
  if (filters.workflowStatus) params.set("workflow_status", filters.workflowStatus);
  if (filters.measurementId) params.set("measurement_id", filters.measurementId);
  if (filters.equipmentId) params.set("equipment_id", filters.equipmentId);
  if (filters.mlPrediction) params.set("ml_prediction", filters.mlPrediction);
  return requestJson<AgentRunList>(`/agent/runs?${params.toString()}`);
}

export async function fetchAgentEvents(runId: string, afterSequence = 0): Promise<AgentEvent[]> {
  const result = await requestJson<{ run_id: string; events: AgentEvent[] }>(
    `/agent/runs/${encodeURIComponent(runId)}/events?after_sequence=${afterSequence}`,
  );
  return result.events;
}

export async function fetchAgentEvidence(runId: string): Promise<Evidence[]> {
  const result = await requestJson<{ run_id: string; evidence: Evidence[] }>(
    `/agent/runs/${encodeURIComponent(runId)}/evidence`,
  );
  return result.evidence;
}

export function fetchAgentReport(runId: string): Promise<FinalReport> {
  return requestJson<FinalReport>(`/agent/runs/${encodeURIComponent(runId)}/report`);
}

export function submitHumanInput(runId: string, payload: HumanInputPayload): Promise<AgentRun> {
  return requestJson<AgentRun>(`/agent/runs/${encodeURIComponent(runId)}/human-input`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function fetchMeasurementPreview(measurementId: string): Promise<MeasurementPreview> {
  return requestJson<MeasurementPreview>(
    `/measurements/${encodeURIComponent(measurementId)}/preview?max_points=160`,
  );
}

export function fetchEquipmentHistory(equipmentId: string): Promise<MemoryHistory> {
  return requestJson<MemoryHistory>(`/equipment/${encodeURIComponent(equipmentId)}/history`);
}

export function fetchKnowledgeSummary(): Promise<KnowledgeSummary> {
  return requestJson<KnowledgeSummary>("/knowledge/summary");
}

export async function fetchKnowledgeDocuments(): Promise<KnowledgeDocument[]> {
  const result = await requestJson<{ documents: KnowledgeDocument[]; total: number }>("/knowledge/documents");
  return result.documents;
}

export function fetchKnowledgeDocument(documentId: string, page = 1, pageSize = 8): Promise<KnowledgeDocumentDetail> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  return requestJson<KnowledgeDocumentDetail>(`/knowledge/documents/${encodeURIComponent(documentId)}?${params.toString()}`);
}

export function searchKnowledge(query: string, topK: number, purpose: string): Promise<KnowledgeSearchResult> {
  return requestJson<KnowledgeSearchResult>("/knowledge/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: topK, purpose }),
  });
}

export function fetchCurrentModel(): Promise<CurrentModel> {
  return requestJson<CurrentModel>("/models/current");
}

export function fetchSystemStatus(): Promise<SystemStatusView> {
  return requestJson<SystemStatusView>("/system/status");
}
