# AI Smart Factory Agent Office 구현 감사

검증일: 2026-10-01  
판정 기준: 실제 소스 경로, 활성 artifact, 저장소, 자동화 테스트, 정상 및 손상 Measurement E2E 실행 결과

## 판정 정의

- `IMPLEMENTED_AND_VERIFIED`: 실행 코드가 현재 서비스에 연결되어 있고 테스트 또는 실제 E2E로 동작을 확인함
- `IMPLEMENTED_BUT_NOT_VERIFIED`: 실행 코드는 있으나 이번 실제 Paderborn 정상·손상 E2E에서는 사용하지 않음
- `PLANNED_OR_UNUSED`: 설계 또는 확장 지점만 있거나 현재 활성 경로에서 사용하지 않음

## 기능별 감사 결과

| 기능 | 구현 여부 | 실제 코드 위치 | E2E 사용 여부 | 보고서 포함 여부 |
|---|---|---|---|---|
| Paderborn MAT 인덱싱과 Measurement 조회 | IMPLEMENTED_AND_VERIFIED | `backend/app/data/adapters/paderborn.py` | 정상·손상 E2E 모두 사용 | 포함 |
| 저장 데이터 Replay와 실측 운전값 표시 | IMPLEMENTED_AND_VERIFIED | `frontend/src/app/page.tsx`, `frontend/src/components/Waveform.tsx`, `backend/app/api/v1/analysis.py` | UI 및 API 경로 확인 | 포함 |
| 특징 추출 | IMPLEMENTED_AND_VERIFIED | `backend/app/ml/features/`, `backend/app/ml/inference/service.py` | 두 E2E의 ML 입력 생성 | 포함 |
| Random Forest 추론 | IMPLEMENTED_AND_VERIFIED | `backend/app/ml/inference/service.py`, `backend/app/services/analysis.py`, `artifacts/ml/baseline_v1/model.joblib` | 정상·손상 분기 결정 | 포함 |
| 모델 artifact와 평가정보 조회 | IMPLEMENTED_AND_VERIFIED | `backend/app/ml/registry/file_registry.py`, `backend/app/api/v1/models.py`, `artifacts/ml/baseline_v1/` | `/models/current`와 시스템 상태에서 확인 | 포함 |
| LangGraph 상태 기반 Workflow | IMPLEMENTED_AND_VERIFIED | `backend/app/agent/graph.py`, `backend/app/agent/routing.py`, `backend/app/agent/nodes.py` | 정상·손상 경로 분리 확인 | 포함 |
| 5개 역할 기반 Agent Office 표시 | IMPLEMENTED_AND_VERIFIED | `frontend/src/components/AgentOffice.tsx`, `frontend/src/features/agent-run/event-mapper.ts` | Backend 이벤트를 역할별 상태로 표시 | 포함 |
| RAG Query 생성 | IMPLEMENTED_AND_VERIFIED | `backend/app/rag/retrieval/query_builder.py`, `backend/app/agent/nodes.py` | 손상 E2E에서 목적별 질의 2개 생성 | 포함 |
| Chroma Vector 검색 | IMPLEMENTED_AND_VERIFIED | `backend/app/rag/vector_store/chroma.py`, `backend/app/rag/retrieval/service.py` | 손상 E2E에서 실제 검색 | 포함 |
| EvidenceObject와 Citation | IMPLEMENTED_AND_VERIFIED | `backend/app/domain/schemas/analysis.py`, `backend/app/rag/retrieval/service.py`, `backend/app/agent/schemas.py` | 손상 E2E에서 Evidence 9건과 보고서 인용 생성 | 포함 |
| 근거 기반 진단 | IMPLEMENTED_AND_VERIFIED | `backend/app/agent/reasoning.py`, `backend/app/agent/nodes.py` | 손상 E2E에서 진단 후보 생성 | 포함 |
| 근거 충족 검증 및 제한된 재검색 | IMPLEMENTED_AND_VERIFIED | `backend/app/agent/reasoning.py`, `backend/app/agent/routing.py` | 통합·라우팅 테스트와 손상 E2E 확인 | 포함 |
| 점검계획 및 조치권고 | IMPLEMENTED_AND_VERIFIED | `backend/app/agent/actions.py`, `backend/app/agent/policies/action_policy.py`, `backend/app/agent/nodes.py` | 손상 E2E에서 생성 | 포함 |
| Final Report | IMPLEMENTED_AND_VERIFIED | `backend/app/agent/nodes.py`, `backend/app/api/v1/agent.py` | 정상·손상 보고서 생성 및 재조회 확인 | 포함 |
| Run History와 상세 복원 | IMPLEMENTED_AND_VERIFIED | `backend/app/agent/run_manager.py`, `frontend/src/app/history/` | 새 프로세스에서 두 Run과 보고서 복원 확인 | 포함 |
| SSE 이벤트와 제한 재연결 | IMPLEMENTED_AND_VERIFIED | `backend/app/api/v1/agent.py`, `frontend/src/features/agent-run/hooks/use-agent-run.ts` | API 및 Frontend 회귀 테스트 확인 | 포함 |
| SQLite Run/Event/Human Request 저장 | IMPLEMENTED_AND_VERIFIED | `backend/app/agent/run_manager.py` | E2E Run과 Event 저장 확인 | 포함 |
| LangGraph SQLite Checkpoint | IMPLEMENTED_AND_VERIFIED | `backend/app/agent/service.py`, `backend/tests/test_checkpoint_resume.py` | E2E Thread와 Checkpoint 생성 및 복원 테스트 | 포함 |
| Long-term Memory | IMPLEMENTED_AND_VERIFIED | `backend/app/memory/`, `backend/app/agent/run_manager.py` | 완료 Run 후 기록, 이력 조회 시 미증가 확인 | 포함 |
| HITL 승인·수정·거절 및 resume | IMPLEMENTED_AND_VERIFIED | `backend/app/agent/nodes.py`, `backend/app/agent/run_manager.py`, `backend/app/api/v1/agent.py` | 통합 테스트와 시나리오 C에서 WAITING→RUNNING→COMPLETED 확인; 일반 손상 B는 정책상 HITL 없이 완료 | 안전 구조로 제한해 포함 |
| Multimodal 이미지 저장과 관찰 분석 | IMPLEMENTED_BUT_NOT_VERIFIED | `backend/app/vision/`, `backend/app/api/v1/agent.py`, `frontend/src/app/page.tsx` | 자동화 통합 테스트는 통과했으나 이번 실제 Paderborn 두 E2E에는 이미지 미첨부 | 확장 구조와 한계로만 포함 |
| 기술지식 읽기 전용 화면과 한국어 검색어 변환 | IMPLEMENTED_AND_VERIFIED | `frontend/src/components/KnowledgeWorkspace.tsx`, `frontend/src/features/knowledge/query-translator.ts`, `backend/app/api/v1/knowledge.py` | API 및 Frontend 테스트 확인 | 포함 |
| AI 모델 투명성 화면 | IMPLEMENTED_AND_VERIFIED | `frontend/src/app/models/page.tsx`, `backend/app/api/v1/models.py` | artifact 값과 API 응답 대조 | 포함 |
| 시스템 Read-only 상태 화면 | IMPLEMENTED_AND_VERIFIED | `backend/app/system/status.py`, `frontend/src/app/system/page.tsx` | 전체 상태 READY와 실제 저장소 Count 대조 | 포함 |
| 외부 LLM 기반 자유 생성 진단 | PLANNED_OR_UNUSED | 활성 Agent factory는 결정론적 reasoner와 planner 사용 | 현재 검증 경로에서 사용하지 않음 | 제외 |
| CNN 또는 Deep Learning 추론 | PLANNED_OR_UNUSED | `input_spec.json`에 deferred로 기록 | 활성 모델은 Random Forest | 제외 |
| PLC MQTT Kafka 실시간 센서 수집 | PLANNED_OR_UNUSED | 활성 ingestion 코드 없음 | Recorded Data 선택 방식 사용 | 현재 한계와 향후 구조로만 포함 |
| 실제 설비 자동제어 | PLANNED_OR_UNUSED | 제어 명령 출력 경로 없음 | 의사결정 지원만 수행 | 구현 기능에서 제외 |
| 현장 사용자 효과 수치 | PLANNED_OR_UNUSED | 측정된 사용자 연구 없음 | 검증 없음 | 정량 효과에서 제외 |

