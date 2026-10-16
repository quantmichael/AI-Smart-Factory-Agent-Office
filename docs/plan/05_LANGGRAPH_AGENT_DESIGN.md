# AI Smart Factory Agent Office

## 05. LangGraph & AI Agent Design

**문서 버전:** v0.1\
**선행 문서:** `01_PROJECT_OVERVIEW.md`, `02_SYSTEM_ARCHITECTURE.md`,
`03_DATA_ML_DL_DESIGN.md`, `04_RAG_DESIGN.md`\
**목적:** ML/DL 분석, RAG 검색, 근거 검증, 진단, 점검 및 조치 과정을
LangGraph 기반 상태형 AI Agent Workflow로 정의한다.

------------------------------------------------------------------------

## 1. 핵심 설계 방향

본 프로젝트에서 LangGraph는 단순히 여러 LLM 호출을 순서대로 연결하는
도구가 아니다.

LangGraph는 전체 진단 프로세스의 **Orchestrator**다.

``` text
Sensor Data
    ↓
ML/DL
    ↓
LangGraph State
    ↓
RAG Retrieval
    ↓
Diagnosis
    ↓
Evidence Verification
    ↓
Conditional Branch
    ↓
Inspection / Action
    ↓
Report
```

LangGraph가 관리해야 할 핵심 요소:

-   현재 설비와 센서 Context
-   ML/DL 분석 결과
-   RAG 검색 결과
-   진단 후보
-   근거 충분성
-   재검색 여부
-   Human-in-the-loop
-   오류 및 재시도
-   최종 점검/조치
-   UI에 전달할 실행 Event

------------------------------------------------------------------------

## 2. Agent의 역할

AI Agent는 다음 세 가지를 구분하여 처리한다.

``` text
ML/DL
= Detect

RAG
= Retrieve / Ground

Agent
= Reason / Coordinate / Recommend
```

Agent가 ML/DL 모델을 대신하거나 기술문서를 임의로 만들어서는 안 된다.

------------------------------------------------------------------------

## 3. MVP Agent 구조

초기에는 여러 개의 독립 Agent를 운영하는 복잡한 Multi-Agent 구조보다
**하나의 LangGraph + 역할별 Node** 구조를 사용한다.

UI에서는 다음과 같은 Agent 캐릭터로 표현할 수 있다.

``` text
Sensor Agent
Detection Agent
RAG Agent
Diagnosis Agent
Maintenance Agent
```

그러나 Backend의 초기 구현은:

``` text
One LangGraph
+
Role-based Nodes
```

로 유지한다.

------------------------------------------------------------------------

## 4. 전체 Graph

``` text
START
  ↓
initialize_run
  ↓
load_sensor_data
  ↓
run_detection
  ↓
check_detection_result
  │
  ├── NORMAL
  │      ↓
  │   save_normal_state
  │      ↓
  │   generate_normal_report
  │      ↓
  │     END
  │
  └── ABNORMAL
         ↓
      build_rag_query
         ↓
      retrieve_knowledge
         ↓
      diagnose
         ↓
      verify_evidence
         │
         ├── SUFFICIENT
         │      ↓
         │   build_inspection_plan
         │      ↓
         │   recommend_action
         │      ↓
         │   generate_report
         │      ↓
         │   save_result
         │      ↓
         │     END
         │
         ├── PARTIAL
         │      ↓
         │   refine_query
         │      ↓
         │   retrieve_knowledge
         │
         ├── INSUFFICIENT
         │      ↓
         │   request_additional_information
         │      ↓
         │   human_or_system_input
         │      ↓
         │   update_context
         │      ↓
         │   build_rag_query
         │
         └── CONFLICTING
                ↓
             retrieve_counter_evidence
                ↓
             diagnose
```

------------------------------------------------------------------------

## 5. Agent State

초기 State 개념:

``` python
class AgentState(TypedDict):
    run_id: str
    equipment_id: str

    sensor_input: dict
    operating_condition: dict

    analysis_result: dict

    retrieval_queries: list[dict]
    rag_evidence: list[dict]

    diagnosis_candidates: list[dict]
    evidence_status: str

    inspection_plan: list[dict]
    recommended_actions: list[dict]

    retrieval_retry_count: int
    max_retrieval_retry: int

    human_input_required: bool
    human_request: dict | None
    human_feedback: dict | None

    current_node: str
    workflow_status: str

    final_report: dict | None
    errors: list[dict]
```

구현 시 Pydantic model 또는 TypedDict를 사용한다.

------------------------------------------------------------------------

## 6. State 설계 원칙

