# MVP-RC1 3분 시연 스크립트

## 사전 확인

```bash
backend/.venv/bin/python scripts/verify_setup.py
cd backend && .venv/bin/uvicorn app.main:app --reload
cd frontend && npm run dev
```

`GET /api/v1/ready`가 `ready`인지 확인한다. 시연 Sample ID와 예상 경로는
`config/demo_scenarios.json`을 기준으로 하며, 화면의 정상/손상 표시는 선택
편의를 위한 메타데이터일 뿐 Agent Runtime Context에 주입되지 않는다.

## 0:00–0:20 — 문제와 설비 선택

- Agent Office에서 베어링 시험 설비와 실제 Paderborn Measurement를 보여준다.
- 시스템은 자동제어가 아니라 이상탐지·근거검색·점검·사람 판단 지원용임을 설명한다.

## 0:20–0:50 — 실제 진동 ML 탐지

- `손상 베어링 샘플`을 선택하고 진단을 시작한다.
- Sensor Agent와 Detection Agent가 실제 Measurement와 활성 모델
  `bearing_rf_binary_v1`을 처리하는 모습을 보여준다.

## 0:50–1:20 — 기술문서 RAG

- 이상 경로에서 `bearing_v1` Knowledge Pack 검색이 실행되는 모습을 보여준다.
- Evidence 탭에서 출처, 문서 위치, 검색 점수와 공식 URL을 확인한다.

## 1:20–1:50 — LangGraph 진단·검증

- Diagnosis Candidate가 Evidence ID에 연결되고 Evidence Verification을 거치는
  과정을 설명한다.
- 사진이 사용된 경우 시각 관찰은 기술 Evidence와 별도 Source임을 강조한다.

## 1:50–2:15 — Retry 또는 HITL

- 재현 가능한 Retry/HITL은 Controlled Scenario임을 화면과 설명에서 숨기지 않는다.
- HITL에서는 같은 `run_id`로 WAITING 후 작업자 입력을 받아 재개되는 점을 보여준다.

## 2:15–2:40 — 점검·권고·보고서

- Inspection Plan과 Recommended Action을 확인한다.
- 중요한 조치는 사람의 승인이 필요하며 설비 명령이 자동 실행되지 않음을 설명한다.

## 2:40–3:00 — Agent Office와 가치

- AgentEvent/SSE가 Agent Office, Graph, Timeline을 실제로 움직인다는 점을 보여준다.
- Final Report의 모델·Knowledge Pack·Workflow 버전과 Citation 추적을 확인한다.
- 다음 Run에서 Equipment Memory가 설비 과거 Context로 사용되는 흐름으로 마무리한다.

## 예비 시나리오

- Normal: `paderborn:K001:N09_M07_F10:01`
- Abnormal: `paderborn:KA01:N09_M07_F10:01`
- 검증 자동화: `backend/.venv/bin/python scripts/run_e2e_integration.py`
