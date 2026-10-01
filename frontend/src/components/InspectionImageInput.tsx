import { useEffect, useState } from "react";

export function InspectionImageInput({ file, disabled, onChange }: { file?: File; disabled: boolean; onChange: (file?: File) => void }) {
  const [preview, setPreview] = useState<string>();
  useEffect(() => {
    if (!file) { setPreview(undefined); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  return (
    <section className="inspection-image-card surface">
      <div className="section-heading compact"><div><span className="kicker">선택 입력 · OPTIONAL MULTIMODAL</span><h2>설비 점검 이미지</h2></div><span className="vision-tag">VISION</span></div>
      {preview ? <div className="inspection-preview"><img src={preview} alt="업로드 전 설비 점검 이미지 미리보기" /><div><strong>{file?.name}</strong><small>{file ? `${(file.size / 1024).toFixed(1)} KB · ${file.type}` : ""}</small><button type="button" disabled={disabled} onClick={() => onChange(undefined)}>이미지 제거</button></div></div> : <label className="inspection-drop"><input type="file" accept="image/jpeg,image/png,image/webp" disabled={disabled} onChange={(event) => onChange(event.target.files?.[0])} /><strong>점검 사진 선택</strong><small>JPEG, PNG, WebP · 최대 크기는 서버 설정 적용</small></label>}
      <p>설비 외관 중심 사진만 사용하세요. 얼굴·명찰·문서 등 개인정보는 업로드하지 마세요.</p>
      <small className="dataset-caution">별도 점검 입력이며 Paderborn 측정과 동기화된 실제 실험체 이미지로 간주하지 않습니다.</small>
    </section>
  );
}
