import { AGENT_STATE_LABEL, NODE_ACTIVITY, ROLE_LABEL } from "@/features/agent-run/event-mapper";
import type { AgentRole, AgentRunUIState } from "@/features/agent-run/types";

const ZONES: Array<{ role: AgentRole; title: string; subtitle: string; icon: string; iconLabel: string }> = [
  { role: "SENSOR_AGENT", title: "설비·센서 구역", subtitle: "측정 데이터 입력", icon: "⌁", iconLabel: "센서 파형" },
  { role: "DETECTION_AGENT", title: "이상탐지 연구실", subtitle: "ML 상태 분석", icon: "△", iconLabel: "탐지 경고" },
  { role: "RAG_AGENT", title: "기술지식 라이브러리", subtitle: "기술 근거 검색", icon: "▤", iconLabel: "기술 문서" },
  { role: "DIAGNOSIS_AGENT", title: "근거기반 진단실", subtitle: "근거 기반 판단", icon: "⌕", iconLabel: "진단 분석" },
  { role: "MAINTENANCE_AGENT", title: "점검·정비 지원실", subtitle: "점검 및 조치 지원", icon: "⚒", iconLabel: "정비 공구" },
];

const STATE_ICON: Record<string, string> = {
  IDLE: "○",
  WORKING: "◌",
  WAITING: "…",
  RETRYING: "↻",
  NEEDS_HUMAN: "♙",
  DONE: "✓",
  ERROR: "!",
};

export function AgentOffice({ state }: { state: AgentRunUIState }) {
  return (
    <section className="office-card surface" aria-labelledby="office-title">
      <div className="section-heading">
        <div><span className="kicker">실시간 에이전트 협업 공간</span><h2 id="office-title">AI 에이전트 오피스</h2></div>
        <div className="office-legend"><span className="pulse-dot" /> 백엔드 이벤트 연동</div>
      </div>
      <div className="office-grid">
        {ZONES.map((zone, index) => {
          const agentState = state.agentStates[zone.role];
          const active = state.activeAgent === zone.role && ["WORKING", "RETRYING"].includes(agentState);
          const humanAttention = state.activeAgent === zone.role && agentState === "NEEDS_HUMAN";
          return (
            <article className={`office-zone zone-${index + 1} agent-${agentState.toLowerCase()} role-${zone.role.toLowerCase()} ${active ? "is-active" : ""} ${humanAttention ? "needs-attention" : ""}`} key={zone.role}>
              <div className="zone-top"><span className="zone-icon" title={zone.iconLabel} aria-label={zone.iconLabel}>{zone.icon}</span><span className="state-pill"><i aria-hidden="true">{STATE_ICON[agentState] ?? "•"}</i>{AGENT_STATE_LABEL[agentState] ?? agentState}</span></div>
              <div className="agent-figure" aria-hidden="true"><span className="agent-head" /><span className="agent-body" /><span className="agent-screen" /><span className="agent-prop" /></div>
              <div className="zone-copy"><strong>{zone.title}</strong><small>{zone.subtitle}</small></div>
              <div className="agent-label">{ROLE_LABEL[zone.role]}</div>
              {active && <div className="activity-bubble">{NODE_ACTIVITY[state.currentNode ?? ""] ?? "실시간 진단 작업을 수행하는 중…"}</div>}
            </article>
          );
        })}
      </div>
      <div className="office-floor"><span>현장 센서 · EDGE</span><i /><span>AI 진단 코어 · CORE</span><i /><span>작업자 검토 · HITL</span></div>
    </section>
  );
}
