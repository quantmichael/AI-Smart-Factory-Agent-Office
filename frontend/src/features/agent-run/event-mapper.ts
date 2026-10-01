import type { AgentRole } from "./types.ts";

export const AGENT_ROLES: AgentRole[] = [
  "SENSOR_AGENT",
  "DETECTION_AGENT",
  "RAG_AGENT",
  "DIAGNOSIS_AGENT",
  "MAINTENANCE_AGENT",
];

export const NODE_AGENT: Record<string, AgentRole> = {
  load_sensor_data: "SENSOR_AGENT",
  load_equipment_memory: "SENSOR_AGENT",
  run_detection: "DETECTION_AGENT",
  check_abnormal: "DETECTION_AGENT",
  check_inspection_image: "DIAGNOSIS_AGENT",
  analyze_inspection_image: "DIAGNOSIS_AGENT",
  merge_visual_context: "DIAGNOSIS_AGENT",
  save_normal_state: "DETECTION_AGENT",
  generate_normal_report: "DETECTION_AGENT",
  build_rag_query: "RAG_AGENT",
  retrieve_knowledge: "RAG_AGENT",
  refine_query: "RAG_AGENT",
  retrieve_counter_evidence: "RAG_AGENT",
  diagnose: "DIAGNOSIS_AGENT",
  verify_evidence: "DIAGNOSIS_AGENT",
  request_additional_information: "DIAGNOSIS_AGENT",
  await_human_input: "DIAGNOSIS_AGENT",
  resume_after_human: "DIAGNOSIS_AGENT",
  update_context: "DIAGNOSIS_AGENT",
  build_inspection_plan: "MAINTENANCE_AGENT",
  recommend_action: "MAINTENANCE_AGENT",
  check_human_approval: "MAINTENANCE_AGENT",
  request_human_approval: "MAINTENANCE_AGENT",
  generate_report: "MAINTENANCE_AGENT",
};

export const GRAPH_NODES = [
  "load_sensor_data",
  "load_equipment_memory",
  "run_detection",
  "check_abnormal",
  "check_inspection_image",
  "analyze_inspection_image",
  "build_rag_query",
  "retrieve_knowledge",
  "diagnose",
  "verify_evidence",
  "build_inspection_plan",
  "recommend_action",
  "generate_report",
] as const;

export const RAG_ROUTE_NODES = [
  "check_inspection_image",
  "analyze_inspection_image",
  "build_rag_query",
  "retrieve_knowledge",
  "diagnose",
  "verify_evidence",
  "build_inspection_plan",
  "recommend_action",
  "generate_report",
];

export const NODE_ACTIVITY: Record<string, string> = {
  initialize_run: "진단 실행을 초기화하는 중…",
  load_sensor_data: "측정 데이터와 설비 정보를 불러오는 중…",
  load_equipment_memory: "설비의 과거 진단 이력을 불러오는 중…",
  run_detection: "진동 특성을 분석하는 중…",
  check_abnormal: "정상·이상 경로를 판정하는 중…",
  check_inspection_image: "선택된 설비 점검 이미지를 확인하는 중…",
  analyze_inspection_image: "이미지에서 직접 관찰 가능한 항목을 분석하는 중…",
  merge_visual_context: "시각 관찰을 진단 Context에 분리해 추가하는 중…",
  build_rag_query: "기술문서 검색 질의를 생성하는 중…",
  retrieve_knowledge: "승인된 기술문서에서 근거를 검색하는 중…",
  diagnose: "근거 기반 진단 후보를 구성하는 중…",
  verify_evidence: "진단 근거의 충족 여부를 검증하는 중…",
  refine_query: "근거 검색 질의를 보완하는 중…",
  retrieve_counter_evidence: "반대 근거를 검색하는 중…",
  build_inspection_plan: "현장 점검 계획을 작성하는 중…",
  recommend_action: "권고 조치를 작성하는 중…",
  request_human_approval: "작업자 검토를 기다리는 중…",
  request_additional_information: "현장 추가 정보를 기다리는 중…",
  await_human_input: "사람 검토 지점에서 안전하게 대기 중…",
  resume_after_human: "작업자 결정을 반영하는 중…",
  update_context: "진단 컨텍스트를 갱신하는 중…",
  generate_normal_report: "정상 상태 보고서를 작성하는 중…",
  generate_report: "최종 진단 보고서를 작성하는 중…",
};

