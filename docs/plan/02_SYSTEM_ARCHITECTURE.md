# AI Smart Factory Agent Office

## 02. System Architecture

**문서 버전:** v0.1\
**선행 문서:** `01_PROJECT_OVERVIEW.md`\
**목적:** AI Smart Factory Agent Office의 전체 시스템 구성, 서비스 경계,
데이터 흐름, Agent State, 저장소 및 배포 구조를 정의한다.

------------------------------------------------------------------------

## 1. 아키텍처 설계 원칙

본 프로젝트는 다음 원칙을 따른다.

1.  **End-to-End Workflow 우선**
    -   센서 데이터 입력부터 진단·조치·시각화까지 하나의 흐름이 실제로
        동작해야 한다.
2.  **ML/DL과 RAG의 역할 분리**
    -   ML/DL은 센서 패턴을 분석한다.
    -   RAG는 기술적 근거와 진단 지식을 검색한다.
3.  **LangGraph가 전체 판단 흐름을 관리**
    -   State, 조건분기, 재검색, Tool 실행 및 Human-in-the-loop를
        관리한다.
4.  **데이터셋과 RAG 자료는 교체 가능**
    -   Paderborn은 첫 Reference Dataset이며 시스템 자체는 특정
        데이터셋에 종속시키지 않는다.
5.  **UI는 실제 Backend State를 시각화**
    -   Pixel/Isometric Agent Office를 단순 애니메이션으로 구현하지
        않는다.
6.  **MVP는 단순하게, 확장은 모듈식으로**
    -   초기에는 하나의 LangGraph Workflow를 사용하고 필요할 때
        Multi-Agent로 확장한다.

------------------------------------------------------------------------

## 2. 전체 논리 아키텍처

``` text
┌─────────────────────────────────────────────────────────────┐
│                       FRONTEND                              │
│                                                             │
│  Smart Factory Dashboard                                   │
│  Pixel / Isometric Agent Office                            │
│  LangGraph Live View                                       │
│  Diagnosis / Evidence / Maintenance Report                 │
└────────────────────────────┬────────────────────────────────┘
                             │ REST / SSE(WebSocket optional)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION BACKEND                      │
│                         FastAPI                             │
│                                                             │
│  API Router                                                 │
│  Equipment Service                                          │
│  Sensor/Data Service                                        │
│  Diagnosis Service                                          │
│  Report Service                                             │
│  Agent Event Stream                                         │
└───────────────┬───────────────────┬─────────────────────────┘
                │                   │
                ▼                   ▼
┌─────────────────────────┐   ┌──────────────────────────────┐
│     ML/DL SERVICE       │   │   LANGGRAPH AGENT ENGINE   │
│                         │   │                              │
│ Data Adapter            │   │ State                       │
│ Preprocessing           │   │ Nodes                       │
│ Feature Extraction      │   │ Conditional Edges           │
│ Model Inference         │   │ Tool Calls                  │
│ Model Evaluation        │   │ Retry / Verification        │
└─────────────┬───────────┘   └──────────────┬───────────────┘
              │                              │
              │                              ▼
              │                    ┌─────────────────────────┐
              │                    │      RAG SERVICE        │
              │                    │                         │
              │                    │ Parser / Chunker        │
              │                    │ Embedding               │
              │                    │ Retriever               │
              │                    │ Reranking(optional)     │
              │                    │ Citation/Evidence       │
              │                    └────────────┬────────────┘
              │                                 │
              ▼                                 ▼
┌─────────────────────────┐       ┌──────────────────────────┐
│   APPLICATION STORAGE   │       │       VECTOR DB          │
│                         │       │                          │
│ Equipment               │       │ Technical Documents      │
│ Sensor Summary          │       │ Failure Cases            │
│ Diagnosis History       │       │ Maintenance Guides       │
│ Agent Run / Events      │       │ Dataset Documentation    │
│ Feedback / Memory       │       │ Metadata                 │
└─────────────────────────┘       └──────────────────────────┘
```

------------------------------------------------------------------------

## 3. 권장 기술 스택

