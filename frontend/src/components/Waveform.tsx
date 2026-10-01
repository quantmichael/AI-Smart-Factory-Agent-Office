import { useEffect, useId, useState } from "react";

import type { MeasurementPreview } from "@/features/agent-run/types";

const REPLAY_SPEED = 0.5;
const WAVEFORM_UPDATE_INTERVAL_MS = 50;
const READING_UPDATE_INTERVAL_MS = 250;

export function Waveform({ preview, replaying, onProgress }: { preview?: MeasurementPreview; replaying: boolean; onProgress?: (progress: number) => void }) {
  if (!preview?.points.length) return <div className="wave-empty">측정 데이터를 선택하면 진동 파형 미리보기가 표시됩니다.</div>;

  return <WaveformTrace preview={preview} replaying={replaying} onProgress={onProgress} />;
}

function WaveformTrace({ preview, replaying, onProgress }: { preview: MeasurementPreview; replaying: boolean; onProgress?: (progress: number) => void }) {
  const [progress, setProgress] = useState(1);
  const clipId = useId().replaceAll(":", "");
  const values = preview.points.map((point) => point.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const spread = max - min || 1;
  const firstTime = preview.points[0].time;
  const lastTime = preview.points.at(-1)?.time ?? firstTime;
  const timeSpan = lastTime - firstTime || 1;
  const path = preview.points
    .map((point, index) => {
      const x = ((point.time - firstTime) / timeSpan) * 600;
      const y = 145 - ((point.value - min) / spread) * 125;
      return `${index ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  useEffect(() => {
    if (!replaying || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setProgress(1);
      onProgress?.(1);
      return;
    }

    const durationMs = Math.max(1000, (timeSpan * 1000) / REPLAY_SPEED);
    const startedAt = performance.now();
    let animationFrame = 0;
    let lastUpdate = 0;
    let lastDisplayUpdate = startedAt;
    setProgress(0);
    onProgress?.(0);
    const update = (now: number) => {
      if (now - lastUpdate >= WAVEFORM_UPDATE_INTERVAL_MS) {
        const nextProgress = ((now - startedAt) % durationMs) / durationMs;
        setProgress(nextProgress);
        lastUpdate = now;
      }
      if (now - lastDisplayUpdate >= READING_UPDATE_INTERVAL_MS) {
        onProgress?.(((now - startedAt) % durationMs) / durationMs);
        lastDisplayUpdate = now;
      }
      animationFrame = window.requestAnimationFrame(update);
    };
    animationFrame = window.requestAnimationFrame(update);
    return () => window.cancelAnimationFrame(animationFrame);
  }, [preview.measurement_id, replaying, timeSpan, onProgress]);

  return (
    <div className="wave-wrap">
      <svg viewBox="0 0 600 160" role="img" aria-label={`${preview.channel} 실제 측정 진동 파형 ${replaying ? "재생 중" : "정지"}`}>
        <defs>
          <linearGradient id="wave-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#43e2c6" stopOpacity=".38" />
            <stop offset="1" stopColor="#43e2c6" stopOpacity="0" />
          </linearGradient>
          <clipPath id={clipId} clipPathUnits="userSpaceOnUse"><rect x="0" y="0" width={600 * progress} height="160" /></clipPath>
        </defs>
        {[30, 80, 130].map((y) => <line key={y} x1="0" y1={y} x2="600" y2={y} className="wave-grid" />)}
        <g clipPath={`url(#${clipId})`}>
          <path d={`${path} L600,160 L0,160 Z`} fill="url(#wave-fill)" />
          <path d={path} className="wave-line" />
        </g>
        {replaying && <line x1={600 * progress} y1="12" x2={600 * progress} y2="150" className="wave-playhead" />}
      </svg>
      <div className="wave-meta"><span>{preview.channel} · {replaying ? "측정 데이터 재생 중" : "재생 정지"}</span><span>{preview.points.length} / {preview.original_sample_count.toLocaleString()} 포인트</span></div>
    </div>
  );
}
