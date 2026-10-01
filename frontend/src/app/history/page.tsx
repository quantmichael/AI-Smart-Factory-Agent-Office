"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { measurementDisplayName, WORKFLOW_LABEL } from "@/features/agent-run/event-mapper";
import type { AgentRunList, AgentRunSummary } from "@/features/agent-run/types";
import { fetchAgentRuns } from "@/lib/api";

const PAGE_SIZE = 20;
const PREDICTION_LABEL: Record<string, string> = { normal: "정상", abnormal: "손상 의심", healthy: "정상", damaged: "손상 의심" };

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function confidence(value?: number | null) {
  return value == null ? "—" : `${(value * 100).toFixed(1)}%`;
}

function RunCard({ run }: { run: AgentRunSummary }) {
  const prediction = run.ml_prediction ? (PREDICTION_LABEL[run.ml_prediction] ?? run.ml_prediction) : "분석 결과 없음";
  return (
    <Link className="history-mobile-card surface" href={`/history/${encodeURIComponent(run.run_id)}`}>
      <div className="history-card-heading"><time>{formatDate(run.created_at)}</time><span className={`history-status status-${run.workflow_status.toLowerCase()}`}>{WORKFLOW_LABEL[run.workflow_status] ?? run.workflow_status}</span></div>
      <h2>{measurementDisplayName(run.measurement_id, run.demo_scenario)}</h2>
      <dl><div><dt>설비</dt><dd>{run.equipment_id}</dd></div><div><dt>AI 판정</dt><dd className={`prediction-${run.ml_prediction ?? "none"}`}>{prediction} · {confidence(run.ml_confidence)}</dd></div><div><dt>근거</dt><dd>{run.evidence_count}건</dd></div><div><dt>보고서</dt><dd>{run.final_report_available ? "완료" : "없음"}</dd></div></dl>
      <small>상세 결과 보기 →</small>
    </Link>
  );
}

export default function HistoryPage() {
  const [data, setData] = useState<AgentRunList>();
  const [page, setPage] = useState(1);
  const [measurement, setMeasurement] = useState("");
  const [submittedMeasurement, setSubmittedMeasurement] = useState("");
  const [prediction, setPrediction] = useState("");
  const [workflowStatus, setWorkflowStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  const load = useCallback(async () => {
    setLoading(true); setError(undefined);
    try {
      setData(await fetchAgentRuns({ page, pageSize: PAGE_SIZE, measurementId: submittedMeasurement, mlPrediction: prediction, workflowStatus }));
    } catch (nextError: unknown) {
      setError(nextError instanceof Error ? nextError.message : "진단 이력을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, [page, prediction, submittedMeasurement, workflowStatus]);

  useEffect(() => { void load(); }, [load]);
  const search = (event: FormEvent) => { event.preventDefault(); setPage(1); setSubmittedMeasurement(measurement.trim()); };

  return (
    <main className="app-shell history-shell">
      <AppHeader active="history" status={<div className="system-health"><span className="connection-dot online" /><div><strong>읽기 전용 조회</strong><small>HISTORICAL RUNS</small></div></div>} />
      <section className="history-hero"><div><span className="kicker">진단 기록 · DIAGNOSIS ARCHIVE</span><h1>진단 이력</h1><p>과거에 수행한 AI 진단 결과를 조회하고 상세 결과를 확인합니다.</p></div>{data && <div className="history-total"><span>저장된 진단</span><strong>{data.total}</strong><small>현재 검색 조건 기준</small></div>}</section>

      <form className="history-filters surface" onSubmit={search}>
        <label><span>Measurement 검색</span><input value={measurement} onChange={(event) => setMeasurement(event.target.value)} placeholder="측정 데이터명 또는 ID" /></label>
        <label><span>AI 판정</span><select value={prediction} onChange={(event) => { setPrediction(event.target.value); setPage(1); }}><option value="">전체</option><option value="normal">정상</option><option value="abnormal">손상</option></select></label>
        <label><span>진단 상태</span><select value={workflowStatus} onChange={(event) => { setWorkflowStatus(event.target.value); setPage(1); }}><option value="">전체</option><option value="CREATED">생성됨</option><option value="RUNNING">실행 중</option><option value="WAITING">작업자 확인 대기</option><option value="COMPLETED">완료</option><option value="FAILED">실패</option></select></label>
        <button type="submit">검색</button>
      </form>

      {loading && <section className="history-feedback surface" aria-live="polite">진단 이력을 불러오는 중…</section>}
      {!loading && error && <section className="history-feedback history-error surface" role="alert"><strong>진단 이력을 불러오지 못했습니다.</strong><p>{error}</p><button onClick={() => void load()} type="button">다시 시도</button></section>}
      {!loading && !error && data?.items.length === 0 && <section className="history-feedback surface">저장된 진단 이력이 없습니다.</section>}

      {!loading && !error && Boolean(data?.items.length) && <>
        <section className="history-table-wrap surface"><table className="history-table"><thead><tr><th>진단 일시</th><th>측정 데이터</th><th>설비</th><th>AI 판정</th><th>진단 상태</th><th>근거 수</th><th>보고서</th><th /></tr></thead><tbody>{data!.items.map((run) => <tr key={run.run_id}><td>{formatDate(run.created_at)}</td><td><strong>{measurementDisplayName(run.measurement_id, run.demo_scenario)}</strong><small>{run.measurement_id}</small></td><td>{run.equipment_id}</td><td><span className={`prediction-${run.ml_prediction ?? "none"}`}>{run.ml_prediction ? (PREDICTION_LABEL[run.ml_prediction] ?? run.ml_prediction) : "—"}</span><small>{confidence(run.ml_confidence)}</small></td><td><span className={`history-status status-${run.workflow_status.toLowerCase()}`}>{WORKFLOW_LABEL[run.workflow_status] ?? run.workflow_status}</span></td><td>{run.evidence_count}건</td><td>{run.final_report_available ? "완료" : "없음"}</td><td><Link href={`/history/${encodeURIComponent(run.run_id)}`}>상세 보기</Link></td></tr>)}</tbody></table></section>
        <div className="history-mobile-list">{data!.items.map((run) => <RunCard run={run} key={run.run_id} />)}</div>
        <nav className="history-pagination" aria-label="진단 이력 페이지"><button disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>이전</button><span>{page} / {Math.max(1, data!.total_pages)}</span><button disabled={page >= data!.total_pages} onClick={() => setPage((value) => value + 1)}>다음</button></nav>
      </>}
    </main>
  );
}
