import { useMemo, useState } from "react";

import type { AgentEvent } from "@/features/agent-run/types";
import { EVENT_LABEL, ROLE_LABEL, NODE_ACTIVITY } from "@/features/agent-run/event-mapper";

const FILTERS = ["ALL", "SENSOR_AGENT", "DETECTION_AGENT", "RAG_AGENT", "DIAGNOSIS_AGENT", "MAINTENANCE_AGENT", "SYSTEM"];
const FILTER_LABEL: Record<string, string> = { ALL: "전체", SENSOR_AGENT: "센서", DETECTION_AGENT: "탐지", RAG_AGENT: "기술지식", DIAGNOSIS_AGENT: "진단", MAINTENANCE_AGENT: "정비", SYSTEM: "시스템" };
const NODE_LABEL: Record<string, string> = {
  load_sensor_data: "측정 데이터 확인", load_equipment_memory: "과거 설비 이력 확인", run_detection: "이상 여부 분석", check_abnormal: "정상·이상 경로 판정",
  retrieve_knowledge: "기술 근거 검색", diagnose: "진단 결과 분석", verify_evidence: "근거 충분성 확인", build_inspection_plan: "점검 계획 수립",
  recommend_action: "권고 조치 생성", generate_report: "최종 보고서 작성", generate_normal_report: "정상 보고서 작성",
};

export function EventTimeline({ events }: { events: AgentEvent[] }) {
  const [filter, setFilter] = useState("ALL");
  const [expanded, setExpanded] = useState(false);
  const shown = useMemo(
    () => events.filter((event) => filter === "ALL" || event.agent_role === filter).reverse(),
    [events, filter],
  );
  const visible = expanded ? shown : shown.slice(0, 6);
  const origin = events[0] ? new Date(events[0].created_at).getTime() : 0;
  return (
    <section className="timeline-card surface" aria-labelledby="timeline-title">
      <div className="section-heading compact">
        <div><span className="kicker">실행 기록 추적</span><h2 id="timeline-title">이벤트 타임라인</h2></div>
        <span className="count-badge">이벤트 {events.length}건</span>
      </div>
      <div className="filter-row" aria-label="Timeline role filter">
        {FILTERS.map((item) => <button className={filter === item ? "active" : ""} onClick={() => { setFilter(item); setExpanded(false); }} key={item}>{FILTER_LABEL[item]}</button>)}
      </div>
      <div className="timeline-list" id="event-timeline-list">
        {!shown.length && <div className="empty-copy">백엔드 이벤트가 발생 순서대로 표시됩니다.</div>}
        {visible.map((event) => {
          const elapsed = origin ? Math.max(0, new Date(event.created_at).getTime() - origin) / 1000 : 0;
          return (
            <article className="timeline-event" key={event.event_id}>
              <time>+{elapsed.toFixed(2)}s</time><span className={`event-mark role-${event.agent_role.toLowerCase()}`} />
              <div><strong>{EVENT_LABEL[event.event_type] ?? "진단 처리"}</strong><small>{ROLE_LABEL[event.agent_role as keyof typeof ROLE_LABEL] ?? "시스템"} · {NODE_LABEL[event.node] ?? NODE_ACTIVITY[event.node] ?? "진단 단계 처리"}</small><details className="technical-details timeline-details"><summary>상세 기술정보</summary><div>순서 {event.sequence} · 이벤트 {event.event_type} · 노드 {event.node}</div></details></div>
            </article>
          );
        })}
      </div>
      {shown.length > 6 && <div className="timeline-more-row"><button className="timeline-more" type="button" aria-expanded={expanded} aria-controls="event-timeline-list" onClick={() => setExpanded((value) => !value)}>{expanded ? "접기" : `더 보기 (${shown.length - 6}개)`}</button></div>}
    </section>
  );
}
