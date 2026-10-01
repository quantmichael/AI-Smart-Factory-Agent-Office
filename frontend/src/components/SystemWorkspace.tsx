"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import type {
  SystemComponent,
  SystemComponentGroup,
  SystemComponentStatus,
  SystemStatusView,
} from "@/lib/api";
import { fetchSystemStatus } from "@/lib/api";

const STATUS_LABEL: Record<SystemComponentStatus, string> = {
  READY: "준비됨",
  DEGRADED: "확인 필요",
  UNAVAILABLE: "사용 불가",
  UNKNOWN: "확인되지 않음",
};
const OVERALL_LABEL: Record<SystemComponentStatus, string> = {
  READY: "정상",
  DEGRADED: "일부 기능 확인 필요",
  UNAVAILABLE: "핵심 기능 사용 불가",
  UNKNOWN: "상태 확인 필요",
};
const GROUPS: Array<{ id: SystemComponentGroup; kicker: string; title: string; description: string }> = [
  { id: "CORE_AI", kicker: "CORE AI", title: "핵심 진단 구성", description: "API, AI 모델, 진단 데이터의 실제 접근 상태" },
  { id: "KNOWLEDGE_AGENT", kicker: "KNOWLEDGE / AGENT", title: "기술지식과 Agent", description: "RAG 저장소와 Workflow 구성 상태" },
  { id: "DATA_STATE", kicker: "DATA / STATE", title: "실행 데이터와 상태", description: "진단 이력, Memory, Multimodal metadata 저장소" },
  { id: "VERSION_RUNTIME", kicker: "VERSION / RUNTIME", title: "버전 정보", description: "외부에 공개 가능한 현재 구성 식별자" },
];
const ICONS: Record<string, string> = {
  backend_api: "↔",
  ml_model: "◆",
  dataset: "▥",
  knowledge_base: "▤",
  vector_db: "◈",
  langgraph: "⌁",
  checkpoint_store: "◇",
  run_database: "▦",
  long_term_memory: "◎",
  multimodal: "◉",
  runtime_versions: "#",
};

function formatCheckedAt(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  }).format(new Date(value));
}

function StatusBadge({ status }: { status: SystemComponentStatus }) {
  return <span className={`system-status-badge status-${status.toLowerCase()}`}><i aria-hidden="true" />{STATUS_LABEL[status]}<small>{status}</small></span>;
}

function ComponentCard({ component }: { component: SystemComponent }) {
  return <article className={`system-component-card status-border-${component.status.toLowerCase()}`}>
    <header>
      <span className="system-component-icon" aria-hidden="true">{ICONS[component.component_id] ?? "·"}</span>
      <StatusBadge status={component.status} />
    </header>
    <div className="system-component-title"><h3>{component.name}</h3><strong>{component.summary}</strong></div>
    {component.details.length > 0 && <dl>{component.details.map((detail) => <div key={`${component.component_id}-${detail.label}`}><dt>{detail.label}</dt><dd>{detail.value}</dd></div>)}</dl>}
    <p className="system-verification"><span>확인 수준</span>{component.verification}</p>
  </article>;
}

export function SystemWorkspace() {
  const [data, setData] = useState<SystemStatusView>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const load = useCallback(async () => {
    setLoading(true);
    setError(undefined);
    try { setData(await fetchSystemStatus()); }
    catch (nextError: unknown) {
      setError(nextError instanceof Error ? nextError.message : "시스템 상태를 불러오지 못했습니다.");
    } finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const grouped = useMemo(() => {
    const result = new Map<SystemComponentGroup, SystemComponent[]>();
    for (const component of data?.components ?? []) {
      result.set(component.group, [...(result.get(component.group) ?? []), component]);
    }
    return result;
  }, [data]);

  const headerStatus = error ? "UNAVAILABLE" : data?.overall_status ?? "UNKNOWN";
  return <main className="app-shell system-shell">
    <AppHeader active="system" status={<div className="system-health"><span className={`connection-dot ${data && !error ? "online" : "offline"}`} /><div><strong>{error ? "Backend 연결 실패" : "시스템 상태"}</strong><small>{error ? "STATUS API UNAVAILABLE" : "READ-ONLY MONITOR"}</small></div></div>} />

    <section className="system-hero">
      <div><span className="kicker">SYSTEM OBSERVABILITY · 읽기 전용</span><h1>시스템</h1><p>AI 설비 진단을 구성하는 서비스와 저장소의 실제 확인 상태를 보여줍니다.</p></div>
      <div className={`system-overall status-border-${headerStatus.toLowerCase()}`}>
        <span>전체 시스템 상태</span>
        <strong>{error ? "Backend 연결 실패" : OVERALL_LABEL[headerStatus]}</strong>
        <small>{data ? `마지막 확인 ${formatCheckedAt(data.checked_at)}` : "상태 확인 대기"}</small>
        <button type="button" onClick={() => void load()} disabled={loading}>{loading ? "확인 중…" : "상태 새로고침"}</button>
      </div>
    </section>

    {loading && !data && <section className="system-feedback surface" aria-live="polite">각 구성요소의 상태를 읽기 전용으로 확인하는 중…</section>}
    {!loading && error && <section className="system-feedback system-error surface" role="alert"><strong>Backend 연결 실패</strong><p>{error}</p><button type="button" onClick={() => void load()}>연결 다시 시도</button></section>}

    {data && <>
      <section className="system-connection surface" aria-label="Frontend와 Backend 연결 상태">
        <div><span className="connection-dot online" /><div><small>FRONTEND ↔ BACKEND</small><strong>API 연결 정상</strong></div></div>
        <p>System Status API의 현재 응답을 기준으로 표시합니다.</p>
        <time dateTime={data.checked_at}>{formatCheckedAt(data.checked_at)}</time>
      </section>

      {GROUPS.map((group) => {
        const components = grouped.get(group.id) ?? [];
        if (!components.length) return null;
        return <section className="system-group" key={group.id} aria-labelledby={`system-group-${group.id}`}>
          <header className="system-group-heading"><div><span className="kicker">{group.kicker}</span><h2 id={`system-group-${group.id}`}>{group.title}</h2></div><p>{group.description}</p></header>
          <div className={`system-component-grid group-${group.id.toLowerCase()}`}>{components.map((component) => <ComponentCard component={component} key={component.component_id} />)}</div>
        </section>;
      })}

      <section className="system-scope-note surface"><span className="kicker">STATUS SCOPE</span><h2>상태 표시 기준</h2><p>파일 존재, DB 접근, Collection 조회, 모델 로드, Workflow 실행은 서로 다른 확인 수준입니다. 각 카드의 <strong>확인 수준</strong>은 이번 조회에서 실제로 검증한 범위만 설명하며 E2E 진단 성공을 의미하지 않습니다.</p></section>
    </>}
  </main>;
}
