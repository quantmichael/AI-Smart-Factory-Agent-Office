"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import type { CurrentModel, ModelFeature, ModelMetricLevel } from "@/lib/api";
import { fetchCurrentModel } from "@/lib/api";

const LEVEL_LABEL: Record<string, string> = {
  window_level: "신호 구간 단위",
  measurement_level: "Measurement 단위",
  bearing_level: "베어링 단위",
};
const CHANNEL_LABEL: Record<string, string> = {
  vibration_1: "진동 채널",
  phase_current_1: "전류 채널 1",
  phase_current_2: "전류 채널 2",
};
const CLASS_LABEL: Record<string, string> = { healthy: "정상", damaged: "손상" };
const FEATURE_INFO: Record<string, { label: string; description: string }> = {
  mean: { label: "Mean", description: "신호의 평균적인 중심값" },
  std: { label: "Standard Deviation", description: "신호가 평균에서 변하는 정도" },
  rms: { label: "RMS", description: "전체적인 신호 크기를 나타내는 실효값" },
  peak: { label: "Peak", description: "가장 큰 순간 신호 크기" },
  peak_to_peak: { label: "Peak-to-Peak", description: "최댓값과 최솟값 사이의 폭" },
  crest_factor: { label: "Crest Factor", description: "RMS 대비 순간 Peak의 상대적 크기" },
  skewness: { label: "Skewness", description: "신호 분포의 비대칭 정도" },
  kurtosis: { label: "Kurtosis", description: "충격성 신호가 나타나는 정도" },
  dominant_frequency_hz: { label: "Dominant Frequency", description: "가장 강하게 나타나는 주요 주파수" },
  spectral_centroid_hz: { label: "Spectral Centroid", description: "주파수 에너지의 중심 위치" },
  spectral_energy: { label: "Spectral Energy", description: "주파수 영역에 분포한 신호 에너지" },
  spectral_entropy: { label: "Spectral Entropy", description: "주파수 에너지의 분산·복잡도" },
};
const LIMITATION_LABEL: Record<string, string> = {
  "Bearing identity and state are confounded because only one healthy bearing is local.": "로컬 데이터에는 정상 베어링이 1개뿐이므로 베어링 ID와 상태가 서로 얽혀 있습니다.",
  "Every bearing identity occurs in both train and test; this is not unseen-bearing evaluation.": "모든 베어링 ID가 학습과 평가 양쪽에 포함되어 있어 미관측 베어링 평가가 아닙니다.",
  "Random Forest probabilities are not calibrated equipment-failure probabilities.": "Random Forest 출력값은 보정된 실제 설비 고장 확률이 아닙니다.",
  "No test-set-driven threshold or hyperparameter tuning was performed.": "평가 데이터에 맞춘 분류 기준값 또는 하이퍼파라미터 조정은 수행하지 않았습니다.",
};

function percent(value?: number | null) {
  return value == null ? "—" : `${(value * 100).toFixed(1)}%`;
}

function displayFeatureName(name: string) {
  const [channel, statistic] = name.split("__");
  return `${CHANNEL_LABEL[channel] ?? channel} · ${FEATURE_INFO[statistic]?.label ?? statistic}`;
}

function modelTypeLabel(value: string) {
  return value === "RandomForestClassifier" ? "Random Forest" : value;
}

function aggregationLabel(value: string) {
  return value === "mean damaged-class probability; threshold=0.5"
    ? "손상 클래스 모델 출력 평균 · 분류 기준 0.5"
    : value;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function MetricCard({ name, metric }: { name: string; metric: ModelMetricLevel }) {
  const values = [
    ["Accuracy", metric.accuracy], ["Precision", metric.precision], ["Recall", metric.recall],
    ["F1", metric.f1], ["ROC-AUC", metric.roc_auc], ["손상 Recall", metric.damaged_recall],
  ] as const;
  return <article className="model-metric-card"><header><div><span>{LEVEL_LABEL[name] ?? name}</span><strong>{metric.sample_count.toLocaleString()}개</strong></div><small>평가 표본</small></header><dl>{values.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{percent(value)}</dd></div>)}</dl></article>;
}