export const ROLE_LABEL: Record<AgentRole, string> = {
  SENSOR_AGENT: "센서 에이전트",
  DETECTION_AGENT: "이상탐지 에이전트",
  RAG_AGENT: "기술지식 에이전트",
  DIAGNOSIS_AGENT: "진단 에이전트",
  MAINTENANCE_AGENT: "정비지원 에이전트",
};

export const WORKFLOW_LABEL: Record<string, string> = {
  IDLE: "대기", CREATED: "생성됨", RUNNING: "실행 중",
  WAITING: "작업자 확인 대기", COMPLETED: "완료", FAILED: "실패",
};

export const CONNECTION_LABEL: Record<string, string> = {
  idle: "대기", connecting: "연결 중", live: "실시간 연결", reconnecting: "재연결 중",
  closed: "연결 종료", error: "실시간 연결 끊김",
};

export const EQUIPMENT_STATUS_LABEL: Record<string, string> = {
  NORMAL: "정상", ANALYZING: "분석 중", ABNORMAL: "이상 감지",
  DIAGNOSING: "진단 중", NEEDS_CHECK: "점검 필요",
  MAINTENANCE_RECOMMENDED: "정비 권고", ERROR: "오류",
};

export const AGENT_STATE_LABEL: Record<string, string> = {
  IDLE: "대기", WORKING: "작업 중", WAITING: "대기 중", RETRYING: "재검색",
  NEEDS_HUMAN: "사람 검토", DONE: "완료", ERROR: "오류",
};

export const GRAPH_STATE_LABEL: Record<string, string> = {
  PENDING: "대기", ACTIVE: "실행 중", COMPLETED: "완료", WAITING: "사람 대기",
  RETRYING: "재시도", ERROR: "오류", SKIPPED: "건너뜀",
};

export const EVIDENCE_STATUS_LABEL: Record<string, string> = {
  SUFFICIENT: "근거 충분", PARTIAL: "근거 일부 확보", INSUFFICIENT: "근거 부족", CONFLICTING: "근거 상충",
};

export const PRIORITY_LABEL: Record<string, string> = { LOW: "낮음", MEDIUM: "보통", HIGH: "높음", CRITICAL: "긴급" };
export const ACTION_LABEL: Record<string, string> = {
  monitor: "상태 지속 관찰", inspection_required: "추가 점검 필요", maintenance_required: "정비 필요", shutdown_review: "설비 정지 검토",
};
export const PURPOSE_LABEL: Record<string, string> = {
  diagnosis: "진단 근거", supporting: "보조 근거", counter_evidence: "반대 근거", technical_reference: "기술 참고자료",
};
export const QUALITY_LABEL: Record<string, string> = { USABLE: "사용 가능", LOW_QUALITY: "품질 낮음", UNUSABLE: "사용 불가" };
export const CONFIDENCE_LABEL: Record<string, string> = { LOW: "낮음", MEDIUM: "보통", HIGH: "높음" };
export const MEMORY_TYPE_LABEL: Record<string, string> = { MEASUREMENT: "측정", ANALYSIS: "분석", DIAGNOSIS: "진단", INSPECTION: "점검", HUMAN_OBSERVATION: "작업자 관찰", ACTION: "조치", MAINTENANCE: "정비", OUTCOME: "결과" };
export const MEMORY_STATUS_LABEL: Record<string, string> = { OBSERVED: "관찰됨", MEASURED: "측정됨", INFERRED: "추론됨", CONFIRMED: "확인됨", REJECTED: "기각됨" };
export const SOURCE_TYPE_LABEL: Record<string, string> = { sensor: "센서", ml_model: "ML 모델", vision_model: "이미지 모델", agent: "에이전트", human: "작업자", maintenance_record: "정비 기록", system: "시스템" };