초기 MVP의 권장 구성이다. 구현 과정에서 변경할 수 있다.

  영역              초기 권장
  ----------------- -----------------------------------------------
  Frontend          Next.js + React
  UI                Tailwind CSS
  Agent Office      SVG/Canvas 기반 Pixel 또는 Isometric UI
  Backend API       Python FastAPI
  ML/DL             Python, scikit-learn, PyTorch 또는 TensorFlow
  Data Processing   pandas, NumPy, SciPy
  RAG Framework     LangChain
  Agent Workflow    LangGraph
  LLM               OpenAI GPT API
  Embedding         OpenAI Embedding 또는 호환 Embedding
  Vector DB         Chroma 또는 Qdrant
  Application DB    PostgreSQL
  Prototype DB      SQLite 허용
  File Storage      Local → 배포 단계 Object Storage
  Event Update      SSE 우선, 필요 시 WebSocket
  Container         Docker
  Source Control    GitHub

초기 MVP에서는 기술 종류를 늘리기보다 전체 흐름 완성을 우선한다.

------------------------------------------------------------------------

## 4. 시스템 주요 모듈

### 4.1 Data Source Layer

초기에는 Paderborn Bearing DataCenter 데이터를 사용한다.

역할: - 원본 데이터 로딩 - Dataset metadata 읽기 - 실험 조건 연결 -
Label 연결 - 향후 다른 설비 데이터로 교체

데이터 소스마다 `Data Adapter`를 구현하여 내부 표준 형식으로 변환한다.

------------------------------------------------------------------------

### 4.2 Data Adapter

외부 데이터 형식을 시스템 내부 표준 Sensor Record로 변환한다.

예시:

``` json
{
  "equipment_id": "bearing_test_rig_01",
  "timestamp": "relative-or-measured-time",
  "sensor_type": "vibration",
  "axis": "x",
  "sampling_rate": 64000,
  "values": [],
  "operating_condition": {
    "rpm": 1500,
    "load": null,
    "temperature": null
  },
  "label": {
    "state": "normal_or_fault",
    "fault_type": null
  },
  "source": "paderborn"
}
```

실제 Paderborn 필드 구조 확인 후 `03_DATA_ML_DL_DESIGN.md`에서 수정한다.

------------------------------------------------------------------------

## 5. ML/DL Layer

ML/DL은 **센서 데이터 기반 상태 분석**에 집중한다.

### 입력

-   진동
-   모터 전류
-   운전 조건
-   추후 온도·RPM·토크 등

### 처리

``` text
Raw Signal
   ↓
Cleaning
   ↓
Windowing
   ↓
Feature Extraction / Signal Transform
   ↓
ML or DL Model
   ↓
Standard Analysis Result
```

### 표준 출력

``` json
{
  "equipment_id": "bearing_test_rig_01",
  "status": "abnormal",
  "anomaly_score": 0.87,
  "predicted_fault": "bearing_damage_candidate",
  "confidence": 0.82,
  "features": {
    "rms": 0.0,
    "peak": 0.0,
    "kurtosis": 0.0
  },
  "model_id": "model_v1",
  "analysis_time": "..."
}
```

핵심은 어떤 ML/DL 모델을 사용하더라도 Agent에는 가능한 한 동일한 형태의
결과를 전달하는 것이다.

------------------------------------------------------------------------

## 6. RAG Architecture

RAG는 ML/DL이 발견한 상태를 **기술적으로 해석할 근거**를 제공한다.

### Document Ingestion

``` text
PDF / HTML / Technical Document
        ↓
Parser
        ↓
Cleaning
        ↓
Chunking
        ↓
Metadata Enrichment
        ↓
Embedding
        ↓
Vector DB
```

### 초기 Metadata

``` json
{
  "document_id": "...",
  "title": "...",
  "source": "...",
  "document_type": "manual|diagnostic_guide|failure_case|dataset_doc",
  "equipment_type": "bearing",
  "component": "bearing",
  "fault_type": "...",
  "manufacturer": "...",
  "page": 10,
  "section": "...",
  "url_or_origin": "..."
}
```

### Retrieval

Agent가 다음 정보를 이용해 Query를 생성한다.

-   ML/DL 분석 결과
-   센서 특징
-   예상 고장 유형
-   설비 유형
-   운전 조건
-   이전 진단 결과

