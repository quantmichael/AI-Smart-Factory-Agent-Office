# AI Smart Factory Agent Office

## 07. API & Database Specification

**문서 버전:** v0.1\
**선행 문서:** `01_PROJECT_OVERVIEW.md` \~ `06_AGENT_OFFICE_UI.md`\
**목적:** Frontend, FastAPI, ML/DL, RAG, LangGraph Agent가 공유할 API
계약과 데이터 저장 구조를 정의한다.

------------------------------------------------------------------------

## 1. 설계 원칙

1.  Frontend는 ML/DL, Vector DB를 직접 호출하지 않는다.
2.  외부 진입점은 FastAPI로 통일한다.
3.  LangGraph는 `run_id`를 중심으로 실행 상태를 관리한다.
4.  ML/DL 결과는 `Standard Analysis Result`로 표준화한다.
5.  RAG 결과는 `Evidence Object`로 표준화한다.
6.  UI 실시간 상태는 Agent Event로 전달한다.
7.  DB에는 원본 대용량 센서 배열보다 참조·요약·결과를 저장한다.
8.  API와 DB가 특정 Paderborn 데이터 구조에 종속되지 않도록 한다.
9.  모든 진단 결과는 사용한 모델과 Knowledge Pack 버전을 추적할 수
    있어야 한다.

------------------------------------------------------------------------

## 2. API Base

초기:

``` text
/api/v1
```

예:

``` text
GET  /api/v1/equipment
POST /api/v1/agent/runs
GET  /api/v1/agent/runs/{run_id}
```

향후 호환성 변경을 위해 API Version을 URL에 포함한다.

------------------------------------------------------------------------

## 3. 공통 ID

``` text
equipment_id
measurement_id
analysis_id
run_id
document_id
chunk_id
evidence_id
event_id
model_id
knowledge_pack_id
```

UUID 또는 충돌 가능성이 낮은 식별자를 사용한다.

사용자 화면용 짧은 Display ID는 별도로 둘 수 있다.

------------------------------------------------------------------------

## 4. Equipment API

### GET `/api/v1/equipment`

설비 목록.

응답 예:

``` json
{
  "items": [
    {
      "equipment_id": "EQ-001",
      "name": "Bearing Test Rig 01",
      "equipment_type": "bearing",
      "status": "NORMAL",
      "latest_analysis_at": "2026-09-17T10:00:00"
    }
  ]
}
```

### GET `/api/v1/equipment/{equipment_id}`

설비 상세.

``` json
{
  "equipment_id": "EQ-001",
  "name": "Bearing Test Rig 01",
  "equipment_type": "bearing",
  "manufacturer": null,
  "model": "6203",
  "dataset_source": "paderborn",
  "metadata": {},
  "status": "NORMAL"
}
```

------------------------------------------------------------------------

## 5. Measurement API

### GET `/api/v1/equipment/{equipment_id}/measurements`

분석 가능한 Measurement 목록.

Query 예:

``` text
?label=damaged&limit=20
```

응답:

``` json
{
  "items": [
    {
      "measurement_id": "MEAS-001",
      "equipment_id": "EQ-001",
      "source": "paderborn",
      "operating_condition": {
        "rpm": 1500,
        "load_torque_nm": 0.7,
        "radial_force_n": 1000
      },
      "label": {
        "state": "damaged",
        "fault_type": null
      }
    }
  ]
}
```

### GET `/api/v1/measurements/{measurement_id}/signal`

UI 차트용 Downsampled signal을 반환한다.

대용량 Raw Signal 전체를 기본 응답으로 반환하지 않는다.

------------------------------------------------------------------------

## 6. Analysis API

### POST `/api/v1/analysis`

ML/DL 분석만 실행할 때 사용한다.

Request:

``` json
{
  "equipment_id": "EQ-001",
  "measurement_id": "MEAS-001",
  "model_id": "rf_v1"
}
```

Response:

``` json
{
  "analysis_id": "AN-001",
  "equipment_id": "EQ-001",
  "measurement_id": "MEAS-001",
  "model": {
    "model_id": "rf_v1",
    "model_type": "random_forest",
    "task": "healthy_vs_damaged"
  },
  "result": {
    "status": "abnormal",
    "predicted_class": "damaged",
    "confidence": 0.91,
    "anomaly_score": null
  },
  "signal_features": {
    "rms": 0.0,
    "peak": 0.0,
    "kurtosis": 0.0
  }
}
```