State에 모든 원본 센서 배열을 저장하지 않는다.

예:

``` text
Raw vibration array
→ 별도 Data/Storage 계층

Agent State
→ reference + summary + analysis result
```

Agent State에는 판단에 필요한 구조화된 정보만 저장한다.

------------------------------------------------------------------------

## 7. Node 공통 규칙

모든 Node는 가능한 한 다음 규칙을 따른다.

``` text
Input State
    ↓
Single Responsibility
    ↓
Structured Output
    ↓
State Update
    ↓
Agent Event Emit
```

Node가 여러 역할을 동시에 수행하지 않도록 한다.

------------------------------------------------------------------------

## 8. initialize_run

### 역할

새 진단 실행을 초기화한다.

### 입력

-   equipment_id
-   measurement/sample ID

### 출력

-   run_id
-   workflow_status = running
-   retry count 초기화

### Event

``` json
{
  "event": "workflow_started",
  "node": "initialize_run"
}
```

------------------------------------------------------------------------

## 9. load_sensor_data

### 역할

Data Adapter를 이용하여 분석 대상 센서 데이터를 읽는다.

### Tool

`load_sensor_measurement`

### State Update

``` text
sensor_input
operating_condition
```

### 실패

데이터가 없거나 형식 오류:

``` text
ERROR → handle_error
```

------------------------------------------------------------------------

## 10. run_detection

### 역할

ML/DL 모델을 실행한다.

### Tool

`run_ml_inference`

### 출력

`Standard Analysis Result`

예:

``` json
{
  "status": "abnormal",
  "predicted_class": "damaged",
  "confidence": 0.91,
  "anomaly_score": null,
  "signal_features": {
    "rms": 0.0,
    "kurtosis": 0.0
  }
}
```

------------------------------------------------------------------------

## 11. check_detection_result

LLM을 호출할 필요가 없는 deterministic node다.

``` python
if status == "normal":
    return "normal"
else:
    return "abnormal"
```

단순 조건은 LLM에게 판단시키지 않는다.

------------------------------------------------------------------------

## 12. build_rag_query

ML/DL 결과를 RAG 검색용 Context로 변환한다.

한 개의 거대한 Query보다 목적을 나눈다.

``` text
dataset_context
diagnostic
inspection
```

예:

``` json
[
  {
    "type": "dataset_context",
    "query": "..."
  },
  {
    "type": "diagnostic",
    "query": "..."
  },
  {
    "type": "inspection",
    "query": "..."
  }
]
```

------------------------------------------------------------------------

## 13. retrieve_knowledge

### Tool

`search_technical_docs`

### 역할

Vector DB에서 관련 Evidence를 검색한다.

### 입력

-   retrieval_queries
-   equipment type
-   component
-   predicted fault
-   source tier filter

### 출력

`Evidence Object[]`

Node 자체가 최종 진단을 생성하지 않는다.

------------------------------------------------------------------------

## 14. diagnose

### 역할

ML/DL 결과와 RAG Evidence를 결합하여 **진단 후보**를 만든다.

출력 예:

``` json
[
  {
    "candidate_id": "C01",
    "cause": "candidate cause",
    "confidence": "medium",
    "supporting_evidence_ids": ["EV01", "EV03"],
    "contradicting_evidence_ids": [],
    "reasoning_summary": "...",
    "requires_confirmation": true
  }
]
```

`confidence`는 LLM이 임의의 0.873 같은 정밀 확률을 생성하지 않는다.

초기에는:

``` text
low
medium
high
```

와 같은 설명적 등급을 사용한다.

ML 모델의 확률과 Agent의 진단 확신도를 구분한다.

------------------------------------------------------------------------

## 15. verify_evidence

진단 후보가 실제 검색 근거로 뒷받침되는지 검사한다.

출력:

``` text
SUFFICIENT
PARTIAL
INSUFFICIENT
CONFLICTING
```

평가 기준:

-   candidate마다 supporting evidence가 있는가?
-   Tier 1\~3 문서가 포함되는가?
-   Dataset Context와 기술문서가 연결되는가?
-   Inspection/Action에 근거가 있는가?
-   상충 문서가 존재하는가?
-   Citation Metadata가 유효한가?

------------------------------------------------------------------------

## 16. refine_query

`PARTIAL`일 때 실행한다.

이전 검색에서 부족한 부분만 다시 검색한다.

잘못된 예:

``` text
"bearing fault"
```

좋은 방향:

``` text
현재 확보되지 않은 항목:
- damage location과 vibration pattern 관계
- inspection procedure

→ 해당 항목 중심 Query 생성
```