export function measurementDisplayName(id?: string, demoScenario?: string | null): string {
  if (!id) return "측정 데이터 없음";
  if (demoScenario === "HITL_CONTROLLED") return "측정 데이터 C · HITL 시연";
  if (id.includes(":K001:")) return "측정 데이터 A";
  if (id.includes(":KA01:")) return "측정 데이터 B";
  if (id.includes(":KI01:")) return "측정 데이터 C";
  if (id.startsWith("paderborn:")) return "Paderborn 베어링 측정 데이터";
  return "측정 데이터";
}

export function executionStatusDisplay(status: string, hasRun: boolean): string {
  if (status === "COMPLETED") return "진단 완료";
  if (status === "FAILED") return "진단 실패";
  if (status === "WAITING") return "작업자 확인 대기";
  if (status === "CREATED") return "진단 준비 중";
  if (status === "RUNNING") return "진단 실행 중";
  return hasRun ? "진단 상태 확인 중" : "실행 전";
}

export function currentTaskDisplay(status: string, node: string | undefined, hasRun: boolean): string {
  if (status === "COMPLETED") return "최종 진단 보고서 작성 완료";
  if (status === "FAILED") return "진단 실행이 중단되었습니다";
  if (status === "WAITING") return "작업자 입력을 기다리는 중입니다";
  return NODE_ACTIVITY[node ?? ""] ?? (hasRun ? "실행 상태 동기화 완료" : "진단 시작 대기");
}

export type MeasurementReplayState = "NO_DATA" | "REPLAYING" | "DIAGNOSING" | "COMPLETED" | "FAILED";

export function measurementReplayState(
  hasMeasurementData: boolean,
  workflowStatus: string,
  requestPending = false,
): MeasurementReplayState {
  if (workflowStatus === "FAILED") return "FAILED";
  if (workflowStatus === "COMPLETED") return "COMPLETED";
  if (requestPending || ["CREATED", "RUNNING", "WAITING"].includes(workflowStatus)) return "DIAGNOSING";
  return hasMeasurementData ? "REPLAYING" : "NO_DATA";
}

export function evidenceExplanation(purpose?: string | null, title?: string): string {
  const text = `${purpose ?? ""} ${title ?? ""}`.toLowerCase();
  if (text.includes("counter") || text.includes("반대")) return "현재 진단과 다른 가능성을 확인하기 위해 함께 검토한 근거입니다.";
  if (text.includes("bearing") || text.includes("베어링")) return "베어링 손상 형태와 진동 특징을 설명해 현재 진단 후보를 뒷받침하는 근거입니다.";
  return "현재 측정 결과를 해석하고 점검 방향을 정하는 데 참고한 기술 근거입니다.";
}

export const EVENT_LABEL: Record<string, string> = {
  workflow_started: "워크플로 실행 시작", node_started: "노드 실행 시작", node_completed: "노드 실행 완료",
  equipment_memory_loaded: "설비 장기기억 Context 로드 완료",
  inspection_image_uploaded: "설비 점검 이미지 연결 완료",
  vision_analysis_completed: "이미지 관찰 분석 완료",
  visual_context_added: "시각 관찰 Context 추가",
  detection_normal: "정상 상태 판정", detection_abnormal: "이상 상태 감지",
  retrieval_completed: "기술 근거 검색 완료", evidence_status_changed: "근거 충족 상태 변경",
  inspection_plan_created: "점검 계획 생성", action_recommended: "권고 조치 생성",
  human_input_required: "작업자 판단 요청", human_input_received: "작업자 입력 접수",
  workflow_resumed: "워크플로 재개", report_generated: "최종 보고서 생성",
  workflow_completed: "워크플로 완료", workflow_error: "워크플로 오류",
};