------------------------------------------------------------------------

## 7. Agent Run 생성

### POST `/api/v1/agent/runs`

전체 End-to-End 진단을 시작한다.

Request:

``` json
{
  "equipment_id": "EQ-001",
  "measurement_id": "MEAS-001",
  "model_id": "rf_v1",
  "knowledge_pack_id": "bearing_v1",
  "options": {
    "max_retrieval_retry": 2,
    "human_in_the_loop": true
  }
}
```

초기 Response:

``` json
{
  "run_id": "RUN-001",
  "workflow_status": "RUNNING",
  "current_node": "initialize_run",
  "created_at": "..."
}
```

장시간 Agent 실행을 HTTP 요청 하나에서 끝까지 기다리지 않는다.

------------------------------------------------------------------------

## 8. Agent Run 조회

### GET `/api/v1/agent/runs/{run_id}`

``` json
{
  "run_id": "RUN-001",
  "equipment_id": "EQ-001",
  "measurement_id": "MEAS-001",
  "workflow_status": "RUNNING",
  "current_node": "retrieve_knowledge",
  "analysis_result": {},
  "evidence_status": "PARTIAL",
  "evidence_count": 4,
  "retrieval_retry_count": 1,
  "human_input_required": false,
  "started_at": "...",
  "completed_at": null
}
```

------------------------------------------------------------------------

## 9. SSE Event Stream

### GET `/api/v1/agent/runs/{run_id}/events/stream`

Content-Type:

``` text
text/event-stream
```

Event payload:

``` json
{
  "event_id": "EVT-012",
  "run_id": "RUN-001",
  "sequence": 12,
  "event_type": "node_started",
  "node": "retrieve_knowledge",
  "agent_role": "rag_agent",
  "message": "관련 기술문서를 검색하고 있습니다.",
  "payload": {},
  "created_at": "..."
}
```

------------------------------------------------------------------------

## 10. Event Type

초기 Enum:

``` text
workflow_started
node_started
node_completed
tool_started
tool_completed
detection_normal
detection_abnormal
retrieval_completed
evidence_status_changed
human_input_required
human_input_received
workflow_completed
workflow_error
```

------------------------------------------------------------------------

## 11. SSE 재연결

Client는 마지막 Event sequence 또는 ID를 기억한다.

연결이 끊기면:

``` text
GET current run
        +
reconnect event stream
```

방식으로 UI State를 복구한다.

MVP에서 완전한 Event Replay가 어렵다면 현재 Run State 조회를 기준으로
복구한다.

------------------------------------------------------------------------

## 12. Evidence API

### GET `/api/v1/agent/runs/{run_id}/evidence`

``` json
{
  "items": [
    {
      "evidence_id": "EVD-001",
      "document_id": "DOC-001",
      "chunk_id": "CHK-001",
      "title": "Technical Document",
      "publisher": "Source Publisher",
      "source_tier": 2,
      "document_type": "diagnostic_guide",
      "page": 10,
      "section": "...",
      "content": "...",
      "retrieval_score": 0.82,
      "query_type": "diagnostic"
    }
  ]
}
```

------------------------------------------------------------------------

## 13. Diagnosis Report API

### GET `/api/v1/agent/runs/{run_id}/report`

``` json
{
  "run_id": "RUN-001",
  "detected_status": "abnormal",
  "analysis_result": {},
  "diagnosis_candidates": [
    {
      "candidate_id": "C01",
      "cause": "...",
      "confidence": "medium",
      "supporting_evidence_ids": ["EVD-001"],
      "contradicting_evidence_ids": [],
      "requires_confirmation": true
    }
  ],
  "evidence_status": "SUFFICIENT",
  "inspection_plan": [],
  "recommended_actions": [],
  "citations": [],
  "limitations": []
}
```

------------------------------------------------------------------------

## 14. Human-in-the-loop API

### GET `/api/v1/agent/runs/{run_id}/human-request`

현재 요청 조회.

### POST `/api/v1/agent/runs/{run_id}/human-response`

Request:

