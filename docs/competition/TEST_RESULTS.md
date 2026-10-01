# Competition Test Results

검증일: 2026-10-01  
기준: 현재 Source Code, local Runtime DB의 read-only 조회, 전체 Backend/Frontend 자동화 테스트

## Summary

| Test Case | Input | Expected Result | Actual Result | Result | Notes |
|---|---|---|---|---|---|
| TC-01 Normal scenario A | `paderborn:K001:N09_M07_F10:01` | ML normal, RAG/Diagnosis skip, Final Report, `COMPLETED` | Runtime Run `COMPLETED`, Evidence 0, Event 19, Final Report available | PASS | 저장 Measurement 사용 |
| TC-02 Abnormal scenario B | `paderborn:KA01:N09_M07_F10:01` | ML abnormal, RAG/Evidence/Diagnosis/Inspection/Action, Final Report | Runtime Run `COMPLETED`, Evidence 9, Event 37, Final Report available | PASS | 실제 Chroma retrieval 사용 |
| TC-03 HITL scenario C | `paderborn:KA01:N09_M07_F10:02`, `HITL_CONTROLLED` | `WAITING`, Human decision, Checkpoint resume, Final Report | Runtime Run `COMPLETED`, Evidence 9, Event 46, `APPROVED` Human Request 기록, Final Report available | PASS | 통제 조건은 UI와 Run metadata에 공개됨 |
| TC-04 Historical Run / Report restore | A/B/C stored Run | 조회만으로 Workflow/Memory를 재실행하지 않고 상세와 보고서 복원 | `final_report_available=1`; History/API 복원 자동화 테스트 통과 | PASS | Runtime DB read-only 조회와 test suite 기준 |
| TC-05 Inspection image API / stale Run recovery | image metadata, valid/missing saved Run ID | 공개 응답에서 `file_ref` 제거; 404 stale ID만 제거; network error는 ID 유지 | Backend/Frontend 회귀 테스트 통과 | PASS | `test_multimodal_api.py`, `active-run-recovery.test.ts` |
| TC-06 Repository security gate | staged tree and public APIs | Secret, 개인 경로, Runtime DB 없이 Push 가능 | Runtime DB·upload·경로 포함 산출물을 Git 후보에서 제외하고 `/ready` 응답의 내부 경로를 안전한 상태 설명으로 교체 | PASS | 내부경로 비노출 회귀 테스트 포함 |

## Automated Test Results

| Suite | Command | Result |
|---|---|---|
| Backend | `cd backend && .venv/bin/pytest -q` | 163 passed, 0 failed; Starlette TestClient deprecation warning 1건 |
| Frontend | `cd frontend && npm test` | 28 passed, 0 failed |
| TypeScript | `cd frontend && npm run lint` | passed |
| Production Build | `cd frontend && npm run build` | passed; `/`, `/history`, `/history/[runId]`, `/knowledge`, `/models`, `/system`, `/_not-found` 생성 |

첫 TypeScript 실행은 Production Build와 동시에 실행되어 `.next/types` 갱신 경쟁으로 실패했습니다. Build 완료 후 단독 재실행한 TypeScript 검사는 통과했습니다. 이는 Source 오류가 아니라 동일 build directory에 대한 병렬 실행 문제였습니다.

## Runtime Read-only Evidence

검증에 사용한 대표 Run은 기존 Runtime DB에 이미 존재했으며 새 A/B/C Run을 만들지 않았습니다.

| Scenario | Workflow | Evidence | Events | Report | Human decision |
|---|---|---:|---:|---|---|
| A | COMPLETED | 0 | 19 | available | 해당 없음 |
| B | COMPLETED | 9 | 37 | available | 정책상 불필요 |
| C | COMPLETED | 9 | 46 | available | APPROVED |

## System Status

`/api/v1/system/status`는 Backend, Dataset, ML, Knowledge, Vector DB, LangGraph, Checkpoint, Run DB, Memory, Vision을 `READY`로 보고했습니다. 조회 시점의 주요 값은 Dataset 240, Documents 15, Embeddings 183, Stored Runs 22, Checkpoints 338, Memory 113입니다.

System status와 `/api/v1/ready` endpoint 모두 공개 가능한 상태 정보만 반환합니다. `/ready`는 Dataset/Model/Knowledge/Vector DB의 준비 여부를 유지하면서 local absolute path를 반환하지 않도록 회귀 검증했습니다.

## Interpretation Limits

- PASS는 위 입력과 현재 대표 subset/환경에서 확인한 결과입니다.
- ML 지표 1.0을 unseen-bearing 또는 현장 정확도 100%로 해석하지 않습니다.
- Vision 자동화 테스트는 품질 관찰 경로를 검증하며 실제 베어링 고장 판독 성능을 의미하지 않습니다.
- SSE 검증 대상은 Agent Event Streaming이며 live factory sensor ingestion이 아닙니다.