------------------------------------------------------------------------

## 17. Retry 제한

``` python
max_retrieval_retry = 2
```

재검색 한도를 초과하면 Agent가 근거를 억지로 생성하지 않는다.

분기:

``` text
retry_count >= max
    ↓
request_additional_information
또는
generate_limited_report
```

------------------------------------------------------------------------

## 18. retrieve_counter_evidence

`CONFLICTING` 상태일 때 실행한다.

목적:

``` text
현재 가설을 확인하는 자료만 찾지 않고
다른 가능한 원인을 설명하는 자료도 검색
```

이를 통해 단순 confirmation bias를 줄인다.

------------------------------------------------------------------------

## 19. request_additional_information

현재 데이터만으로 판단하기 어려운 경우 사용한다.

예:

``` text
추가 진동 측정
다른 축 센서
모터 전류
온도
회전속도
육안 점검
윤활 상태
소음
설비 사진
```

초기 Paderborn MVP에서는 실제 센서 추가 수집 대신 준비된 추가
Sample/Metadata 또는 사용자 입력으로 시뮬레이션할 수 있다.

------------------------------------------------------------------------

## 20. Human-in-the-loop

Human-in-the-loop는 장식 기능이 아니다.

사용 시점:

``` text
근거 부족
상충 근거
고위험 조치
추가 현장정보 필요
최종 정비 승인
```

상태 예:

``` json
{
  "human_input_required": true,
  "human_request": {
    "type": "inspection_confirmation",
    "question": "...",
    "requested_fields": ["visual_condition", "lubrication_state"]
  }
}
```

Workflow는 사용자 입력을 기다렸다가 Resume할 수 있도록 확장한다.

------------------------------------------------------------------------

## 21. build_inspection_plan

원인 후보를 확인하기 위한 점검 순서를 생성한다.

예:

``` json
[
  {
    "step": 1,
    "action": "...",
    "purpose": "...",
    "related_candidate_ids": ["C01"],
    "evidence_ids": ["EV04"]
  }
]
```

근거 없는 점검 절차를 임의로 추가하지 않는다.

------------------------------------------------------------------------

## 22. recommend_action

점검 결과 또는 현재 근거를 바탕으로 조치 후보를 생성한다.

구분:

``` text
monitor
inspect
schedule_maintenance
expert_review
shutdown_check
```

실제 안전 관련 작업은 자동 실행하지 않는다.

MVP의 Agent는 **의사결정 지원** 역할로 제한한다.

------------------------------------------------------------------------

## 23. generate_report

최종 Report는 Structured Output으로 생성한다.

``` json
{
  "run_id": "...",
  "equipment_id": "...",
  "detected_status": "abnormal",
  "ml_result": {},
  "diagnosis_candidates": [],
  "evidence_status": "SUFFICIENT",
  "inspection_plan": [],
  "recommended_actions": [],
  "citations": [],
  "limitations": [],
  "generated_at": "..."
}
```

------------------------------------------------------------------------

## 24. Citation 규칙

Citation은 LLM이 생성한 문서명이 아니라 `Evidence Object` Metadata에서
만든다.

``` text
Evidence ID
Document ID
Title
Publisher
Page / Section
Source Origin
```

Report의 주장과 Evidence ID를 연결한다.

------------------------------------------------------------------------

## 25. Error Handling

공통 Error Type:

``` text
DATA_LOAD_ERROR
MODEL_INFERENCE_ERROR
RAG_SEARCH_ERROR
LLM_ERROR
INVALID_STRUCTURED_OUTPUT
DATABASE_ERROR
MAX_RETRY_EXCEEDED
```

Error State:

``` json
{
  "code": "RAG_SEARCH_ERROR",
  "node": "retrieve_knowledge",
  "message": "...",
  "retryable": true
}
```

------------------------------------------------------------------------

## 26. LLM Retry와 Workflow Retry 구분

둘을 혼동하지 않는다.

### LLM/API Retry

일시적 API 실패.

``` text
timeout
rate limit
temporary error
```

### Workflow Retry

근거가 부족해서 Query를 바꾸고 다시 검색.

``` text
PARTIAL evidence
→ refine_query
→ retrieve_knowledge
```

서로 별도의 retry counter를 둔다.

------------------------------------------------------------------------

## 27. Agent Tool 목록

MVP:

``` text
load_sensor_measurement
run_ml_inference
search_technical_docs
save_diagnosis
get_agent_run
```

고도화:

``` text
get_equipment_history
search_failure_cases
request_human_check
save_human_feedback
create_maintenance_ticket
send_alert
analyze_equipment_image
```

