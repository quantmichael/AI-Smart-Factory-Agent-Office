import { useEffect, useState } from "react";

import type { HumanRequest, RecommendedAction } from "@/features/agent-run/types";
import type { HumanInputPayload } from "@/lib/api";

const FIELD_LABEL: Record<string, string> = { inspection_image_id: "설비 점검 이미지", operating_condition_confirmation: "운전 조건 확인", bearing_visual_inspection: "베어링 외관 점검", vibration_measurement: "진동 상태 확인" };

export function HumanInputModal({ request, action, submitting, onSubmit, onImageUpload }: { request?: HumanRequest; action?: RecommendedAction; submitting: boolean; onSubmit: (payload: HumanInputPayload) => Promise<void>; onImageUpload: (file: File) => Promise<string> }) {
  const [fields, setFields] = useState<Record<string, string>>({});
  const [comment, setComment] = useState("");
  const [image, setImage] = useState<File>();
  const [uploading, setUploading] = useState(false);
  useEffect(() => { setFields({}); setComment(""); setImage(undefined); }, [request?.request_id]);
  if (!request) return null;

  const submitApproval = (decision: string) => onSubmit({ request_id: request.request_id, response: { decision }, comment, actor: "agent-office-operator" });
  const submitInformation = async () => {
    const response = { ...fields };
    if (request.requested_fields.includes("inspection_image_id") && image) {
      setUploading(true);
      try { response.inspection_image_id = await onImageUpload(image); }
      finally { setUploading(false); }
    }
    await onSubmit({ request_id: request.request_id, response, comment, actor: "agent-office-operator" });
  };
  return (
    <div className="modal-backdrop" role="presentation">
      <section className="human-modal" role="dialog" aria-modal="true" aria-labelledby="human-title">
        <div className="modal-signal"><span /> 작업자 확인 지점</div>
        <h2 id="human-title">{request.request_type === "APPROVAL" ? "작업자 판단이 필요합니다" : "현장 추가 정보가 필요합니다"}</h2>
        <p className="modal-question">{request.question}</p>
        <div className="modal-reason"><strong>에이전트가 멈춘 이유</strong><p>{request.reason}</p></div>
        {action && <div className="modal-action"><span>{action.action_type.replaceAll("_", " ")}</span><strong>{action.summary}</strong><p>{action.reason}</p><small>이 요청은 작업자 검토를 위한 것이며 설비에 자동 명령을 보내지 않습니다.</small></div>}
        {request.request_type === "ADDITIONAL_INFORMATION" && request.requested_fields.map((field) => field === "inspection_image_id" ? <label className="field-label" key={field}><span>{FIELD_LABEL[field]}</span><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setImage(event.target.files?.[0])} required /><small>사진은 외관 관찰 보조정보이며 내부 고장을 확정하지 않습니다.</small></label> : <label className="field-label" key={field}><span>{FIELD_LABEL[field] ?? field.replaceAll("_", " ")}</span><input value={fields[field] ?? ""} onChange={(event) => setFields((current) => ({ ...current, [field]: event.target.value }))} required /></label>)}
        <label className="field-label"><span>작업자 의견 (선택)</span><textarea value={comment} onChange={(event) => setComment(event.target.value)} rows={3} /></label>
        {request.request_type === "APPROVAL" ? <div className="modal-actions"><button className="btn approve" disabled={submitting} onClick={() => submitApproval("APPROVED")}>승인</button><button className="btn revise" disabled={submitting} onClick={() => submitApproval("NEEDS_REVISION")}>수정 요청</button><button className="btn reject" disabled={submitting} onClick={() => submitApproval("REJECTED")}>거절</button></div> : <button className="btn approve full" disabled={submitting || uploading || request.requested_fields.some((field) => field === "inspection_image_id" ? !image : !fields[field]?.trim())} onClick={submitInformation}>{uploading ? "이미지 업로드 중…" : "요청 정보 제출"}</button>}
      </section>
    </div>
  );
}
