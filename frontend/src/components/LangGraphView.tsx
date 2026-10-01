import { GRAPH_NODES, GRAPH_STATE_LABEL } from "@/features/agent-run/event-mapper";
import type { AgentRunUIState } from "@/features/agent-run/types";

const LABELS: Record<string, string> = {
  load_sensor_data: "센서 데이터 로드",
  load_equipment_memory: "설비 이력 로드",
  run_detection: "ML 이상탐지",
  check_abnormal: "정상·이상 분기",
  check_inspection_image: "점검 이미지 확인",
  analyze_inspection_image: "시각 관찰 분석",
  build_rag_query: "검색 질의 생성",
  retrieve_knowledge: "기술 근거 검색",
  diagnose: "근거기반 진단",
  verify_evidence: "근거 충족 검증",
  build_inspection_plan: "점검 계획 수립",
  recommend_action: "조치 권고",
  generate_report: "최종 보고서",
};

export function LangGraphView({ state }: { state: AgentRunUIState }) {
  return (
    <section className="graph-card surface" aria-labelledby="graph-title">
      <div className="section-heading compact">
        <div><span className="kicker">실시간 실행 흐름 · LangGraph</span><h2 id="graph-title">에이전트 워크플로</h2></div>
        {state.selectedEdge && <span className={`edge-badge edge-${state.selectedEdge.toLowerCase()}`}>{state.selectedEdge === "NORMAL" ? "정상 경로" : state.selectedEdge === "ABNORMAL" ? "이상 경로" : "근거 검증 결과"}</span>}
      </div>
      <div className="graph-flow">
        {GRAPH_NODES.map((node, index) => (
          <div className="graph-step-wrap" key={node}>
            <div className={`graph-node graph-${(state.graphNodeStates[node] ?? "PENDING").toLowerCase()}`} title={node}>
              <span>{String(index + 1).padStart(2, "0")}</span><strong>{LABELS[node]}</strong><small>{GRAPH_STATE_LABEL[state.graphNodeStates[node] ?? "PENDING"]}</small>
            </div>
            {index < GRAPH_NODES.length - 1 && <div className="graph-edge" aria-hidden="true"><i /></div>}
          </div>
        ))}
      </div>
    </section>
  );
}