외부 시스템을 실제 변경하는 Tool은 승인 단계를 둔다.

------------------------------------------------------------------------

## 28. Long-term Memory 연결

MVP 이후:

``` text
get_equipment_history
        ↓
Previous Diagnosis
Previous Maintenance
Previous Anomaly
Human Feedback
        ↓
Diagnosis Context
```

Memory는 RAG 문서와 분리한다.

``` text
RAG
= domain knowledge

Long-term Memory
= this equipment's history
```

------------------------------------------------------------------------

## 29. Multimodal 연결

향후 사진 입력이 들어오면:

``` text
request_additional_information
        ↓
Equipment Image
        ↓
analyze_equipment_image
        ↓
visual_findings
        ↓
update_context
        ↓
diagnose
```

`visual_findings` 역시 State의 구조화된 필드로 저장한다.

------------------------------------------------------------------------

## 30. Agent Event

모든 주요 Node는 UI용 Event를 발행한다.

예:

``` json
{
  "run_id": "RUN-001",
  "sequence": 12,
  "event_type": "node_started",
  "node": "retrieve_knowledge",
  "agent_role": "rag_agent",
  "message": "관련 기술문서를 검색하고 있습니다.",
  "timestamp": "..."
}
```

완료:

``` json
{
  "event_type": "node_completed",
  "node": "retrieve_knowledge",
  "summary": {
    "evidence_count": 5
  }
}
```

------------------------------------------------------------------------

## 31. Backend State → Agent Office

매핑 예:

  LangGraph Node          UI Agent                 Office 표현
  ----------------------- ------------------------ -----------------------
  load_sensor_data        Sensor Agent             센서/설비 데이터 수집
  run_detection           Detection Agent          분석 모니터 활성화
  retrieve_knowledge      RAG Agent                문서실/검색 작업
  diagnose                Diagnosis Agent          진단 Desk 작업
  verify_evidence         Diagnosis Agent          근거 검증 표시
  build_inspection_plan   Maintenance Agent        점검계획 작성
  recommend_action        Maintenance Agent        조치안 생성
  generate_report         Report/Diagnosis Agent   최종 보고서 생성

따라서 UI의 캐릭터 움직임은 실제 Node Event를 기반으로 한다.

------------------------------------------------------------------------

## 32. UI 상태 예

``` text
IDLE
RUNNING
WAITING
RETRYING
NEEDS_HUMAN
COMPLETED
ERROR
```

색상이나 애니메이션은 UI 설계 문서에서 정의한다.

------------------------------------------------------------------------

## 33. SSE Event Stream

초기 실시간 연결은 SSE를 우선한다.

``` text
LangGraph Node
    ↓
Event Store
    ↓
FastAPI SSE Endpoint
    ↓
React Client
    ↓
Agent Office Update
```

Endpoint 예:

``` text
GET /api/agent/runs/{run_id}/events/stream
```

WebSocket이 반드시 필요한 기능이 생기면 이후 변경한다.

------------------------------------------------------------------------

## 34. Checkpoint / Resume

LangGraph의 상태형 장점을 활용한다.

필요 상황:

``` text
Human input 대기
일시적 오류
페이지 새로고침
진단 과정 재현
```

최종 구현에서는 `run_id`를 기준으로 State/Checkpoint를 복구할 수 있도록
설계한다.

MVP에서는 먼저 실행 Event와 최종 결과 저장부터 구현하고 이후
Checkpointer를 붙일 수 있다.

------------------------------------------------------------------------

## 35. Observability

Agent가 왜 그런 결과를 냈는지 추적할 수 있어야 한다.

기록:

``` text
run_id
node
start/end
duration
tool
retrieval query
retrieved evidence IDs
structured output
conditional edge
retry
error
token/cost(optional)
```

단, 사용자에게 내부 chain-of-thought를 표시하지 않는다.

UI에는 **결정에 필요한 실행 상태와 근거 요약**만 보여준다.

------------------------------------------------------------------------

## 36. Deterministic vs LLM Node

LLM이 필요 없는 작업에는 LLM을 쓰지 않는다.

### Deterministic

``` text
check_detection_result
retry_count check
schema validation
DB save
event emission
metadata filtering
```

### LLM 활용

``` text
build_rag_query
diagnose
refine_query
inspection plan synthesis
report narrative
```

이 원칙은 비용, 속도, 재현성을 개선한다.

------------------------------------------------------------------------

## 37. Structured Output

LLM 결과는 가능한 한 JSON Schema/Pydantic으로 강제한다.

예:

``` text
DiagnosisCandidate
InspectionStep
RecommendedAction
EvidenceVerification
```