RAG 응답은 단순 답변이 아니라 다음 구조를 목표로 한다.

``` json
{
  "evidence": [
    {
      "content": "...",
      "document": "...",
      "page": 10,
      "score": 0.0
    }
  ],
  "retrieval_query": "...",
  "evidence_count": 3
}
```

------------------------------------------------------------------------

## 7. LangGraph Agent Architecture

LangGraph가 시스템의 핵심 Orchestrator 역할을 한다.

### 기본 State

``` python
AgentState = {
    "run_id": str,
    "equipment_id": str,
    "sensor_input": dict,
    "analysis_result": dict,
    "retrieval_query": str,
    "rag_evidence": list,
    "diagnosis_candidates": list,
    "evidence_sufficient": bool,
    "inspection_plan": list,
    "recommended_actions": list,
    "human_feedback": dict | None,
    "current_node": str,
    "status": str,
    "errors": list
}
```

실제 TypedDict/Pydantic 정의는 구현 단계에서 확정한다.

### 기본 Node

``` text
load_data
    ↓
run_detection
    ↓
check_abnormal
    ↓
build_rag_query
    ↓
retrieve_knowledge
    ↓
diagnose
    ↓
verify_evidence
    ↓
inspection_plan
    ↓
recommend_action
    ↓
generate_report
    ↓
save_result
```

### Conditional Edge

#### 정상

``` text
run_detection
    ↓
NORMAL
    ↓
save_normal_state
    ↓
END
```

#### 이상

``` text
run_detection
    ↓
ABNORMAL
    ↓
retrieve_knowledge
```

#### 근거 부족

``` text
verify_evidence
    ↓
INSUFFICIENT
    ↓
refine_query
    ↓
retrieve_knowledge
```

#### 근거 충분

``` text
verify_evidence
    ↓
SUFFICIENT
    ↓
inspection_plan
```

재검색 횟수에는 상한을 둬 무한 Loop를 방지한다.

------------------------------------------------------------------------

## 8. Tool 설계

Agent가 직접 사용할 Tool은 초기에는 최소화한다.

### `run_ml_inference`

센서 데이터를 ML/DL 모델에 전달하고 분석 결과를 반환한다.

### `search_technical_docs`

Vector DB에서 관련 기술문서를 검색한다.

### `get_equipment_history`

해당 설비의 이전 이상·진단·정비 기록을 조회한다.

### `save_diagnosis`

최종 진단 결과를 저장한다.

### `request_human_check`

정보 부족 또는 위험한 판단이 필요한 경우 사용자 확인을 요청한다.

MVP에서는 모든 Tool을 구현할 필요는 없으며 핵심 E2E에 필요한 Tool부터
개발한다.

------------------------------------------------------------------------

## 9. Application DB

초기 주요 Entity:

### Equipment

``` text
id
name
equipment_type
manufacturer
model
installation_date
metadata
created_at
```

### SensorAnalysis

``` text
id
equipment_id
timestamp
model_id
status
anomaly_score
predicted_fault
confidence
features_json
```

### DiagnosisRun

``` text
id
equipment_id
analysis_id
status
started_at
completed_at
final_diagnosis
inspection_plan
recommended_actions
```

### AgentEvent

``` text
id
run_id
node
event_type
message
payload
created_at
```

### Evidence

``` text
id
run_id
document_id
page
chunk_id
score
content_reference
```

### MaintenanceHistory

``` text
id
equipment_id
diagnosis_run_id
action
result
performed_at
feedback
```

------------------------------------------------------------------------

## 10. Frontend Architecture

Frontend은 세 가지 관점을 하나의 서비스에서 제공한다.

### A. Smart Factory Dashboard

운영자 중심 화면.

``` text
설비 목록
현재 상태
센서 Trend
Anomaly Score
최근 Alert
최근 Agent 진단
```

### B. AI Smart Factory Agent Office

시각적 Agent Workflow.

예:

``` text
[Machine]
   │ abnormal event
   ▼
[Detection Agent Desk]
   │
   ▼
[RAG Agent Desk]
   │
   ▼
[Diagnosis Agent Desk]
   │
   ▼
[Maintenance Agent Desk]
```

