import { useMemo, useState } from "react";
import type { ReactNode } from "react";

import type { AgentRunUIState, MemoryHistory } from "@/features/agent-run/types";
import { inspectionImageUrl } from "@/lib/api";
import { ACTION_LABEL, CONFIDENCE_LABEL, EVIDENCE_STATUS_LABEL, MEMORY_STATUS_LABEL, MEMORY_TYPE_LABEL, PRIORITY_LABEL, PURPOSE_LABEL, QUALITY_LABEL, SOURCE_TYPE_LABEL, evidenceExplanation, measurementDisplayName } from "@/features/agent-run/event-mapper";

const TABS = ["Evidence", "Visual", "Diagnosis", "Inspection", "Action", "History", "Report"] as const;
type Tab = (typeof TABS)[number];
const TAB_LABEL: Record<Tab, string> = { Evidence: "기술 근거", Visual: "시각 관찰", Diagnosis: "진단 후보", Inspection: "점검 계획", Action: "권고 조치", History: "설비 이력", Report: "최종 보고서" };

const label = (value: string | undefined | null, map: Record<string, string>) => value ? (map[value] ?? value.replaceAll("_", " ")) : "없음";
const fieldLabel = (value: string) => ({ operating_condition_confirmation: "운전 조건 확인", bearing_visual_inspection: "베어링 외관 점검", vibration_measurement: "진동 상태 확인", inspection_image_id: "설비 점검 이미지" }[value] ?? value.replaceAll("_", " "));
const TechDetails = ({ children }: { children: ReactNode }) => <details className="technical-details"><summary>상세 기술정보</summary><div>{children}</div></details>;
const analysisLabel: Record<string, string> = { status: "분석 상태", predicted_class: "판정 결과", confidence: "모델 출력 신뢰도", signal_features: "진동 신호 특성", model_id: "적용 모델" };
function analysisForDisplay(summary: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(summary).map(([key, value]) => [analysisLabel[key] ?? key, key === "status" ? (value === "normal" ? "정상" : value === "abnormal" ? "이상" : value) : key === "confidence" && typeof value === "number" ? `${(value * 100).toFixed(1)}%` : value]));
}

function IdChips({ ids, tone = "teal" }: { ids: string[]; tone?: string }) {
  return <div className="id-chips">{ids.map((id) => <span className={`chip chip-${tone}`} key={id}>{id.slice(0, 18)}</span>)}</div>;
}

