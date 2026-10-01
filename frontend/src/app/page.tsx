"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AgentOffice } from "@/components/AgentOffice";
import { AppHeader } from "@/components/AppHeader";
import { DetailTabs } from "@/components/DetailTabs";
import { EventTimeline } from "@/components/EventTimeline";
import { HumanInputModal } from "@/components/HumanInputModal";
import { InspectionImageInput } from "@/components/InspectionImageInput";
import { LangGraphView } from "@/components/LangGraphView";
import { Waveform } from "@/components/Waveform";
import { CONNECTION_LABEL, currentTaskDisplay, EVIDENCE_STATUS_LABEL, executionStatusDisplay, measurementReplayState, ROLE_LABEL, WORKFLOW_LABEL, measurementDisplayName } from "@/features/agent-run/event-mapper";
import { useAgentRun } from "@/features/agent-run/hooks/use-agent-run";
import type { MeasurementPreview, MemoryHistory } from "@/features/agent-run/types";
import { fetchEquipmentHistory, fetchHealth, fetchMeasurementPreview } from "@/lib/api";

const SAMPLES = [
  { id: "paderborn:K001:N09_M07_F10:01", label: "측정 데이터 A" },
  { id: "paderborn:KA01:N09_M07_F10:01", label: "측정 데이터 B" },
  { id: "paderborn:KA01:N09_M07_F10:02", label: "측정 데이터 C · HITL 시연", demoScenario: "HITL_CONTROLLED" as const },
];
const EQUIPMENT_ID = "paderborn-bearing-test-rig";
const HEALTH_CHECK_TIMEOUT_MS = 4000;
const HEALTH_CHECK_INTERVAL_MS = 30000;
const HEALTH_RETRY_INTERVAL_MS = 4000;

function shortId(value?: string) {
  if (!value) return "—";
  return value.length > 26 ? `${value.slice(0, 13)}…${value.slice(-8)}` : value;
}

function formatFeature(key: string) {
  const labels: Record<string, string> = { rms: "실효값 · RMS", kurtosis: "첨도 · Kurtosis", peak: "최댓값 · Peak", peak_to_peak: "첨두간값 · Peak-to-Peak", crest_factor: "파고율 · Crest Factor", dominant_frequency: "주요 주파수 · Dominant Frequency" };
  if (labels[key]) return labels[key];
  return key.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function signalValueAtProgress(points: Array<{ time: number; value: number }> | undefined, progress: number) {
  if (!points?.length) return undefined;
  const targetTime = points[0].time + (points.at(-1)!.time - points[0].time) * Math.min(1, Math.max(0, progress));
  let low = 0;
  let high = points.length - 1;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (points[middle].time < targetTime) low = middle + 1;
    else high = middle;
  }
  if (low === 0) return points[0].value;
  const before = points[low - 1];
  const after = points[low];
  const span = after.time - before.time;
  if (span <= 0) return after.value;
  const ratio = (targetTime - before.time) / span;
  return before.value + (after.value - before.value) * ratio;
}