현재 LangGraph Node에 따라 Agent 위치, 상태, 작업 표시가 변경된다.

### C. LangGraph Live View

기술 시연 및 개발자/심사 관점.

``` text
Current Node
State Summary
Tool Calls
RAG Retrieval
Evidence
Conditional Edge
Retry Count
Final Result
```

------------------------------------------------------------------------

## 11. Backend → UI 실시간 상태 연동

Agent Office의 핵심은 Backend와 실제 연결하는 것이다.

LangGraph Node가 변경될 때 Event를 생성한다.

예:

``` json
{
  "run_id": "run_001",
  "event": "node_started",
  "node": "retrieve_knowledge",
  "agent": "rag_agent",
  "message": "기술문서를 검색하고 있습니다."
}
```

Frontend는 Event Stream을 받아 UI를 갱신한다.

초기 구현은 **SSE(Server-Sent Events)**를 우선 검토한다.

이 구조를 사용하면:

``` text
LangGraph State Change
        ↓
Agent Event
        ↓
FastAPI SSE
        ↓
Frontend
        ↓
Dashboard + Agent Office + Live View
```

세 화면이 동일한 실제 상태를 공유할 수 있다.

------------------------------------------------------------------------

## 12. API 초안

### Equipment

``` text
GET  /api/equipment
GET  /api/equipment/{id}
```

### Sensor / Analysis

``` text
POST /api/analysis/run
GET  /api/analysis/{id}
```

### Agent

``` text
POST /api/agent/diagnose
GET  /api/agent/runs/{run_id}
GET  /api/agent/runs/{run_id}/events
```

### RAG

``` text
POST /api/rag/search
GET  /api/rag/documents
POST /api/rag/documents
```

### Report

``` text
GET /api/reports/{run_id}
```

실제 Request/Response Schema는 `07_API_DB_SPEC.md`에서 확정한다.

------------------------------------------------------------------------

## 13. 프로젝트 디렉터리 초안

``` text
ai-smart-factory-agent-office/
│
├── docs/
│   ├── 01_PROJECT_OVERVIEW.md
│   ├── 02_SYSTEM_ARCHITECTURE.md
│   └── ...
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── features/
│   └── lib/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── core/
│   └── tests/
│
├── ml/
│   ├── data/
│   ├── adapters/
│   ├── preprocessing/
│   ├── features/
│   ├── models/
│   ├── training/
│   └── inference/
│
├── rag/
│   ├── documents/
│   ├── ingestion/
│   ├── chunking/
│   ├── retrieval/
│   └── evaluation/
│
├── agent/
│   ├── state/
│   ├── nodes/
│   ├── tools/
│   ├── graphs/
│   └── prompts/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample/
│
├── scripts/
├── tests/
├── docker/
└── README.md
```

구현 시 Python package 경계와 Backend 통합 여부에 따라 단순화할 수 있다.

------------------------------------------------------------------------

## 14. 데이터셋 교체 구조

Paderborn을 제거하더라도 Agent와 UI를 최대한 수정하지 않는 것이 목표다.

``` text
Paderborn
    ↓
PaderbornAdapter
    ↓
Standard Sensor Format
```

향후:

``` text
New Factory Dataset
    ↓
NewDatasetAdapter
    ↓
Standard Sensor Format
```

ML/DL 모델 역시 표준 `AnalysisResult`를 반환한다.

따라서 Agent는 데이터 출처가 아니라 다음 결과를 중심으로 동작한다.

``` text
status
anomaly_score
predicted_fault
confidence
features
operating_condition
```

------------------------------------------------------------------------

## 15. RAG Knowledge Base 교체 구조

RAG 역시 특정 문서에 종속시키지 않는다.

``` text
Domain Knowledge Pack
├── dataset_docs
├── equipment_docs
├── diagnostic_guides
├── maintenance_guides
└── failure_cases
```

새로운 설비를 적용할 때 해당 설비용 `Domain Knowledge Pack`을 구축한다.

예:

``` text
knowledge/
├── bearing/
├── motor/
├── pump/
└── agitator/
```