자연어 전체를 State의 핵심 데이터로 사용하지 않는다.

------------------------------------------------------------------------

## 38. Prompt 관리

Prompt를 코드에 길게 하드코딩하지 않는다.

``` text
agent/
└── prompts/
    ├── query_builder.md
    ├── diagnosis.md
    ├── evidence_verifier.md
    ├── inspection_plan.md
    └── report.md
```

Prompt 변경 이력을 Git에서 관리한다.

------------------------------------------------------------------------

## 39. 프로젝트 파일 구조

``` text
agent/
├── state/
│   ├── agent_state.py
│   └── schemas.py
├── nodes/
│   ├── initialize.py
│   ├── detection.py
│   ├── retrieval.py
│   ├── diagnosis.py
│   ├── verification.py
│   ├── inspection.py
│   ├── action.py
│   └── report.py
├── edges/
│   └── routing.py
├── tools/
│   ├── ml_tool.py
│   ├── rag_tool.py
│   ├── equipment_tool.py
│   └── storage_tool.py
├── prompts/
├── events/
├── graphs/
│   └── diagnosis_graph.py
└── tests/
```

실제 Codex 구현 시 현재 Repository 구조에 맞춰 조정한다.

------------------------------------------------------------------------

## 40. 핵심 Demo Scenario

심사/발표용 핵심 시나리오:

``` text
① 사용자가 Bearing Sample 선택
        ↓
② Sensor Agent 데이터 수집
        ↓
③ Detection Agent ML/DL 분석
        ↓
④ "Abnormal" 탐지
        ↓
⑤ RAG Agent 기술문서 검색
        ↓
⑥ Diagnosis Agent 원인 후보 생성
        ↓
⑦ 근거 부족
        ↓
⑧ Query 수정 후 재검색
        ↓
⑨ 근거 확보
        ↓
⑩ Maintenance Agent 점검안 생성
        ↓
⑪ 최종 조치안 + Citation
        ↓
⑫ Agent Office 전체 Workflow 완료
```

이 시나리오에서는 LangGraph의 **조건분기와 재검색**이 눈에 보이도록
한다.

------------------------------------------------------------------------

## 41. MVP 완료 기준

-   [ ] AgentState Schema 구현
-   [ ] Graph 생성
-   [ ] Sensor Data Node
-   [ ] ML/DL Tool 연결
-   [ ] 정상/이상 Conditional Edge
-   [ ] Query Builder
-   [ ] RAG Retrieval Node
-   [ ] Diagnosis Node
-   [ ] Evidence Verification
-   [ ] PARTIAL → 재검색 Edge
-   [ ] Retry 제한
-   [ ] Inspection Plan
-   [ ] Recommended Action
-   [ ] Citation 기반 Report
-   [ ] Agent Event 저장
-   [ ] SSE 연결
-   [ ] Frontend에서 현재 Node 확인
-   [ ] End-to-End Demo 성공

------------------------------------------------------------------------

## 42. 고도화 순서

MVP 이후 권장:

``` text
1. Checkpoint / Resume
2. Human-in-the-loop
3. Equipment Long-term Memory
4. Multimodal
5. Alert / Maintenance Workflow Automation
6. RAG Evaluation 고도화
7. Agent Observability
8. 필요 시 Multi-Agent
```

Multi-Agent는 마지막에 검토한다.

------------------------------------------------------------------------

## 43. 설계의 핵심

본 프로젝트에서 가장 중요한 것은 Agent의 숫자가 아니다.

``` text
센서에서 실제 데이터가 들어오고
        ↓
ML/DL이 분석하고
        ↓
RAG가 근거를 찾고
        ↓
LangGraph가 근거를 검증하고 분기하고
        ↓
Agent가 점검과 조치를 제시하며
        ↓
그 과정이 UI에서 실제 상태로 보이는 것
```

이 흐름 자체가 **AI Smart Factory Agent Office**의 핵심이다.

------------------------------------------------------------------------

## 44. 다음 문서

다음 산출물:

**`06_AGENT_OFFICE_UI.md`**

다음 내용을 정의한다.

-   전체 화면 Information Architecture
-   Smart Factory Dashboard
-   Pixel / Isometric Agent Office
-   설비 상태 표현
-   Agent 캐릭터/역할
-   LangGraph Live View
-   RAG Evidence Panel
-   Diagnosis Report
-   Human-in-the-loop UI
-   Event → Animation mapping
-   Demo Mode
-   Desktop 화면 기준 Wireframe
-   실제 Backend State와 UI의 연결 규칙