``` json
{
  "request_id": "HR-001",
  "response": {
    "lubrication_state": "unknown",
    "visual_condition": "normal"
  }
}
```

Response:

``` json
{
  "run_id": "RUN-001",
  "workflow_status": "RUNNING",
  "resumed": true
}
```

------------------------------------------------------------------------

## 15. Knowledge Base API

### GET `/api/v1/knowledge/documents`

문서 목록.

### POST `/api/v1/knowledge/documents`

문서 등록/ingestion 요청.

### GET `/api/v1/knowledge/documents/{document_id}`

Metadata 조회.

### POST `/api/v1/knowledge/search`

개발/평가용 직접 검색 API.

Request:

``` json
{
  "query": "bearing vibration damage inspection",
  "knowledge_pack_id": "bearing_v1",
  "filters": {
    "document_type": ["diagnostic_guide", "failure_analysis"],
    "source_tier_max": 3
  },
  "top_k": 5
}
```

운영 UI에서 RAG를 우회해 최종 진단을 생성하는 용도로 사용하지 않는다.

------------------------------------------------------------------------

## 16. Model API

### GET `/api/v1/models`

``` json
{
  "items": [
    {
      "model_id": "rf_v1",
      "name": "Bearing RF Baseline",
      "model_type": "random_forest",
      "task": "healthy_vs_damaged",
      "version": "1.0",
      "status": "active"
    }
  ]
}
```

------------------------------------------------------------------------

## 17. 공통 Error Response

``` json
{
  "error": {
    "code": "MODEL_INFERENCE_ERROR",
    "message": "분석을 완료하지 못했습니다.",
    "request_id": "REQ-001",
    "retryable": true
  }
}
```

내부 Stack Trace는 Client에 노출하지 않는다.

------------------------------------------------------------------------

# DATABASE

## 18. DB 선택

MVP:

``` text
SQLite
```

또는 처음부터:

``` text
PostgreSQL
```

권장 최종 구조는 PostgreSQL이다.

Vector Embedding은 Application DB와 분리하여 Chroma/Qdrant 등에 저장할
수 있다.

------------------------------------------------------------------------

## 19. 관계 개요

``` text
Equipment
   │
   ├── Measurement
   │       │
   │       └── SensorAnalysis
   │
   ├── DiagnosisRun
   │       ├── AgentEvent
   │       ├── Evidence
   │       ├── DiagnosisCandidate
   │       ├── InspectionStep
   │       ├── RecommendedAction
   │       └── HumanFeedback
   │
   └── MaintenanceHistory

KnowledgePack
   │
   └── KnowledgeDocument
            │
            └── KnowledgeChunk (Vector DB reference)

MLModel
   │
   └── SensorAnalysis
```

------------------------------------------------------------------------

## 20. `equipment`

``` text
id                  PK
name
equipment_type
manufacturer
model
dataset_source
status
metadata_json
created_at
updated_at
```

------------------------------------------------------------------------

## 21. `measurement`

``` text
id                  PK
equipment_id        FK
source
source_reference
measured_at
sampling_rate
duration_sec
operating_condition_json
ground_truth_json
raw_data_reference
metadata_json
created_at
```

Raw Signal 자체는 파일/Object Storage에 둘 수 있다.

------------------------------------------------------------------------

## 22. `ml_model`

``` text
id                  PK
name
model_type
task
version
artifact_reference
feature_schema_json
metrics_json
status
created_at
```

------------------------------------------------------------------------

## 23. `sensor_analysis`

``` text
id                  PK
equipment_id        FK
measurement_id      FK
model_id            FK
status
predicted_class
confidence
anomaly_score
signal_features_json
model_output_json
created_at
```

------------------------------------------------------------------------

## 24. `diagnosis_run`

``` text
id                      PK
equipment_id            FK
measurement_id          FK
analysis_id             FK
knowledge_pack_id       FK
workflow_status
current_node
evidence_status
retrieval_retry_count
max_retrieval_retry
human_input_required
started_at
completed_at
error_json
created_at
updated_at
```

------------------------------------------------------------------------

## 25. `agent_event`

``` text
id                  PK
run_id              FK
sequence
event_type
node
agent_role
message
payload_json
created_at
```

Index:

``` text
(run_id, sequence)
```

------------------------------------------------------------------------