## 검증된 핵심 수치

| 항목 | 확인 값 | 근거 |
|---|---:|---|
| Paderborn Measurement | 240건 | Dataset adapter 인덱스 및 `/system` |
| ML 입력 Feature | 36개 | `feature_list.json` |
| ML 모델 | RandomForestClassifier v1.0 | `metadata.json`, artifact 역직렬화 |
| Train/Test Measurement | 180 / 60건 | `split.json` |
| Test Window | 239개 | `metrics.json` |
| Knowledge Document | 15개 | Knowledge catalog 및 Chroma metadata |
| Embedding/Chunk | 183개 | `chroma.sqlite3` |
| Embedding 차원 | 384 | 시스템 상태 및 embedding 구현 |
| Agent Office 역할 | 5개 | Frontend 역할 매핑 |
| Backend Graph Node | 25개 | `backend/app/agent/graph.py` |
| 사용자 Workflow 단계 | 13개 | `frontend/src/components/LangGraphView.tsx` |
| 대표 정상 Run | COMPLETED, Evidence 0건, Event 19건 | 실제 E2E 실행 |
| 대표 손상 Run | COMPLETED, Evidence 9건, Event 37건 | 실제 E2E 실행 |
| Backend 테스트 | 163 passed | 전체 pytest 실행 |
| Frontend 테스트 | 28 passed | 전체 npm test 실행 |

## 모델 평가 해석 제한

내부 test split의 Measurement-level Accuracy, Precision, Recall, F1, ROC-AUC는 모두 1.0이다. Split은 measurement 단위 누수를 차단했지만 K001, KA01, KI01 세 bearing ID가 train과 test에 모두 존재한다. 따라서 이 수치는 현재 대표 subset 내부 재현 결과이며, 새로운 설비나 처음 보는 베어링에 대한 현장 일반화 성능으로 해석할 수 없다. 모델 출력 confidence 또한 보정된 실제 고장 확률이 아니다.

## 감사 결론

보고서의 핵심 구현에는 Recorded Measurement 입력, 36개 Feature 기반 Random Forest 분류, 상태별 LangGraph 분기, 손상 경로의 Chroma RAG와 Evidence, 진단·점검·조치·보고서, 저장 및 복원만 사용한다. HITL은 통합 테스트가 확인한 안전 경로로 설명한다. Multimodal은 실제 Paderborn 대표 E2E에서 검증하지 않았으므로 선택형 확장 구조로만 표시한다. 실시간 센서 ingestion, 설비 자동제어, 외부 LLM 자유 생성, CNN은 현재 구현 기능으로 표현하지 않는다.