function ConfusionMatrix({ metric, classes }: { metric?: ModelMetricLevel; classes: string[] }) {
  if (!metric?.confusion_matrix?.length) return <div className="model-empty">저장된 Confusion Matrix가 없습니다.</div>;
  const labels = classes.map((name) => CLASS_LABEL[name] ?? name);
  return <div className="confusion-wrap"><div className="confusion-axis">예측 결과 →</div><div className="confusion-matrix" style={{ gridTemplateColumns: `minmax(64px, .8fr) repeat(${labels.length}, minmax(72px, 1fr))` }}><span /><>{labels.map((label) => <strong key={`pred-${label}`}>예측 {label}</strong>)}</>{metric.confusion_matrix.map((row, rowIndex) => <div className="confusion-row" key={`row-${labels[rowIndex] ?? rowIndex}`}><strong>실제 {labels[rowIndex] ?? rowIndex}</strong>{row.map((value, columnIndex) => <span className={rowIndex === columnIndex ? "correct" : "incorrect"} key={`${rowIndex}-${columnIndex}`}><b>{value}</b><small>{rowIndex === columnIndex ? "일치" : "오분류"}</small></span>)}</div>)}</div></div>;
}

function FeatureGroup({ channel, features }: { channel: string; features: ModelFeature[] }) {
  return <article className="model-feature-group"><header><span>{CHANNEL_LABEL[channel] ?? channel}</span><strong>{features.length} Features</strong></header><div>{features.map((feature) => { const info = FEATURE_INFO[feature.statistic]; return <div className="model-feature-item" key={feature.name}><strong>{info?.label ?? feature.statistic}</strong><p>{info?.description ?? "저장된 Feature"}</p><small>{feature.name}</small></div>; })}</div></article>;
}