## 26. `knowledge_pack`

``` text
id                  PK
name
domain
version
embedding_model
chunking_version
status
created_at
updated_at
```

예:

``` text
bearing_v1
```

------------------------------------------------------------------------

## 27. `knowledge_document`

``` text
id                  PK
knowledge_pack_id   FK
title
publisher
source_tier
document_type
equipment_type
component
fault_type_json
language
version
license
source_origin
checksum
metadata_json
ingested_at
```

------------------------------------------------------------------------

## 28. `knowledge_chunk`

Application DB에는 Vector DB의 Chunk를 추적할 최소 Metadata를 둘 수
있다.

``` text
id                  PK
document_id         FK
vector_store_id
section
page
content_hash
metadata_json
created_at
```

실제 embedding/vector는 Vector DB가 관리한다.

------------------------------------------------------------------------

## 29. `evidence`

특정 Agent Run에서 실제 사용된 검색 근거 Snapshot.

``` text
id                  PK
run_id              FK
document_id         FK
chunk_id
query_type
retrieval_score
content_snapshot
page
section
source_tier
created_at
```

Knowledge Base가 나중에 바뀌어도 당시 진단에 사용한 근거를 추적할 수
있도록 필요한 Snapshot을 보존한다.

------------------------------------------------------------------------

## 30. `diagnosis_candidate`

``` text
id                          PK
run_id                      FK
candidate_key
cause
confidence_level
reasoning_summary
requires_confirmation
created_at
```

관계 Evidence는 별도 Mapping Table 또는 JSON으로 구현할 수 있다.

권장:

``` text
diagnosis_candidate_evidence
candidate_id
evidence_id
relation_type
```

`relation_type`:

``` text
supporting
contradicting
```

------------------------------------------------------------------------

## 31. `inspection_step`

``` text
id                  PK
run_id              FK
step_order
action
purpose
status
evidence_ids_json
result_json
created_at
updated_at
```

------------------------------------------------------------------------

## 32. `recommended_action`

``` text
id                  PK
run_id              FK
action_level
action
reason
evidence_ids_json
requires_approval
created_at
```

`action_level`:

``` text
MONITOR
INSPECT
SCHEDULE_MAINTENANCE
EXPERT_REVIEW
SHUTDOWN_CHECK
```

------------------------------------------------------------------------

## 33. `human_request`

``` text
id                  PK
run_id              FK
request_type
question
requested_fields_json
status
created_at
resolved_at
```

------------------------------------------------------------------------

## 34. `human_feedback`

``` text
id                  PK
run_id              FK
request_id          FK nullable
feedback_type
response_json
created_at
```

------------------------------------------------------------------------

## 35. `maintenance_history`

Long-term Memory 고도화용.

``` text
id                  PK
equipment_id        FK
run_id              FK nullable
action
result
performed_at
performed_by
metadata_json
created_at
```

------------------------------------------------------------------------

## 36. Long-term Memory View

Agent가 과거 기록을 사용할 때 전체 DB를 LLM에 전달하지 않는다.

필요한 정보를 조회하여 요약한다.

예:

``` json
{
  "equipment_id": "EQ-001",
  "recent_anomalies": 3,
  "last_diagnosis": "...",
  "last_maintenance": "...",
  "repeated_candidate_causes": ["..."]
}
```

------------------------------------------------------------------------

## 37. 상태 Enum

### Workflow

``` text
CREATED
RUNNING
WAITING_HUMAN
COMPLETED
LIMITED
ERROR
CANCELLED
```

### Equipment

``` text
NORMAL
ANALYZING
ABNORMAL
DIAGNOSING
NEEDS_CHECK
MAINTENANCE_RECOMMENDED
ERROR
```

### Evidence

``` text
NOT_STARTED
SUFFICIENT
PARTIAL
INSUFFICIENT
CONFLICTING
```

------------------------------------------------------------------------

## 38. Timestamp

API:

``` text
ISO 8601
```

DB는 가능한 한 UTC로 저장하고 UI에서 사용자 시간대로 표시한다.

------------------------------------------------------------------------

## 39. JSON Field 사용 원칙

빠른 MVP를 위해 일부 유연한 데이터는 JSON을 허용한다.

적합:

``` text
operating_condition
signal_features
metadata
model_output
human_response
```