export function DetailTabs({ state, history }: { state: AgentRunUIState; history?: MemoryHistory }) {
  const [tab, setTab] = useState<Tab>("Evidence");
  const [candidateId, setCandidateId] = useState<string>();
  const candidates = state.run?.diagnosis_candidates ?? state.report?.diagnosis_candidates ?? [];
  const inspections = state.run?.inspection_plan ?? state.report?.inspection_plan ?? [];
  const actions = state.run?.recommended_actions ?? state.report?.recommended_actions ?? [];
  const visual = state.run?.visual_observations ?? state.report?.visual_observations ?? [];
  const usedVisualIds = new Set(candidates.flatMap((item) => item.supporting_visual_observation_ids ?? []));
  const linkedEvidence = useMemo(() => {
    const candidate = candidates.find((item) => item.candidate_id === candidateId);
    return new Set(candidate?.supporting_evidence_ids ?? []);
  }, [candidateId, candidates]);
  const maxRms = Math.max(1, ...(history?.trend.points.map((item) => item.rms ?? 0) ?? []));

  return (
    <section className="details-card surface" aria-labelledby="details-title">
      <div className="tabs" role="tablist" aria-label="Run details">
        {TABS.map((item) => <button role="tab" aria-selected={tab === item} className={tab === item ? "active" : ""} onClick={() => setTab(item)} key={item}>{TAB_LABEL[item]}{item === "Evidence" && state.evidenceCount ? ` ${state.evidenceCount}` : ""}<small>{item}</small></button>)}
      </div>
      <div className="tab-content" id="details-title">
        {tab === "Evidence" && (
          <div className="card-grid evidence-grid">
            {!state.evidence.length && <div className="empty-copy">이상 경로에서 승인된 기술문서를 검색하면 근거가 표시됩니다.</div>}
            {state.evidence.map((item) => (
              <article className={`detail-card ${linkedEvidence.has(item.evidence_id) ? "is-linked" : ""}`} key={item.evidence_id}>
                <div className="detail-top"><span className="purpose-tag">{label(item.purpose, PURPOSE_LABEL)}</span><span>출처 등급 {item.source_tier}</span></div>
                <h3>{item.title}</h3><p className="evidence-explanation">{evidenceExplanation(item.purpose, item.title)}</p><p>{item.content}</p>
                <dl><div><dt>발행기관</dt><dd>{item.publisher}</dd></div><div><dt>문서 위치</dt><dd>{item.page ? `쪽 ${item.page}` : "페이지 정보 없음"}{item.section ? ` · ${item.section}` : ""}</dd></div></dl>
                {item.official_url && <a href={item.official_url} target="_blank" rel="noreferrer">공식 원문 열기 ↗</a>}
                <TechDetails><div>Evidence ID: {item.evidence_id}</div><div>검색 점수: {item.retrieval_score?.toFixed(3) ?? "확인 불가"}</div><div>원문 근거는 번역하지 않고 보존됩니다.</div></TechDetails>
              </article>
            ))}
          </div>
        )}
        {tab === "Visual" && (
          <div className="visual-observation-view">
            {!visual.length && <div className="empty-copy">점검 이미지는 선택사항입니다. 이미지가 없어도 센서·RAG Workflow는 정상 실행됩니다.</div>}
            {visual.map((result) => <article className={`visual-result quality-${result.quality.toLowerCase()}`} key={result.image_id}><img className="visual-source-image" src={inspectionImageUrl(result.image_id)} alt="작업자가 제공한 설비 외관 점검 이미지" /><div className="detail-top"><span className="purpose-tag">{QUALITY_LABEL[result.quality] ?? result.quality}</span><span>이미지 관찰 결과</span></div><h3>설비 점검 이미지 관찰</h3><dl><div><dt>관찰 항목</dt><dd>{result.observations.length}건</dd></div><div><dt>진단 반영 여부</dt><dd>{result.observations.some((item) => usedVisualIds.has(item.observation_id)) ? "반영됨" : "반영되지 않음"}</dd></div></dl>{result.observations.map((item) => <div className="visual-item" key={item.observation_id}><span>{item.category} · {label(item.confidence_level, CONFIDENCE_LABEL)}</span><p>{item.description}</p></div>)}<div className="visual-limitations"><strong>주의사항</strong>{result.limitations.map((item) => <p key={item}>• {item}</p>)}</div><TechDetails><div>이미지 ID: {result.image_id}</div><div>분석 제공자: {result.provider} / {result.model}</div></TechDetails></article>)}
            <p className="dataset-caution">시각 관찰은 기술문서 근거가 아니며, Paderborn 진동 데이터와 동일 실험체의 사진으로 간주하지 않습니다.</p>
          </div>
        )}
        {tab === "Diagnosis" && (
          <div className="card-grid">
            {!candidates.length && <div className="empty-copy">기술 근거 검증 후 진단 후보가 표시됩니다.</div>}
            {candidates.map((item) => (
              <button className={`detail-card diagnosis-card ${candidateId === item.candidate_id ? "is-linked" : ""}`} onClick={() => { setCandidateId(item.candidate_id); setTab("Evidence"); }} key={item.candidate_id}>
                <div className="detail-top"><span className="purpose-tag">{item.fault_type}</span><span>판단 신뢰 수준: {label(item.confidence_level, CONFIDENCE_LABEL)}</span></div>
                <h3>{item.summary}</h3><p>불확실성: {item.uncertainties.join(" · ") || "기록된 항목 없음"}</p>
                <strong>연결된 기술 근거</strong><IdChips ids={item.supporting_evidence_ids} />
                {!!item.supporting_visual_observation_ids?.length && <><strong>연결된 시각 관찰</strong><IdChips ids={item.supporting_visual_observation_ids} tone="amber" /></>}
              </button>
            ))}
          </div>
        )}
        {tab === "Inspection" && (
          <div className="step-list">
            {!inspections.length && <div className="empty-copy">이상 상태가 감지되면 순서형 점검 계획이 표시됩니다.</div>}
            {inspections.map((item) => <article className="inspection-step" key={item.step_id}><span className="step-no">{String(item.order).padStart(2, "0")}</span><div><h3>{item.title}</h3><p>{item.description}</p><small><b>점검 이유:</b> {item.reason}</small><IdChips ids={item.supporting_evidence_ids} /><div className="required-input">필요 입력: {item.required_input.map(fieldLabel).join(", ") || "없음"}</div>{item.safety_note && <div className="safety-note">◇ 안전 참고: {item.safety_note}</div>}<TechDetails><div>점검 ID: {item.step_id}</div><div>원본 입력 키: {item.required_input.join(", ") || "없음"}</div></TechDetails></div></article>)}
          </div>
        )}
        {tab === "Action" && (
          <div className="card-grid">
            {!actions.length && <div className="empty-copy">점검 계획 이후 권고 조치가 표시됩니다. 어떤 조치도 자동 실행되지 않습니다.</div>}
            {actions.map((item) => <article className="detail-card action-card" key={item.action_id}><div className="detail-top"><span className={`priority priority-${item.priority}`}>우선순위 {label(item.priority, PRIORITY_LABEL)}</span><span>{label(item.action_type, ACTION_LABEL)}</span></div><h3>{item.summary}</h3><p>{item.reason}</p><div className="approval-row"><span>{item.requires_human_approval ? "작업자 승인 필요" : "승인 절차 불필요"}</span><span>의사결정 지원 전용</span></div><IdChips ids={item.supporting_evidence_ids} tone="amber" /><TechDetails><div>조치 ID: {item.action_id}</div><div>내부 조치 유형: {item.action_type}</div></TechDetails></article>)}
          </div>
        )}
        {tab === "History" && (
          <div className="history-view">
            <div className="history-summary">
              <article><span>저장된 장기기억</span><strong>{history?.records.length ?? 0}</strong><small>설비별 격리 저장</small></article>
              <article><span>이상 분석 이력</span><strong>{history?.trend.abnormal_count ?? 0}</strong><small>확정 고장 건수 아님</small></article>
              <article><span>정비 기록</span><strong>{history?.maintenance.length ?? 0}</strong><small>명시적 입력만 저장</small></article>
              <article><span>현재 진단 사용</span><strong>{state.run?.memory_used_ids.length ?? 0}</strong><small>과거 기록 참고</small></article>
            </div>
            <section className="trend-panel"><div className="trend-heading"><div><span>RMS 추이</span><h3>최근 측정 분석 추이</h3></div><small>운전조건별 비교 필요</small></div>
              {history?.trend.points.length ? <div className="trend-bars">{history.trend.points.map((point) => <article key={point.memory_id}><div className={`trend-bar trend-${point.analysis_status}`} style={{ height: `${Math.max(8, ((point.rms ?? 0) / maxRms) * 100)}%` }} title={`RMS ${point.rms ?? "N/A"}`} /><span>{point.rms?.toFixed(2) ?? "—"}</span><small>{point.operating_condition ?? "조건 미상"}</small></article>)}</div> : <div className="empty-copy">완료된 진단 Run이 쌓이면 실제 RMS 추이가 표시됩니다.</div>}
              <p>{history?.trend.note ?? "Feature 비교에는 동일 운전조건 확인이 필요합니다."}</p>
            </section>
            <div className="memory-timeline">
              {!history?.records.length && <div className="empty-copy">아직 저장된 설비 장기기억이 없습니다. 첫 진단은 이력 없이 정상 진행됩니다.</div>}
              {history?.records.slice(0, 20).map((record) => <article key={record.memory_id}><time>{new Date(record.event_time).toLocaleString("ko-KR")}</time><div><span>{label(record.memory_type, MEMORY_TYPE_LABEL)} · {label(record.source_type, SOURCE_TYPE_LABEL)}</span><strong>{record.summary}</strong><small>{label(record.status, MEMORY_STATUS_LABEL)}</small></div>{state.run?.memory_used_ids.includes(record.memory_id) && <b>현재 진단에 사용</b>}<TechDetails><div>Memory ID: {record.memory_id}</div><div>원본 출처 ID: {record.source_id}</div></TechDetails></article>)}
              {history?.maintenance.map((record) => <article className="maintenance-memory" key={record.maintenance_id}><time>{new Date(record.performed_at).toLocaleString("ko-KR")}</time><div><span>정비 기록 · 작업자 입력</span><strong>{record.maintenance_type}: {record.description}</strong><small>{record.source_label}</small></div><TechDetails><div>정비 ID: {record.maintenance_id}</div><div>연결 실행 ID: {record.related_run_id ?? "없음"}</div></TechDetails></article>)}
            </div>
          </div>
        )}
        {tab === "Report" && (
          <div className="report-view">
            {!state.report && <div className="empty-copy">보고서 생성 노드가 완료되면 최종 결과가 표시됩니다.</div>}
            {state.report && <><div className="report-banner"><div><span>최종 진단 보고서</span><h3>{measurementDisplayName(state.report.measurement_id, state.report.demo_scenario)}</h3></div><strong>{state.report.evidence_status ? (EVIDENCE_STATUS_LABEL[state.report.evidence_status] ?? state.report.evidence_status) : "정상 경로"}</strong></div><div className="report-columns"><div><h4>AI 분석 결과</h4><pre>{JSON.stringify(analysisForDisplay(state.report.analysis_summary), null, 2)}</pre></div><div><h4>한계 및 주의사항</h4><ul>{state.report.limitations.map((item) => <li key={item}>{item}</li>)}</ul><h4>작업자 검토</h4><p>{state.report.human_interactions.length ? `작업자 검토 ${state.report.human_interactions.length}건 기록` : "작업자 검토가 필요하지 않았습니다."}</p><h4>설비 장기기억</h4><p>이번 진단에서 참고한 과거 기록 {state.report.historical_context_used.length}건</p><h4>버전 추적</h4><p>{state.report.version_trace.model_id} v{state.report.version_trace.model_version} · {state.report.version_trace.knowledge_pack_id} · {state.report.version_trace.workflow_version}</p><h4>인용 근거</h4><p>추적 가능한 기술문서 출처 {state.report.citations.length}건</p><TechDetails><div>Run ID: {state.report.run_id}</div><div>Measurement ID: {state.report.measurement_id}</div>{state.report.demo_scenario && <div>시연 조건: HITL Controlled</div>}</TechDetails></div></div></>}
          </div>
        )}
      </div>
    </section>
  );
}