export function ModelWorkspace() {
  const [data, setData] = useState<CurrentModel>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const load = useCallback(async () => {
    setLoading(true); setError(undefined);
    try { setData(await fetchCurrentModel()); }
    catch (nextError: unknown) { setError(nextError instanceof Error ? nextError.message : "AI 모델 정보를 불러오지 못했습니다."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const groupedFeatures = useMemo(() => data?.features.reduce<Record<string, ModelFeature[]>>((groups, feature) => {
    (groups[feature.channel] ??= []).push(feature); return groups;
  }, {}) ?? {}, [data]);
  const topImportance = data?.feature_importance.slice(0, 10) ?? [];
  const maxImportance = topImportance[0]?.importance || 1;
  const measurementMetric = data?.evaluation.levels.measurement_level;

  return <main className="app-shell model-shell">
    <AppHeader active="models" status={<div className="system-health"><span className={`connection-dot ${data?.status === "READY" ? "online" : "offline"}`} /><div><strong>모델 정보 조회</strong><small>READ-ONLY ARTIFACT</small></div></div>} />
    <section className="model-hero"><div><span className="kicker">모델 투명성 · MODEL TRANSPARENCY</span><h1>AI 모델</h1><p>설비 상태 판정에 사용되는 AI 모델의 구조와 평가 결과를 확인합니다.</p></div>{data && <div className="model-ready"><small>ACTIVE MODEL</small><strong>{data.model.model_id}</strong><span>v{data.model.version}</span></div>}</section>

    {loading && <section className="model-feedback surface" aria-live="polite">AI 모델 artifact를 확인하는 중…</section>}
    {!loading && error && <section className="model-feedback model-error surface" role="alert"><strong>AI 모델 정보를 불러오지 못했습니다.</strong><p>{error}</p><button onClick={() => void load()} type="button">다시 시도</button></section>}
    {!loading && !error && !data && <section className="model-feedback surface">표시할 모델 정보가 없습니다.</section>}

    {!loading && !error && data && <>
      <section className="model-overview surface"><div><span>모델</span><strong>{modelTypeLabel(data.model.model_type)}</strong><small>{data.model.model_type}</small></div><div><span>분류</span><strong>{data.model.classes.map((item) => CLASS_LABEL[item] ?? item).join(" / ")}</strong><small>이진 상태 분류</small></div><div><span>입력 Feature</span><strong>{data.model.feature_count}개</strong><small>{data.training_data.diagnostic_channels.length}개 신호 채널</small></div><div><span>학습 Measurement</span><strong>{data.training_data.train_measurement_count ?? "—"}개</strong><small>{data.training_data.train_window_count ?? "—"} windows</small></div><div><span>평가 Measurement</span><strong>{data.training_data.test_measurement_count ?? "—"}개</strong><small>{data.training_data.test_window_count ?? "—"} windows</small></div></section>

      <section className="model-panel surface"><div className="model-panel-heading"><div><span className="kicker">STORED EVALUATION</span><h2>성능 평가</h2><p>저장된 artifact의 평가 결과이며, 현장 정확도나 새로운 설비의 성능 보장을 의미하지 않습니다.</p></div></div>{Object.keys(data.evaluation.levels).length ? <div className="model-metric-grid">{Object.entries(data.evaluation.levels).map(([name, metric]) => <MetricCard key={name} name={name} metric={metric} />)}</div> : <div className="model-empty">저장된 성능 평가 정보가 없습니다.</div>}{data.evaluation.aggregation_rule && <p className="model-technical-note">집계 규칙: {aggregationLabel(data.evaluation.aggregation_rule)} · 모델 출력은 보정된 실제 고장 확률이 아닙니다.</p>}</section>

      <section className="model-split-layout"><div className="model-panel surface"><div className="model-panel-heading"><div><span className="kicker">MEASUREMENT LEVEL</span><h2>Confusion Matrix</h2><p>행은 실제 상태, 열은 모델이 예측한 상태입니다.</p></div></div><ConfusionMatrix metric={measurementMetric} classes={data.model.classes} /></div><div className="model-panel model-limit-summary surface"><span className="kicker">EVALUATION SCOPE</span><h2>평가 결과 해석</h2><strong>현재 결과가 100%여도 완벽한 모델을 뜻하지 않습니다.</strong><p>프로젝트의 제한된 대표 subset에서 얻은 결과이며, 새로운 설비나 미관측 베어링에서 동일한 성능을 보장하지 않습니다.</p><dl><div><dt>Measurement 중복</dt><dd>{data.training_data.measurement_overlap_count === 0 ? "없음" : `${data.training_data.measurement_overlap_count ?? "—"}개`}</dd></div><div><dt>미관측 베어링 평가</dt><dd>{data.training_data.shared_bearing_ids.length ? "아님" : "해당"}</dd></div></dl></div></section>

      <section className="model-panel surface"><div className="model-panel-heading"><div><span className="kicker">MODEL INTERPRETATION</span><h2>Feature Importance</h2><p>모델이 각 Feature를 얼마나 활용했는지 나타내는 상대적 중요도이며, 고장의 원인이나 인과관계가 아닙니다.</p></div></div>{topImportance.length ? <div className="importance-chart">{topImportance.map((item) => <div className="importance-row" key={item.feature}><span className="importance-rank">{String(item.rank).padStart(2, "0")}</span><div><header><strong>{displayFeatureName(item.feature)}</strong><b>{item.importance.toFixed(4)}</b></header><div className="importance-track"><i style={{ width: `${(item.importance / maxImportance) * 100}%` }} /></div><small>{item.feature}</small></div></div>)}</div> : <div className="model-empty">저장된 Feature Importance 정보가 없습니다.</div>}{data.feature_importance.length > 10 && <details className="importance-all"><summary>전체 {data.feature_importance.length}개 Feature Importance 보기</summary><div>{data.feature_importance.map((item) => <p key={item.feature}><span>{item.rank}. {item.feature}</span><b>{item.importance.toFixed(6)}</b></p>)}</div></details>}</section>

      <section className="model-panel surface"><div className="model-panel-heading"><div><span className="kicker">MODEL INPUT</span><h2>입력 Feature</h2><p>Feature의 일반적인 의미이며, 특정 값 하나가 곧 고장을 의미하지는 않습니다.</p></div><span className="count-badge">{data.features.length}개</span></div>{data.features.length ? <div className="model-feature-grid">{Object.entries(groupedFeatures).map(([channel, features]) => <FeatureGroup channel={channel} features={features} key={channel} />)}</div> : <div className="model-empty">저장된 Feature 목록이 없습니다.</div>}<p className="model-exclusion-note">RPM, Torque, Radial Load는 운전조건 Replay 표시값이며 현재 Random Forest의 입력 Feature가 아닙니다.</p></section>

      <section className="model-panel surface"><div className="model-panel-heading"><div><span className="kicker">TRAIN / TEST DATA</span><h2>학습·평가 데이터</h2></div></div><div className="model-data-grid"><dl><div><dt>Dataset</dt><dd>{data.training_data.dataset}</dd></div><div><dt>Task</dt><dd>{data.model.classes.map((item) => CLASS_LABEL[item] ?? item).join(" / ")} 이진 분류</dd></div><div><dt>Split</dt><dd>{data.training_data.split_method ?? "—"}</dd></div><div><dt>Group Key</dt><dd>{data.training_data.group_key ?? "—"}</dd></div></dl><dl><div><dt>Train / Test</dt><dd>{data.training_data.train_measurement_count ?? "—"} / {data.training_data.test_measurement_count ?? "—"} measurements</dd></div><div><dt>Test Ratio</dt><dd>{data.training_data.test_ratio == null ? "—" : percent(data.training_data.test_ratio)}</dd></div><div><dt>Seed</dt><dd>{data.training_data.random_seed ?? "—"}</dd></div><div><dt>Bearing IDs</dt><dd>{[...new Set([...data.training_data.train_bearing_ids, ...data.training_data.test_bearing_ids])].join(", ") || "—"}</dd></div></dl><dl><div><dt>신호 채널</dt><dd>{data.training_data.diagnostic_channels.map((item) => CHANNEL_LABEL[item] ?? item).join(", ") || "—"}</dd></div><div><dt>Window</dt><dd>{data.training_data.window_duration_sec ?? "—"}초 · overlap {data.training_data.overlap_percent ?? "—"}%</dd></div><div><dt>Sampling Rate</dt><dd>{data.training_data.sampling_rate_hz?.toLocaleString() ?? "—"} Hz</dd></div><div><dt>학습 완료</dt><dd>{formatDate(data.model.trained_at)} · v{data.model.version}</dd></div></dl></div></section>

      <section className="model-limitations surface"><span className="kicker">LIMITATIONS · 반드시 함께 확인</span><h2>평가 범위 및 한계</h2><p className="model-limit-lead">현재 성능은 프로젝트에서 사용한 제한된 평가 데이터에 대한 결과이며, 새로운 설비나 미관측 베어링에서 동일한 성능을 보장하지 않습니다.</p><ul><li>Paderborn 전체 데이터가 아닌 <strong>{data.training_data.dataset}</strong>을 사용했습니다.</li><li>Train/Test Measurement 자체의 중복은 {data.training_data.measurement_overlap_count === 0 ? "없으며" : "존재하며"}, 분할 검증은 {data.training_data.leakage_check_passed ? "통과했습니다" : "확인이 필요합니다"}.</li><li>학습과 평가에 공통으로 포함된 Bearing ID: <strong>{data.training_data.shared_bearing_ids.join(", ") || "없음"}</strong></li>{data.artifact_limitations.map((limitation) => <li key={limitation}>{LIMITATION_LABEL[limitation] ?? limitation}</li>)}</ul></section>
    </>}
  </main>;
}
