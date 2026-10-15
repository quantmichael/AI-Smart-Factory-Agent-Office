import type { AgentRunUIState } from "./types.ts";

export type ResultOverview = {
  phase: "idle" | "starting" | "running" | "waiting" | "completed" | "failed";
  workflowTitle: string;
  workflowDescription: string;
  prediction: "normal" | "abnormal" | null;
  predictionTitle: string;
  predictionDescription: string;
  recommendation: string | null;
  diagnosisSummary: string | null;
  reportAvailable: boolean;
  evidenceAvailable: boolean;
  inspectionAvailable: boolean;
  actionAvailable: boolean;
};

export function resultOverview(state: AgentRunUIState, measurementSelected: boolean, starting = false): ResultOverview {
  const prediction = state.analysisSummary?.status ?? null;
  const predictionTitle = prediction === "normal" ? "정상" : prediction === "abnormal" ? "이상 감지" : "판정 전";
  const predictionDescription = prediction === "normal"
    ? "선택한 측정 데이터에서 정상으로 분류되었습니다. 이후 설비 상태까지 보증하는 결과는 아닙니다."
    : prediction === "abnormal"
      ? "선택한 측정 데이터에서 이상으로 분류되었습니다. 고장 원인이 확정된 것은 아닙니다."
      : "ML 분석 결과가 아직 없습니다.";

  let phase: ResultOverview["phase"] = "running";
  let workflowTitle = "진단 진행 중";
  let workflowDescription = "측정 데이터를 분석하고 있습니다. 결과가 도착하면 이곳에 표시됩니다.";

  if (starting) {
    phase = "starting";
    workflowTitle = "진단 시작 요청 중";
    workflowDescription = "진단 실행을 생성하고 있습니다. ML 판정은 결과가 도착한 뒤 표시됩니다.";
  } else if (state.workflowStatus === "IDLE" || (!state.runId && !state.run)) {
    phase = "idle";
    workflowTitle = "분석 대기";
    workflowDescription = measurementSelected
      ? "측정 데이터를 선택했습니다. AI 진단 시작을 눌러 분석하세요."
      : "먼저 측정 데이터를 선택한 뒤 AI 진단을 시작하세요.";
  } else if (state.workflowStatus === "WAITING") {
    phase = "waiting";
    workflowTitle = "사람 확인 필요";
    workflowDescription = state.pendingHumanRequest?.request_type === "APPROVAL"
      ? "권고 조치에 대한 승인·거절·수정 요청을 기다리고 있습니다."
      : "진단을 계속하려면 요청한 현장 정보를 입력해야 합니다.";
  } else if (state.workflowStatus === "COMPLETED") {
    phase = "completed";
    workflowTitle = "진단 워크플로 완료";
    workflowDescription = "분석과 보고서 생성 절차가 끝났습니다. 실제 설비 정비가 완료되었다는 뜻은 아닙니다.";
  } else if (state.workflowStatus === "FAILED") {
    phase = "failed";
    workflowTitle = "진단 워크플로 실패";
    workflowDescription = "진단 실행이 실패했습니다. 오류 내용을 확인하고 필요하면 새 진단을 시작하세요.";
  }

  const actions = state.report?.recommended_actions ?? state.run?.recommended_actions ?? [];
  const recommendation = phase === "completed" && actions.length
    ? actions[0].summary
    : null;
  const diagnosisCandidates = state.run?.diagnosis_candidates ?? state.report?.diagnosis_candidates ?? [];
  const diagnosisSummary = phase === "completed" && diagnosisCandidates.length
    ? diagnosisCandidates[0].summary
    : null;

  return {
    phase,
    workflowTitle,
    workflowDescription,
    prediction,
    predictionTitle,
    predictionDescription,
    recommendation,
    diagnosisSummary,
    reportAvailable: Boolean(state.report || state.reportReady || state.run?.final_report_available),
    evidenceAvailable: state.evidenceCount > 0,
    inspectionAvailable: Boolean(state.run?.inspection_plan.length || state.report?.inspection_plan.length),
    actionAvailable: actions.length > 0,
  };
}
