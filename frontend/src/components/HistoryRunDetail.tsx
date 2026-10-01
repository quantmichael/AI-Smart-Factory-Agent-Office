"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { DetailTabs } from "@/components/DetailTabs";
import { EventTimeline } from "@/components/EventTimeline";
import { measurementDisplayName, WORKFLOW_LABEL } from "@/features/agent-run/event-mapper";
import { agentRunReducer, initialAgentRunState } from "@/features/agent-run/reducer";
import type { AgentRunUIState, HumanInteraction, MemoryHistory } from "@/features/agent-run/types";
import { ApiClientError, fetchAgentEvents, fetchAgentEvidence, fetchAgentReport, fetchAgentRun, fetchEquipmentHistory } from "@/lib/api";

const PREDICTION_LABEL: Record<string, string> = { normal: "정상", abnormal: "손상 의심", healthy: "정상", damaged: "손상 의심" };

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", { dateStyle: "long", timeStyle: "medium" }).format(new Date(value));
}

function interactionDecision(interaction: HumanInteraction) {
  const decision = interaction.response.decision;
  if (typeof decision !== "string") return "응답 기록됨";
  return { APPROVED: "승인", REJECTED: "거절", NEEDS_REVISION: "수정 요청" }[decision] ?? decision;
}

export function HistoryRunDetail({ runId }: { runId: string }) {
  const [state, setState] = useState<AgentRunUIState>();
  const [history, setHistory] = useState<MemoryHistory>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  const load = useCallback(async () => {
    setLoading(true); setError(undefined);
    try {
      const [run, events] = await Promise.all([fetchAgentRun(runId), fetchAgentEvents(runId)]);
      let historical = agentRunReducer(initialAgentRunState, { type: "HYDRATE", run, events });
      const [evidence, report, equipmentHistory] = await Promise.all([
        run.evidence_count ? fetchAgentEvidence(runId) : Promise.resolve([]),
        run.final_report_available ? fetchAgentReport(runId) : Promise.resolve(undefined),
        fetchEquipmentHistory(run.equipment_id).catch(() => undefined),
      ]);
      historical = agentRunReducer(historical, { type: "EVIDENCE", evidence });
      if (report) historical = agentRunReducer(historical, { type: "REPORT", report });
      historical = { ...historical, connectionStatus: "closed" };
      setState(historical); setHistory(equipmentHistory);
    } catch (nextError: unknown) {
      setError(nextError instanceof ApiClientError && nextError.status === 404
        ? "요청한 진단 이력을 찾을 수 없습니다."
        : nextError instanceof Error ? nextError.message : "진단 상세를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => { void load(); }, [load]);

  return (
    <main className="app-shell history-shell">
      <AppHeader active="history" status={<div className="system-health"><span className="connection-dot online" /><div><strong>저장 기록 조회</strong><small>NO LIVE SSE</small></div></div>} />
      <section className="history-detail-heading"><div><Link href="/history">← 진단 이력</Link><h1>진단 상세</h1><p>저장된 Run 결과를 읽기 전용으로 확인합니다.</p></div></section>
      {loading && <section className="history-feedback surface">진단 상세를 불러오는 중…</section>}
      {!loading && error && <section className="history-feedback history-error surface" role="alert"><strong>진단 상세를 불러오지 못했습니다.</strong><p>{error}</p><button type="button" onClick={() => void load()}>다시 시도</button></section>}
      {!loading && !error && state?.run && <>
        <section className="history-overview surface"><div><span>진단 일시</span><strong>{formatDate(state.run.created_at)}</strong></div><div><span>측정 데이터</span><strong>{measurementDisplayName(state.run.measurement_id, state.run.demo_scenario)}</strong><small>{state.run.measurement_id}</small></div><div><span>설비</span><strong>{state.run.equipment_id}</strong></div><div><span>AI 판정</span><strong>{state.run.analysis_result ? (PREDICTION_LABEL[state.run.analysis_result.status] ?? state.run.analysis_result.status) : "분석 결과 없음"}</strong><small>{state.run.analysis_result?.confidence == null ? "출력값 없음" : `모델 출력 신뢰도 ${(state.run.analysis_result.confidence * 100).toFixed(1)}%`}</small></div><div><span>진단 상태</span><strong>{WORKFLOW_LABEL[state.run.workflow_status] ?? state.run.workflow_status}</strong></div></section>
        <section className="history-detail-grid"><div className="history-detail-main"><DetailTabs state={state} history={history} /><section className="hitl-history surface"><div className="section-heading compact"><div><span className="kicker">작업자 판단 · HITL</span><h2>작업자 확인 기록</h2></div></div>{state.run.pending_human_request && <article className="hitl-pending"><div><span>{state.run.pending_human_request.request_type}</span><strong>작업자 확인 대기</strong></div><p>{state.run.pending_human_request.question}</p><small>생성된 요청이 아직 처리되지 않았습니다.</small></article>}{state.report?.human_interactions.length ? state.report.human_interactions.map((item) => <article key={item.request_id}><div><span>{item.request_type}</span><strong>{interactionDecision(item)}</strong></div><p>{item.comment || "별도 의견 없음"}</p><small>{item.actor || "작업자"} · {formatDate(item.recorded_at)} · 처리 완료</small><details className="technical-details"><summary>응답 상세</summary><div>{JSON.stringify(item.response, null, 2)}</div></details></article>) : !state.run.pending_human_request && <div className="empty-copy">작업자 확인 과정 없음</div>}</section></div><EventTimeline events={state.timeline} /></section>
        <details className="technical-details history-run-id"><summary>실행 식별정보</summary><div>Run ID: {state.run.run_id}</div></details>
      </>}
    </main>
  );
}