------------------------------------------------------------------------

## 16. Long-term Memory

고도화 단계에서 다음 정보를 설비별 Memory로 활용한다.

``` text
Equipment Profile
       +
Previous Sensor Analysis
       +
Previous Diagnosis
       +
Inspection Result
       +
Maintenance Result
       +
Human Feedback
```

이를 통해 Agent가 과거 상태를 참고하여 현재 이상을 분석할 수 있다.

------------------------------------------------------------------------

## 17. Multimodal 확장

향후 다음 입력을 Agent Context에 추가한다.

``` text
Sensor Data
     +
Equipment Photo
     +
Control Panel Photo
     +
Bearing / Component Photo
     +
Maintenance Document Image
```

Multimodal 결과 역시 LangGraph State에 저장하고 Diagnosis Node에서 함께
사용한다.

------------------------------------------------------------------------

## 18. 배포 구조 초안

``` text
User Browser
     ↓
Frontend
     ↓
FastAPI Backend
     ├── LangGraph Agent
     ├── ML/DL Inference
     ├── RAG Retriever
     ├── Application DB
     └── Vector DB
```

MVP에서는 단일 서버/컨테이너 중심으로 단순하게 시작한다.

고도화 시:

``` text
Frontend
Backend API
ML Inference Service
Agent Service
Vector DB
PostgreSQL
Object Storage
```

로 분리할 수 있다.

------------------------------------------------------------------------

## 19. 안전한 진단 표현

본 시스템은 실제 산업설비의 최종 고장 판정을 자동 확정하는 시스템으로
표현하지 않는다.

출력은 다음과 같이 설계한다.

``` text
이상 탐지
→ 가능한 원인 후보
→ 기술문서 근거
→ 추가 확인이 필요한 항목
→ 권장 점검 순서
→ 권장 조치
```

최종 정비 의사결정은 현장 전문가가 수행할 수 있도록 Human-in-the-loop
구조를 지원한다.

------------------------------------------------------------------------

## 20. MVP 개발 순서

``` text
STEP 1  데이터 로딩
STEP 2  전처리/특징 추출
STEP 3  ML/DL Baseline
STEP 4  추론 API
STEP 5  RAG 문서 수집/정제
STEP 6  Vector DB / Retrieval
STEP 7  LangGraph State + Nodes
STEP 8  ML/DL + RAG 결합
STEP 9  진단/조치 결과
STEP 10 Dashboard
STEP 11 Agent Office
STEP 12 LangGraph Live View
STEP 13 평가/테스트
STEP 14 배포
```

단, Codex 실행용 STEP 문서는 별도로 작성한다. 이 순서를 그대로 한 번에
Codex에 전달하지 않는다.

------------------------------------------------------------------------

## 21. 핵심 End-to-End 시나리오

최초 MVP에서 반드시 성공시킬 시나리오는 하나다.

``` text
1. 사용자가 테스트 설비/센서 데이터를 선택한다.
2. ML/DL 모델이 데이터를 분석한다.
3. 이상 상태를 탐지한다.
4. LangGraph가 진단 Workflow를 시작한다.
5. RAG가 관련 기술문서를 검색한다.
6. Agent가 ML/DL 결과와 기술 근거를 결합한다.
7. 근거가 부족하면 추가 검색한다.
8. 가능한 원인 후보를 생성한다.
9. 추가 점검 항목과 조치안을 생성한다.
10. 출처가 포함된 진단 Report를 생성한다.
11. Agent Office에서 전체 처리 과정을 시각화한다.
```

이 시나리오가 완성되기 전에는 부가기능 확장을 최소화한다.

------------------------------------------------------------------------

## 22. 다음 문서

다음 산출물:

**`03_DATA_ML_DL_DESIGN.md`**

다음 내용을 구체화한다.

-   Paderborn 데이터 실제 구조 확인
-   사용할 Sensor Channel
-   Label 정의
-   Train / Validation / Test 전략
-   Windowing
-   Signal preprocessing
-   Feature engineering
-   ML Baseline
-   DL Baseline
-   평가 Metric
-   Agent로 전달할 표준 AnalysisResult
-   새로운 데이터셋 교체 Interface
