export type WorkflowStatus = "CREATED" | "RUNNING" | "WAITING" | "COMPLETED" | "FAILED";
export type ConnectionStatus = "idle" | "connecting" | "live" | "reconnecting" | "closed" | "error";
export type AgentRole =
  | "SENSOR_AGENT"
  | "DETECTION_AGENT"
  | "RAG_AGENT"
  | "DIAGNOSIS_AGENT"
  | "MAINTENANCE_AGENT";
export type AgentVisualState = "IDLE" | "WORKING" | "WAITING" | "RETRYING" | "NEEDS_HUMAN" | "DONE" | "ERROR";
export type GraphNodeState = "PENDING" | "ACTIVE" | "COMPLETED" | "WAITING" | "RETRYING" | "ERROR" | "SKIPPED";
export type EquipmentStatus = "NORMAL" | "ANALYZING" | "ABNORMAL" | "DIAGNOSING" | "NEEDS_CHECK" | "MAINTENANCE_RECOMMENDED" | "ERROR";

export type AgentEvent = {
  event_id: string;
  sequence: number;
  run_id: string;
  event_type: string;
  node: string;
  agent_role: string;
  message: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type HumanRequest = {
  request_id: string;
  run_id: string;
  request_type: "ADDITIONAL_INFORMATION" | "APPROVAL";
  question: string;
  requested_fields: string[];
  reason: string;
  action_id?: string | null;
};

export type AnalysisResult = {
  analysis_id: string;
  measurement_id: string;
  model_id: string;
  status: "normal" | "abnormal";
  predicted_class: string;
  confidence?: number | null;
  signal_features: Record<string, number>;
  metadata: Record<string, unknown>;
};

export type AgentRun = {
  run_id: string;
  equipment_id: string;
  measurement_id: string;
  demo_scenario?: "HITL_CONTROLLED" | null;
  workflow_status: WorkflowStatus;
  current_node: string;
  analysis_result?: AnalysisResult | null;
  evidence_status?: string | null;
  evidence_count: number;
  retrieval_retry_count: number;
  diagnosis_candidates: DiagnosisCandidate[];
  inspection_plan: InspectionStep[];
  recommended_actions: RecommendedAction[];
  memory_used_ids: string[];
  inspection_image_ids: string[];
  visual_observations: VisualObservation[];
  version_trace: VersionTrace;
  pending_human_request?: HumanRequest | null;
  final_report_available: boolean;
  created_at: string;
  updated_at: string;
};

export type Evidence = {
  evidence_id: string;
  purpose?: string | null;
  title: string;
  publisher: string;
  source_tier: number;
  page?: number | null;
  section?: string | null;
  content: string;
  retrieval_score?: number | null;
  official_url?: string | null;
};

export type DiagnosisCandidate = {
  candidate_id: string;
  fault_type: string;
  summary: string;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  supporting_visual_observation_ids: string[];
  supporting_memory_ids: string[];
  confidence_level: string;
  uncertainties: string[];
};

export type InspectionStep = {
  step_id: string;
  order: number;
  title: string;
  description: string;
  reason: string;
  related_candidate_ids: string[];
  supporting_evidence_ids: string[];
  required_input: string[];
  safety_note?: string | null;
};

export type RecommendedAction = {
  action_id: string;
  action_type: string;
  priority: string;
  summary: string;
  reason: string;
  supporting_evidence_ids: string[];
  requires_human_approval: boolean;
  limitations: string[];
};

export type HumanInteraction = {
  request_id: string;
  request_type: string;
  request?: Record<string, unknown>;
  response: Record<string, unknown>;
  comment?: string | null;
  actor?: string | null;
  recorded_at: string;
};

export type AgentRunSummary = {
  run_id: string;
  equipment_id: string;
  measurement_id: string;
  demo_scenario?: "HITL_CONTROLLED" | null;
  workflow_status: WorkflowStatus;
  ml_prediction?: string | null;
  ml_confidence?: number | null;
  evidence_count: number;
  final_report_available: boolean;
  hitl_status: "NONE" | "PENDING" | "RESOLVED";
  created_at: string;
  updated_at: string;
};

export type AgentRunList = {
  items: AgentRunSummary[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type FinalReport = {
  run_id: string;
  equipment_id: string;
  measurement_id: string;
  demo_scenario?: "HITL_CONTROLLED" | null;
  analysis_summary: Record<string, unknown>;
  diagnosis_candidates: DiagnosisCandidate[];
  evidence_status?: string | null;
  inspection_plan: InspectionStep[];
  recommended_actions: RecommendedAction[];
  human_interactions: HumanInteraction[];
  limitations: string[];
  citations: Array<Record<string, unknown>>;
  historical_context_used: string[];
  visual_observations: VisualObservation[];
  visual_context_used: string[];
  version_trace: VersionTrace;
  created_at: string;
};

export type VersionTrace = {
  application_version: string;
  model_id: string;
  model_version: string;
  knowledge_pack_id: string;
  knowledge_manifest_version: string;
  workflow_version: string;
};

export type VisualObservationItem = {
  observation_id: string;
  category: string;
  description: string;
  confidence_level: string;
};

export type VisualObservation = {
  image_id: string;
  provider: string;
  model: string;
  observations: VisualObservationItem[];
  visible_components: string[];
  quality: "USABLE" | "LOW_QUALITY" | "UNUSABLE";
  limitations: string[];
  metrics: Record<string, unknown>;
  analysis_error?: string | null;
  created_at: string;
};

export type MeasurementPreview = {
  measurement_id: string;
  equipment_id: string;
  source: string;
  bearing_id: string;
  operating_condition: Record<string, unknown>;
  run_index: number;
  channel: string;
  original_sample_count: number;
  points: Array<{ time: number; value: number }>;
  operating_signals: Record<string, Array<{ time: number; value: number }>>;
};

export type MemoryRecord = {
  memory_id: string;
  equipment_id: string;
  memory_type: "MEASUREMENT" | "ANALYSIS" | "DIAGNOSIS" | "INSPECTION" | "HUMAN_OBSERVATION" | "ACTION" | "MAINTENANCE" | "OUTCOME";
  source_type: "sensor" | "ml_model" | "vision_model" | "agent" | "human" | "maintenance_record" | "system";
  source_id: string;
  status: "OBSERVED" | "MEASURED" | "INFERRED" | "CONFIRMED" | "REJECTED";
  summary: string;
  structured_data: Record<string, unknown>;
  event_time: string;
  recorded_at: string;
  memory_version: number;
};

export type MaintenanceRecord = {
  maintenance_id: string;
  equipment_id: string;
  maintenance_type: string;
  description: string;
  performed_at: string;
  performed_by_role?: string | null;
  related_run_id?: string | null;
  outcome?: string | null;
  source_label: string;
  recorded_at: string;
};

export type TrendPoint = {
  memory_id: string;
  run_id: string;
  measurement_id: string;
  event_time: string;
  operating_condition?: string | null;
  analysis_status?: string | null;
  predicted_class?: string | null;
  rms?: number | null;
  kurtosis?: number | null;
};

export type MemoryHistory = {
  equipment_id: string;
  records: MemoryRecord[];
  maintenance: MaintenanceRecord[];
  trend: { equipment_id: string; points: TrendPoint[]; abnormal_count: number; note: string };
};

export type AgentRunUIState = {
  run?: AgentRun;
  runId?: string;
  workflowStatus: WorkflowStatus | "IDLE";
  currentNode?: string;
  activeAgent?: string;
  agentStates: Record<AgentRole, AgentVisualState>;
  graphNodeStates: Record<string, GraphNodeState>;
  selectedEdge?: "NORMAL" | "ABNORMAL" | "SUFFICIENT" | "PARTIAL" | "INSUFFICIENT" | "CONFLICTING";
  equipmentStatus: EquipmentStatus;
  analysisSummary?: AnalysisResult;
  evidenceStatus?: string;
  evidenceCount: number;
  retryCount: number;
  pendingHumanRequest?: HumanRequest;
  timeline: AgentEvent[];
  reportReady: boolean;
  evidence: Evidence[];
  report?: FinalReport;
  connectionStatus: ConnectionStatus;
  error?: string;
  startedAt?: string;
};