하지만 검색/관계/통계에 자주 쓰는 핵심 필드는 정규 Column으로 둔다.

------------------------------------------------------------------------

## 40. 원본 파일 저장

대용량 데이터:

``` text
Raw MAT
Processed NPY/Parquet
Model Artifact
PDF Documents
```

DB BLOB로 저장하지 않는 것을 기본으로 한다.

``` text
File/Object Storage
       +
DB Reference
```

구조를 사용한다.

------------------------------------------------------------------------

## 41. Audit / Reproducibility

진단 결과마다 최소 다음을 추적한다.

``` text
measurement_id
model_id + version
knowledge_pack_id + version
retrieved evidence
LangGraph run_id
timestamps
human feedback
final report
```

이 정보가 있어야 동일 진단을 재현하거나 결과가 바뀐 이유를 추적할 수
있다.

------------------------------------------------------------------------

## 42. 보안 기본

MVP라도 다음은 적용한다.

-   API Key를 Frontend에 넣지 않음
-   `.env` 사용
-   Secret을 Git에 commit하지 않음
-   업로드 파일 형식/크기 검증
-   SQL parameterization/ORM 사용
-   오류 응답에서 내부 경로/Secret 제거
-   CORS 범위 제한
-   외부 Tool의 변경 작업은 승인 구조 고려

------------------------------------------------------------------------

## 43. 개발용 Mock API

Frontend와 Backend를 병렬 개발할 수 있도록 Mock Data를 제공한다.

예:

``` text
fixtures/
├── equipment.json
├── measurement_normal.json
├── measurement_abnormal.json
├── agent_events_retry.json
├── evidence.json
└── final_report.json
```

Mock은 UI 개발용이며 최종 Demo에서는 실제 Backend 실행을 사용한다.

------------------------------------------------------------------------

## 44. API 테스트

최소 테스트:

``` text
Equipment list
Measurement retrieval
ML analysis
Agent run creation
Agent run state
SSE event
Evidence retrieval
Final report
Human response
Error response
```

FastAPI 자동 API 문서에서도 확인 가능하도록 Schema를 정의한다.

------------------------------------------------------------------------

## 45. MVP에서 먼저 구현할 DB

모든 Table을 처음부터 만들지 않는다.

P0:

``` text
equipment
measurement
ml_model
sensor_analysis
diagnosis_run
agent_event
knowledge_pack
knowledge_document
evidence
```

P1:

``` text
diagnosis_candidate
inspection_step
recommended_action
human_request
human_feedback
```

P2:

``` text
maintenance_history
장기 Memory 관련 구조
```

------------------------------------------------------------------------

## 46. API 개발 순서

``` text
STEP 1
Pydantic 공통 Schema

STEP 2
Equipment / Measurement API

STEP 3
ML Analysis API

STEP 4
Agent Run 생성/조회

STEP 5
Agent Event 저장

STEP 6
SSE

STEP 7
Evidence API

STEP 8
Report API

STEP 9
Human-in-the-loop API

STEP 10
Knowledge 관리/평가 API
```

------------------------------------------------------------------------

## 47. 완료 기준

-   [ ] `/api/v1` 구조 확정
-   [ ] Pydantic Request/Response Schema
-   [ ] Equipment API
-   [ ] Measurement API
-   [ ] Analysis API
-   [ ] Agent Run 생성
-   [ ] Agent Run 조회
-   [ ] Agent Event 저장
-   [ ] SSE 연결
-   [ ] Evidence 조회
-   [ ] Final Report 조회
-   [ ] DB Migration
-   [ ] 모델/Knowledge Pack Version 추적
-   [ ] Error Schema
-   [ ] API 테스트
-   [ ] Frontend와 실제 E2E 연결

------------------------------------------------------------------------

## 48. 다음 문서

다음 산출물:

**`08_EVALUATION_TEST_PLAN.md`**

다음 영역을 통합 평가한다.

-   Data pipeline
-   ML/DL
-   RAG Retrieval
-   RAG Grounding
-   LangGraph branching
-   Agent Tool execution
-   Citation correctness
-   Human-in-the-loop
-   API
-   UI/Event synchronization
-   End-to-End scenario
-   사용자 테스트
-   Demo/competition acceptance test