export default function HomePage() {
  const { state, loadingPhase, startRun, submitHuman, uploadHumanInspectionImage, clearRun, retryConnection } = useAgentRun();
  const [measurementId, setMeasurementId] = useState("");
  const [preview, setPreview] = useState<MeasurementPreview>();
  const [replayProgress, setReplayProgress] = useState(1);
  const [previewError, setPreviewError] = useState<string>();
  const [backendOnline, setBackendOnline] = useState<boolean>();
  const [healthCheckKey, setHealthCheckKey] = useState(0);
  const [history, setHistory] = useState<MemoryHistory>();
  const [inspectionImage, setInspectionImage] = useState<File>();
  const [, setClock] = useState(0);
  const synchronizedRunRef = useRef<string | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;
    let nextCheck: number | undefined;
    let activeController: AbortController | undefined;

    const checkHealth = async () => {
      activeController?.abort();
      const controller = new AbortController();
      activeController = controller;
      const timeout = window.setTimeout(() => controller.abort(), HEALTH_CHECK_TIMEOUT_MS);
      let delay = HEALTH_RETRY_INTERVAL_MS;
      try {
        await fetchHealth(controller.signal);
        if (!cancelled) setBackendOnline(true);
        delay = HEALTH_CHECK_INTERVAL_MS;
      } catch {
        if (!cancelled) setBackendOnline(false);
      } finally {
        window.clearTimeout(timeout);
        if (!cancelled) nextCheck = window.setTimeout(checkHealth, delay);
      }
    };

    void checkHealth();
    return () => {
      cancelled = true;
      activeController?.abort();
      if (nextCheck) window.clearTimeout(nextCheck);
    };
  }, [healthCheckKey]);
  useEffect(() => {
    if (state.runId && state.run?.measurement_id && synchronizedRunRef.current !== state.runId) {
      synchronizedRunRef.current = state.runId;
      setMeasurementId(state.run.measurement_id);
    }
  }, [state.run?.measurement_id, state.runId]);
  useEffect(() => {
    let cancelled = false;
    setPreview(undefined); setPreviewError(undefined);
    if (!measurementId) return;
    fetchMeasurementPreview(measurementId)
      .then((nextPreview) => { if (!cancelled) setPreview(nextPreview); })
      .catch((error: unknown) => { if (!cancelled) setPreviewError(error instanceof Error ? error.message : "파형 미리보기를 불러올 수 없습니다."); });
    return () => { cancelled = true; };
  }, [measurementId]);
  useEffect(() => {
    const equipmentId = state.run?.equipment_id ?? preview?.equipment_id;
    if (!equipmentId) return;
    fetchEquipmentHistory(equipmentId).then(setHistory).catch(() => undefined);
  }, [preview?.equipment_id, state.run?.equipment_id, state.run?.updated_at]);
  useEffect(() => {
    if (!state.startedAt || ["COMPLETED", "FAILED", "IDLE"].includes(state.workflowStatus)) return;
    const timer = window.setInterval(() => setClock((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [state.startedAt, state.workflowStatus]);

  const features = Object.entries(state.analysisSummary?.signal_features ?? {});
  const activeAction = state.run?.recommended_actions.find((item) => item.action_id === state.pendingHumanRequest?.action_id);
  const selectedSample = SAMPLES.find((sample) => sample.id === measurementId);
  const condition = preview?.operating_condition ?? {};
  const replayState = measurementReplayState(Boolean(measurementId && preview), state.workflowStatus, Boolean(loadingPhase?.startsWith("AI 에이전트를 시작")));
  const replaying = replayState === "REPLAYING";
  const reportReplayProgress = useCallback((progress: number) => setReplayProgress(progress), []);
  const measuredSpeed = signalValueAtProgress(preview?.operating_signals.speed, replayProgress);
  const measuredTorque = signalValueAtProgress(preview?.operating_signals.torque, replayProgress);
  const measuredForce = signalValueAtProgress(preview?.operating_signals.force, replayProgress);
  const equipmentBadgeLabel = replayState === "NO_DATA"
    ? (previewError ? "측정 데이터 오류" : measurementId ? "측정 데이터 로드 중" : "데이터 선택 대기")
    : replayState === "REPLAYING" ? "센서 데이터 Replay"
      : replayState === "DIAGNOSING" ? (state.workflowStatus === "WAITING" ? "작업자 확인 대기" : "AI 진단 실행 중")
        : replayState === "COMPLETED" ? "진단 완료" : "진단 실패";
  const activeLabel = state.activeAgent && state.activeAgent in ROLE_LABEL ? ROLE_LABEL[state.activeAgent as keyof typeof ROLE_LABEL] : "시스템";
  const statusTone = state.workflowStatus === "FAILED" ? "danger" : state.workflowStatus === "WAITING" ? "amber" : state.workflowStatus === "COMPLETED" ? "success" : "cyan";
  const operationLabel = currentTaskDisplay(state.workflowStatus, state.currentNode, Boolean(state.runId));
  const elapsedEnd = ["COMPLETED", "FAILED"].includes(state.workflowStatus) ? state.run?.updated_at : undefined;
  const elapsed = state.startedAt
    ? Math.max(0, ((elapsedEnd ? new Date(elapsedEnd).getTime() : Date.now()) - new Date(state.startedAt).getTime()) / 1000)
    : 0;
  const featureCards = useMemo(() => features.slice(0, 4), [features]);

  return (
    <main className="app-shell">
      <AppHeader active="dashboard" status={<div className="system-health"><span className={`connection-dot ${backendOnline === true ? "online" : backendOnline === false ? "offline" : ""}`} /><div><strong>{backendOnline === undefined ? "서버 준비 중" : backendOnline ? "시스템 정상" : "백엔드 연결 실패"}</strong><small>{CONNECTION_LABEL[state.connectionStatus] ?? state.connectionStatus}</small></div>{backendOnline === false && <button className="health-retry" type="button" onClick={() => { setBackendOnline(undefined); setHealthCheckKey((value) => value + 1); }}>연결 다시 시도</button>}</div>} />

      <section className="command-header">
        <div><h1 className="command-title">AI 기반 설비 상태진단</h1><p>저장된 Paderborn 측정 데이터를 센서 입력처럼 사용해 ML 판정과 이상 시 근거 기반 진단을 수행합니다.</p></div>
        <div className="run-controls">
          <label><span>데모 센서 입력</span><select value={measurementId} onChange={(event) => { const nextMeasurementId = event.target.value; if (nextMeasurementId !== measurementId) { clearRun(); setPreview(undefined); setPreviewError(undefined); setMeasurementId(nextMeasurementId); } }} disabled={Boolean(loadingPhase) || state.workflowStatus === "RUNNING" || state.workflowStatus === "WAITING"}><option value="">측정 데이터 선택</option>{SAMPLES.map((sample) => <option value={sample.id} key={sample.id}>{sample.label}</option>)}</select><small className="dataset-hint">선택하면 저장된 센서 데이터를 재생합니다. AI 진단은 버튼을 눌러 시작합니다.</small></label>
          <button className="start-button" disabled={backendOnline !== true || !measurementId || !preview || Boolean(loadingPhase) || state.workflowStatus === "RUNNING" || state.workflowStatus === "WAITING"} onClick={() => startRun(EQUIPMENT_ID, measurementId, inspectionImage, selectedSample?.demoScenario)}><span>{loadingPhase ? "◌" : "▶"}</span>{loadingPhase ?? (state.runId ? "새 진단 시작" : "AI 진단 시작")}</button>
          {state.runId && <button className="icon-button" onClick={clearRun} aria-label="현재 진단 결과 지우기">×</button>}
        </div>
      </section>

      {selectedSample?.demoScenario === "HITL_CONTROLLED" && <div className="controlled-demo-banner" role="note"><strong>HITL 시연 조건</strong><span>실제 KA01 측정 데이터와 ML·RAG를 사용하며, 조치 검토 단계에서 작업자 승인 흐름을 확인하기 위한 통제 조건만 적용합니다. 설비 명령은 실행하지 않습니다.</span></div>}

      {state.error && <div className="error-banner" role="alert"><strong>실행 알림</strong><span>{state.error}</span>{state.connectionStatus === "error" && state.runId && <button type="button" onClick={retryConnection}>실시간 연결 다시 시도</button>}</div>}
      {state.workflowStatus === "WAITING" && <div className="waiting-banner"><span className="waiting-icon">!</span><div><strong>AI 에이전트가 작업자 판단을 기다리고 있습니다</strong><p>워크플로는 저장된 사람 검토 지점(HITL)에서 안전하게 일시정지되었습니다.</p></div></div>}

      <section className="run-strip surface" aria-label="Active run summary">
        <div><span>워크플로</span><strong className={`tone-${statusTone}`}>{WORKFLOW_LABEL[state.workflowStatus] ?? state.workflowStatus}</strong></div>
        <div><span>대상 설비</span><strong>{preview?.equipment_id ?? "베어링 시험 설비"}</strong></div>
        <div><span>측정 데이터</span><strong>{measurementDisplayName(state.run?.measurement_id ?? measurementId, state.run?.demo_scenario ?? selectedSample?.demoScenario)}</strong>{measurementId && <details className="technical-details run-tech"><summary>상세 기술정보</summary><div>Measurement ID: {state.run?.measurement_id ?? measurementId}</div>{(state.run?.demo_scenario ?? selectedSample?.demoScenario) && <div>시연 조건: HITL Controlled</div>}</details>}</div>
        <div><span>실행 상태</span><strong>{executionStatusDisplay(state.workflowStatus, Boolean(state.runId))}</strong>{state.runId && <details className="technical-details run-tech"><summary>상세 기술정보</summary><div>Run ID: {state.runId}</div></details>}</div>
        <div><span>현재 작업</span><strong>{currentTaskDisplay(state.workflowStatus, state.currentNode, Boolean(state.runId))}</strong></div>
        <div><span>워크플로 연결</span><strong className={`connection-${state.connectionStatus}`}><i />{CONNECTION_LABEL[state.connectionStatus] ?? state.connectionStatus}</strong></div>
      </section>

      <div className="dashboard-grid">
        <aside className="equipment-column">
          <section className="equipment-card surface">
            <div className="section-heading compact"><div><span className="kicker">설비 정보 · PADERBORN TEST RIG</span><h2>베어링 시험 설비</h2></div><span className={`equipment-badge equipment-${replayState.toLowerCase()}`}>{equipmentBadgeLabel}</span></div>
            <div className={`machine-visual${replaying ? " is-replaying" : ""}`} role="img" aria-label={`모터, 축, 시험 베어링, 반경 하중 구조${replaying ? "; 저장된 측정 데이터 Replay 중" : "; 정지 상태"}`}>
              <div className="machine-sequence">
                <div className="machine-part machine-motor"><i className="machine-motor-rotor">M</i><span>모터</span></div>
                <div className="machine-shaft"><i /></div>
                <div className="machine-part machine-bearing"><i className="machine-bearing-ring"><b /></i><span>시험 베어링</span></div>
                <div className="machine-shaft"><i /></div>
                <div className="machine-part machine-load"><i className="machine-load-mark">F</i><span>반경 하중</span></div>
              </div>
              <div className="machine-sensor">S1 · vibration_1</div>
            </div>
            <div className="machine-caption-flow">저장 측정 데이터 기반 시뮬레이션 · 실시간 센서 수집 아님</div>
            <dl className="equipment-data"><div><dt>선택 데이터</dt><dd>{selectedSample?.label ?? "선택 안 됨"}</dd></div><div><dt>운전 조건 코드</dt><dd>{String(condition.code ?? "N/A")}</dd></div><div className="equipment-reading-group"><dt>시험 설정값</dt><dd><span>회전속도 <b>{typeof condition.rpm === "number" ? `${condition.rpm} RPM` : "—"}</b></span><span>토크 <b>{typeof condition.load_torque_nm === "number" ? `${condition.load_torque_nm} Nm` : "—"}</b></span><span>반경하중 <b>{typeof condition.radial_force_n === "number" ? `${condition.radial_force_n} N` : "—"}</b></span><small>시험 시 설정한 기준 운전조건</small></dd></div><div className="equipment-reading-group is-measured"><dt>현재 실측값 · Replay</dt><dd><span>회전속도 <b>{measuredSpeed === undefined ? "—" : `${measuredSpeed.toFixed(2)} RPM`}</b></span><span>토크 <b>{measuredTorque === undefined ? "—" : `${measuredTorque.toFixed(2)} Nm`}</b></span><span>반경하중 <b>{measuredForce === undefined ? "—" : `${Math.round(measuredForce)} N`}</b></span><small>측정 당시 기록된 값 · Replay 시간에 따라 변경</small></dd></div><div><dt>데이터 출처</dt><dd>{preview?.source ?? "—"}</dd></div></dl>{measurementId && <details className="technical-details equipment-tech"><summary>측정 기술정보</summary><div>베어링 ID: {preview?.bearing_id ?? "—"}</div><div>Measurement ID: {measurementId}</div></details>}
          </section>
          <section className="sensor-card surface"><div className="section-heading compact"><div><span className="kicker">PADERBORN · 측정 데이터 Replay</span><h2>진동 파형</h2></div></div>{previewError ? <div className="empty-copy">{previewError}</div> : <Waveform key={measurementId} preview={preview} replaying={replaying} onProgress={reportReplayProgress} />}</section>
          <InspectionImageInput file={inspectionImage} disabled={state.workflowStatus === "RUNNING" || state.workflowStatus === "WAITING"} onChange={setInspectionImage} />
          <section className="features-card surface"><div className="section-heading compact"><div><span className="kicker">모델 입력</span><h2>진동 신호 특성</h2></div></div><div className="feature-grid">{featureCards.length ? featureCards.map(([key, value]) => <article key={key}><span>{formatFeature(key)}</span><strong>{Number(value).toFixed(3)}</strong><small>특성 추출 파이프라인 값</small></article>) : ["실효값 · RMS", "첨도 · Kurtosis", "파고율 · Crest factor", "주요 주파수 · Dominant freq."].map((item) => <article className="placeholder" key={item}><span>{item}</span><strong>—</strong><small>분석 대기 중</small></article>)}</div></section>
        </aside>

        <div className="center-column"><AgentOffice state={state} /><LangGraphView state={state} /></div>

        <aside className="status-column">
          <section className="live-card surface">
            <div className="section-heading compact"><div><span className="kicker">실시간 워크플로 상태</span><h2>AI 진단 진행 상태</h2></div><span className="live-tag"><i /> Workflow LIVE</span></div>
            <div className="current-operation"><span>현재 수행 작업 · ACTIVE OPERATION</span><strong>{operationLabel}</strong><small>{activeLabel}</small></div>
            <div className="metric-stack"><div><span>근거 충족 상태</span><strong className={`evidence-${(state.evidenceStatus ?? "none").toLowerCase()}`}>{state.evidenceStatus ? (EVIDENCE_STATUS_LABEL[state.evidenceStatus] ?? state.evidenceStatus) : "해당 없음"}</strong></div><div><span>검색된 근거</span><strong>{state.evidenceCount}건</strong></div><div><span>근거 재검색</span><strong>{state.retryCount}회</strong></div><div><span>경과 시간</span><strong>{elapsed.toFixed(1)}초</strong></div></div>
          </section>
          <section className="model-card surface"><div className="section-heading compact"><div><span className="kicker">ML 이상탐지</span><h2>설비 상태 분석 결과</h2></div></div>{state.analysisSummary ? <><div className={`model-result result-${state.analysisSummary.status}`}><span>{state.analysisSummary.status === "normal" ? "정상" : "이상"}</span><strong>{state.analysisSummary.status === "normal" ? "정상 상태" : "손상 의심"}</strong></div><dl><div><dt>적용 모델</dt><dd>{state.analysisSummary.model_id}</dd></div><div><dt>모델 출력 신뢰도</dt><dd>{state.analysisSummary.confidence == null ? "확인 불가" : `${(state.analysisSummary.confidence * 100).toFixed(1)}%`}</dd></div></dl><p className="probability-note">모델 출력값이며 보정된 설비 고장 확률이 아닙니다.</p></> : <div className="empty-copy">이상탐지 분석이 완료되면 결과가 표시됩니다.</div>}</section>
          <EventTimeline events={state.timeline} />
        </aside>
      </div>

      <DetailTabs state={state} history={history} />
      <footer><span>AI SMART FACTORY AGENT OFFICE</span><p>의사결정 지원 전용 · 설비 자동제어 없음 · 모든 기술 근거는 승인된 출처로 추적 가능</p><span>저장 측정 데이터로 센서 입력을 시뮬레이션하며, Workflow 진행 상태는 실시간 표시됩니다.</span></footer>
      <HumanInputModal request={state.pendingHumanRequest} action={activeAction} submitting={Boolean(loadingPhase)} onSubmit={submitHuman} onImageUpload={uploadHumanInspectionImage} />
    </main>
  );
}
