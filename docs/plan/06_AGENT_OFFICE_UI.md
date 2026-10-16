# AI Smart Factory Agent Office

## 06. Agent Office UI / UX Design

**문서 버전:** v0.1\
**선행 문서:** `01_PROJECT_OVERVIEW.md` \~
`05_LANGGRAPH_AGENT_DESIGN.md`\
**목적:** AI Smart Factory Agent Office의 화면 구조, Pixel/Isometric
Agent Office, Dashboard, LangGraph Live View 및 실제 Backend State 연동
규칙을 정의한다.

------------------------------------------------------------------------

## 1. UI 핵심 콘셉트

본 서비스의 UI는 일반적인 제조 대시보드만으로 구성하지 않는다.

핵심 콘셉트:

> **"AI Agent들이 실제 스마트팩토리 관제실에서 함께 설비 문제를 해결하는
> 모습을 보여주는 Agent Office"**

화면은 다음 세 가지 관점을 결합한다.

``` text
① Smart Factory Dashboard
② Pixel / Isometric Agent Office
③ LangGraph Live View
```

시각적 재미보다 더 중요한 원칙은 **화면이 실제 Backend Workflow를
반영해야 한다**는 것이다.

------------------------------------------------------------------------

## 2. UI 설계 원칙

1.  **Backend State First**
    -   화면 상태는 LangGraph Node/Event에서 파생한다.
2.  **Story of Diagnosis**
    -   사용자가 "무슨 일이 일어났고 AI가 지금 무엇을 하는지" 바로
        이해해야 한다.
3.  **Operational + Technical View**
    -   운영자에게는 간단한 상태, 개발자/심사자에게는 Agent 내부 흐름을
        제공한다.
4.  **Evidence Visible**
    -   AI의 진단에는 RAG 근거를 바로 확인할 수 있어야 한다.
5.  **Progressive Disclosure**
    -   처음부터 모든 기술 정보를 노출하지 않고 필요할 때 상세 정보를
        펼친다.
6.  **Demo Friendly**
    -   3분 내 시연에서도 AI Agent의 입력→판단→검색→분기→결과가 명확해야
        한다.

------------------------------------------------------------------------

## 3. Desktop 기준 전체 Layout

``` text
┌───────────────────────────────────────────────────────────────────────────┐
│ AI SMART FACTORY AGENT OFFICE          System ● Online     RUN #001      │
├───────────────┬───────────────────────────────────────┬───────────────────┤
│               │                                       │                   │
│ EQUIPMENT     │          AGENT OFFICE                 │   LIVE STATUS     │
│               │                                       │                   │
│ ● Bearing 01  │     [Sensor]      [RAG Library]       │ Current Node      │
│ ○ Bearing 02  │          \          /                 │ retrieve_knowledge│
│ ○ Motor 01    │        [Diagnosis Desk]               │                   │
│               │             |                         │ ML Result         │
│ Sensor        │      [Maintenance Desk]               │ ABNORMAL          │
│ Summary       │                                       │ Confidence 91%    │
│               │                                       │                   │
├───────────────┴───────────────────────────────────────┴───────────────────┤
│ Timeline / LangGraph Live Flow                                           │
│ Sensor → Detection → RAG → Diagnosis → Verify → Maintenance → Report    │
├───────────────────────────────────────────────────────────────────────────┤
│ Evidence / Diagnosis / Inspection / Action Tabs                          │
└───────────────────────────────────────────────────────────────────────────┘
```

------------------------------------------------------------------------

## 4. Information Architecture

주요 화면:

``` text
/
├── Dashboard / Agent Office
├── Equipment
│   └── Equipment Detail
├── Diagnosis Runs
│   └── Run Detail
├── Knowledge Base
├── Models
└── System / Evaluation
```

MVP에서는 첫 화면에 기능을 집중하고 나머지는 최소화한다.

------------------------------------------------------------------------

## 5. Main Dashboard

Main Dashboard에서 한눈에 보여줄 정보:

### 상단

-   프로젝트/서비스명
-   시스템 상태
-   현재 Run
-   Knowledge Pack Version
-   Model Version

### 좌측

-   설비 목록
-   설비별 정상/이상 상태
-   선택 설비 센서 Summary

### 중앙

-   Agent Office

### 우측

-   현재 Agent
-   현재 LangGraph Node
-   ML/DL 분석 상태
-   RAG 검색 상태
-   진단 진행 상태

### 하단

-   Workflow Timeline
-   Evidence
-   Diagnosis
-   Inspection
-   Action
-   Report

------------------------------------------------------------------------

## 6. Equipment Status

설비 상태 Enum:

``` text
NORMAL
ANALYZING
ABNORMAL
DIAGNOSING
NEEDS_CHECK
MAINTENANCE_RECOMMENDED
ERROR
```

표현은 색상만으로 구분하지 않는다.

함께 사용:

``` text
Icon
Text
Badge
Animation
```

접근성을 위해 상태 텍스트는 항상 표시한다.

------------------------------------------------------------------------

## 7. Agent Office 공간

초기 공간은 5개 Zone으로 구성한다.

``` text
┌──────────────────────────────┐
│  SENSOR / MACHINE ZONE       │
│                              │
│  DETECTION LAB               │
│                              │
│  RAG KNOWLEDGE LIBRARY       │
│                              │
│  DIAGNOSIS DESK              │
│                              │
│  MAINTENANCE DESK            │
└──────────────────────────────┘
```

------------------------------------------------------------------------

## 8. Agent 역할

### Sensor Agent

역할: - 센서 데이터 수집 - 측정 상태 확인

### Detection Agent

역할: - ML/DL 모델 실행 - 정상/이상 분석

### RAG Agent

역할: - 기술문서 검색 - Fact Sheet 검색 - 진단/정비 근거 수집

### Diagnosis Agent

역할: - ML/DL 결과와 RAG Evidence 결합 - 원인 후보 생성 - 근거 검증

### Maintenance Agent

역할: - 점검 순서 - 권장 조치 - 정비 검토

UI상의 Agent는 역할 표현이며 초기 Backend는 하나의 LangGraph Workflow를
사용한다.

------------------------------------------------------------------------

## 9. Agent Animation 원칙

Agent를 계속 움직이게 하지 않는다.

이벤트가 발생할 때만 의미 있는 상태 변화가 일어난다.

예:

``` text
node_started: run_detection
→ Detection Agent 활성화

node_completed: run_detection
→ 분석 결과 카드 표시

node_started: retrieve_knowledge
→ RAG Agent가 Knowledge Library에서 작업

node_completed: retrieve_knowledge
→ Evidence 문서 카드가 Diagnosis Desk로 이동

node_started: diagnose
→ Diagnosis Agent 활성화
```

------------------------------------------------------------------------

## 10. Event → UI Mapping

  Backend Event           Agent Office              Status Panel
  ----------------------- ------------------------- ----------------
  workflow_started        Office 활성화             RUNNING
  load_sensor_data        Sensor Agent 작업         Loading sensor
  run_detection           Detection Lab 활성화      ML analyzing
  detection_normal        설비 정상 표시            NORMAL
  detection_abnormal      설비 경고 표시            ABNORMAL
  retrieve_knowledge      RAG Library 활성화        Searching docs
  retrieval_completed     문서 카드 표시            Evidence N
  diagnose                Diagnosis Desk 활성화     Diagnosing
  evidence_partial        RAG Agent 재작업          RETRYING
  evidence_insufficient   사용자 확인 표시          NEEDS HUMAN
  build_inspection_plan   Maintenance Desk 활성화   Building plan
  generate_report         Report 생성               Finalizing
  workflow_completed      전체 안정화               COMPLETED
  workflow_error          해당 Zone 오류            ERROR

------------------------------------------------------------------------

## 11. Agent 상태

``` text
IDLE
WORKING
WAITING
RETRYING
NEEDS_HUMAN
DONE
ERROR
```

각 Agent 위에 작은 Status Badge를 표시한다.

예:

``` text
RAG AGENT
[RETRYING]
"추가 근거 검색 중..."
```

------------------------------------------------------------------------

## 12. Smart Factory Dashboard

Dashboard는 시각화보다 실제 분석정보 전달이 우선이다.

표시 항목:

``` text
Equipment
Status
Current RPM
Operating Condition
Anomaly Score
Predicted Class
ML Confidence
RMS
Kurtosis
Last Analysis
```

실제 데이터에 없는 값은 임의 생성하지 않는다.

------------------------------------------------------------------------

## 13. Sensor Visualization

초기:

-   Time waveform
-   Feature cards
-   필요 시 FFT chart

예:

``` text
Vibration
┌───────────────────────────┐
│ ~~~/\~~~~~/\/\~~~~/\~~~   │
└───────────────────────────┘

RMS       0.xx
Kurtosis  x.xx
Peak      x.xx
```

Chart는 분석 대상 Sample과 연결한다.

------------------------------------------------------------------------

## 14. ML Result Card

``` text
DETECTION RESULT

Status
ABNORMAL

Model
Random Forest v1

Task
Healthy vs Damaged

Prediction
Damaged

Model Confidence
91%

Key Features
RMS ...
Kurtosis ...
```

`Model Confidence`와 Agent의 진단 확신도를 혼동하지 않는다.

------------------------------------------------------------------------

## 15. LangGraph Live View

심사와 교육 측면에서 중요한 화면이다.

Graph:

``` text
[Load Data]
     ↓
[ML Detection]
     ↓
 [Abnormal]
     ↓
[RAG Search] ←────────┐
     ↓                │
 [Diagnose]           │
     ↓                │
[Verify Evidence]     │
     ↓                │
   PARTIAL ───────────┘
     ↓
[Inspection]
     ↓
[Action]
     ↓
[Report]
```

현재 Node를 강조하고 완료된 Node와 대기 Node를 구분한다.

------------------------------------------------------------------------

## 16. Live State Panel

표시 가능한 State:

``` text
run_id
equipment_id
workflow_status
current_node
detection status
retrieval retry count
evidence count
evidence status
diagnosis candidate count
human input required
```

원본 Prompt, 비공개 reasoning, chain-of-thought는 표시하지 않는다.

------------------------------------------------------------------------

## 17. Workflow Timeline

시간순 Event:

``` text
10:31:02  Sensor data loaded
10:31:03  ML inference started
10:31:04  Abnormal condition detected
10:31:05  RAG retrieval started
10:31:06  4 evidence chunks retrieved
10:31:07  Evidence status: PARTIAL
10:31:08  Retrieval query refined
10:31:09  3 additional chunks retrieved
10:31:10  Evidence status: SUFFICIENT
10:31:11  Inspection plan generated
10:31:12  Report completed
```

이 Timeline은 실제 AgentEvent를 기반으로 한다.

------------------------------------------------------------------------

## 18. RAG Evidence Panel

각 Evidence Card:

``` text
[EV-001]

Title
Bearing Damage and Failure Analysis

Publisher
...

Document Type
failure_analysis

Section / Page
...

Source Tier
2

Relevance
...

[View Evidence]
```

펼치면 실제 검색 Chunk를 확인한다.

------------------------------------------------------------------------

## 19. Evidence와 주장 연결

Diagnosis Candidate마다 근거 ID를 표시한다.

``` text
Candidate Cause A

Supporting Evidence
EV-001
EV-004

Contradicting Evidence
EV-007
```

Evidence를 클릭하면 해당 문서 Chunk를 연다.

------------------------------------------------------------------------

## 20. Diagnosis Panel

``` text
DIAGNOSIS

Detected Condition
Abnormal bearing vibration

Possible Causes

1. Candidate A
   Confidence: Medium
   Evidence: EV-001, EV-004
   Confirmation Required: Yes

2. Candidate B
   Confidence: Low
   Evidence: EV-006
```

`Possible Causes`라는 표현을 기본으로 한다.

------------------------------------------------------------------------

## 21. Inspection Plan

``` text
INSPECTION PLAN

STEP 1
Check ...

Purpose
Confirm Candidate A

Evidence
EV-004

STEP 2
Check ...

Purpose
Differentiate Candidate A/B

Evidence
EV-008
```

순서를 시각적으로 명확하게 표시한다.

------------------------------------------------------------------------

## 22. Recommended Action

조치 Level:

``` text
MONITOR
INSPECT
SCHEDULE_MAINTENANCE
EXPERT_REVIEW
SHUTDOWN_CHECK
```

실제 자동 정지 기능을 MVP에 구현하지 않는다.

예:

``` text
Recommended Action
SCHEDULE_MAINTENANCE

Reason
...

Supporting Evidence
EV-002
```

------------------------------------------------------------------------

## 23. Human-in-the-loop UI

Agent가 추가 정보가 필요할 때:

``` text
┌───────────────────────────────┐
│ ADDITIONAL CHECK REQUIRED     │
│                               │
│ 현재 근거만으로 원인 구분이   │
│ 충분하지 않습니다.            │
│                               │
│ 윤활 상태를 확인해 주세요.    │
│                               │
│ [Normal] [Low] [Unknown]      │
│                               │
│          [Continue Diagnosis] │
└───────────────────────────────┘
```

사용자 입력 후 Graph가 Resume된다.

------------------------------------------------------------------------

## 24. Demo Mode

공개 Dataset 기반 시연을 위해 `Demo Scenario`를 제공한다.

예:

``` text
Scenario 01
Healthy Bearing

Scenario 02
Damaged Bearing — Evidence Sufficient

Scenario 03
Damaged Bearing — RAG Retry

Scenario 04
Evidence Insufficient — Human Check
```

Demo Mode는 결과를 가짜로 만드는 기능이 아니다.

미리 선택된 실제 Sample과 정해진 Workflow 조건으로 재현성을 높이는
기능이다.

------------------------------------------------------------------------

## 25. Demo Story

가장 중요한 발표 Scenario:

``` text
1. 설비가 정상 작동 중
2. 새 센서 Sample 입력
3. Detection Agent 분석 시작
4. 이상 탐지
5. 설비 Warning
6. RAG Agent 기술문서 검색
7. Diagnosis Agent 분석
8. Evidence = PARTIAL
9. RAG Agent 재검색
10. Evidence = SUFFICIENT
11. Maintenance Agent 점검계획 생성
12. 근거 포함 조치안 생성
13. 최종 Report
```

이 흐름 하나만 완성되어도 LangGraph를 사용한 이유가 분명해진다.

------------------------------------------------------------------------

## 26. Responsive Strategy

### Desktop

전체 Agent Office + Dashboard + Live View.

### Tablet

Agent Office 중심 + 접이식 Side Panel.

### Mobile

운영 상태와 Report 중심.

Pixel/Isometric 전체 관제실을 모바일에 억지로 축소하지 않는다.

MVP 발표/심사 환경은 Desktop을 우선한다.

------------------------------------------------------------------------

## 27. Pixel / Isometric 구현 방식

초기 권장:

``` text
SVG
+
React Components
+
CSS Animation
```

장점:

-   상태 제어 용이
-   DOM 이벤트 연결 쉬움
-   Backend Event와 매핑 쉬움
-   Canvas보다 초기 구현 난이도가 낮음

고도화 시 Canvas/WebGL을 검토한다.

------------------------------------------------------------------------

## 28. Agent Office Asset 원칙

필요 Asset:

``` text
factory machine
sensor
monitor
agent character
knowledge library
diagnosis desk
maintenance desk
document card
warning icon
status light
```

Asset과 실제 데이터 의미를 분리한다.

예:

``` text
Agent animation = presentation
Agent State = backend truth
```

------------------------------------------------------------------------

## 29. UI Component 구조

``` text
components/
├── dashboard/
│   ├── EquipmentList
│   ├── EquipmentStatus
│   ├── SensorChart
│   └── MLResultCard
│
├── agent-office/
│   ├── AgentOffice
│   ├── FactoryMachine
│   ├── AgentCharacter
│   ├── DetectionLab
│   ├── KnowledgeLibrary
│   ├── DiagnosisDesk
│   └── MaintenanceDesk
│
├── graph/
│   ├── LangGraphView
│   ├── GraphNode
│   └── GraphEdge
│
├── evidence/
│   ├── EvidencePanel
│   └── EvidenceCard
│
├── diagnosis/
│   ├── DiagnosisPanel
│   ├── InspectionPlan
│   └── ActionPanel
│
└── timeline/
    └── AgentTimeline
```

------------------------------------------------------------------------

## 30. Frontend State

Frontend의 핵심 State:

``` typescript
type AgentRunUIState = {
  runId: string;
  workflowStatus: string;
  currentNode: string | null;
  activeAgent: string | null;
  equipmentStatus: string;
  analysisResult: AnalysisResult | null;
  evidenceStatus: string | null;
  evidenceCount: number;
  retryCount: number;
  diagnosisCandidates: DiagnosisCandidate[];
  inspectionPlan: InspectionStep[];
  recommendedActions: RecommendedAction[];
  events: AgentEvent[];
  humanInputRequired: boolean;
};
```

Backend State 전체를 Frontend가 그대로 복제할 필요는 없다.

------------------------------------------------------------------------

## 31. SSE 처리

``` text
Page Load
    ↓
Create Diagnosis Run
    ↓
Receive run_id
    ↓
Open SSE
    ↓
Receive Agent Events
    ↓
Reducer / Store
    ↓
Update Agent Office
```

연결 종료 조건:

``` text
COMPLETED
ERROR
USER_CANCELLED
```

------------------------------------------------------------------------

## 32. API → UI

초기 Endpoint:

``` text
POST /api/agent/diagnose
GET  /api/agent/runs/{run_id}
GET  /api/agent/runs/{run_id}/events/stream
GET  /api/reports/{run_id}
```

UI는 SSE Event와 최종 Run 조회를 함께 사용한다.

------------------------------------------------------------------------

## 33. 화면 상태 복구

페이지 새로고침 시:

``` text
run_id
  ↓
GET run
  ↓
현재 State 복원
  ↓
Event Stream 재연결
```

UI가 화면 새로고침만으로 진단 상태를 잃지 않도록 한다.

------------------------------------------------------------------------

## 34. Loading / Empty / Error

반드시 별도로 설계한다.

### Loading

``` text
센서 데이터 준비 중
ML 분석 중
기술문서 검색 중
```

### Empty

``` text
아직 진단 기록이 없습니다.
```

### Error

``` text
분석을 완료하지 못했습니다.
Error ID: ...
[Retry]
```

사용자에게 내부 Stack Trace를 보여주지 않는다.

------------------------------------------------------------------------

## 35. 접근성

-   상태를 색상만으로 표현하지 않음
-   충분한 텍스트 대비
-   키보드 접근
-   Chart에 숫자 Summary 병행
-   Animation 감소 설정 고려
-   중요 Warning은 Icon + Text 사용

------------------------------------------------------------------------

## 36. 화면 성능

Agent Office가 분석 자체를 느리게 만들면 안 된다.

원칙:

``` text
Backend Workflow
≠
UI Animation Duration
```

Backend Event를 받으면 즉시 State를 갱신하고 애니메이션은 짧게 표현한다.

------------------------------------------------------------------------

## 37. 발표용 3분 시연 구성

### 0:00--0:20

문제와 Agent Office 소개

### 0:20--0:40

설비 Sample 선택 및 센서 확인

### 0:40--1:00

ML/DL 이상 탐지

### 1:00--1:30

RAG 기술문서 검색

### 1:30--1:50

LangGraph 근거 검증 → PARTIAL → 재검색

### 1:50--2:20

진단 후보 + 점검계획 + 조치안

### 2:20--2:40

Citation 확인

### 2:40--3:00

Agent Office 전체 흐름 및 확장성 설명

------------------------------------------------------------------------

## 38. MVP UI 우선순위

### P0 --- 반드시 구현

-   Equipment/Sample 선택
-   Sensor Chart
-   ML Result
-   Agent Office 기본 화면
-   현재 Agent/Node 표시
-   LangGraph Flow
-   RAG Evidence
-   Diagnosis
-   Inspection/Action
-   Event Timeline
-   SSE 실시간 상태

### P1 --- 구현 권장

-   Agent 이동/작업 Animation
-   Human-in-the-loop
-   Report 상세
-   Knowledge Base 화면

### P2 --- 시간 여유 시

-   고급 Isometric 그래픽
-   설비 여러 대 동시 관제
-   Multimodal
-   Long-term Memory Timeline
-   고급 Chart

------------------------------------------------------------------------

## 39. MVP Wireframe

``` text
┌─────────────────────────────────────────────────────────────────────┐
│ AI SMART FACTORY AGENT OFFICE     RUNNING          Bearing #01     │
├──────────────┬────────────────────────────────┬─────────────────────┤
│ EQUIPMENT    │                                │ LIVE STATUS         │
│              │       AGENT OFFICE             │                     │
│ ● Bearing 01 │                                │ Node: RAG Search    │
│ ○ Bearing 02 │ [Machine]  [Knowledge Library] │ Agent: RAG Agent    │
│              │      \        /                │ Evidence: 4         │
│ STATUS       │    [Diagnosis]                 │ Retry: 1            │
│ ABNORMAL     │         |                      │                     │
│              │   [Maintenance]                │ ML: ABNORMAL        │
│ RMS ...      │                                │ Confidence: 91%     │
│ Kurtosis ... │                                │                     │
├──────────────┴────────────────────────────────┴─────────────────────┤
│ GRAPH                                                               │
│ Load ✓ → Detect ✓ → RAG ● → Diagnose → Verify → Action → Report   │
├───────────────────────────────────┬─────────────────────────────────┤
│ EVIDENCE                          │ DIAGNOSIS                       │
│ EV-001 ...                        │ Candidate A — Medium            │
│ EV-002 ...                        │ Candidate B — Low               │
├───────────────────────────────────┴─────────────────────────────────┤
│ TIMELINE                                                            │
│ 10:31:05 RAG retrieval started ...                                 │
└─────────────────────────────────────────────────────────────────────┘
```

------------------------------------------------------------------------

## 40. 디자인 단계의 성공 기준

UI가 예뻐 보이는 것만으로 성공으로 보지 않는다.

다음 질문에 모두 `YES`여야 한다.

-   사용자가 현재 설비 상태를 즉시 알 수 있는가?
-   ML/DL이 무엇을 판단했는지 보이는가?
-   Agent가 현재 무엇을 하고 있는지 보이는가?
-   RAG가 어떤 자료를 찾았는지 보이는가?
-   LangGraph의 분기가 보이는가?
-   재검색이 실제로 발생했음을 확인할 수 있는가?
-   진단 후보와 근거가 연결되는가?
-   점검 및 조치안의 근거를 확인할 수 있는가?
-   UI 상태가 실제 Backend State와 연결되어 있는가?

------------------------------------------------------------------------

## 41. 다음 문서

다음 산출물:

**`07_API_DB_SPEC.md`**

다음 내용을 정의한다.

-   REST API 상세 Request/Response
-   SSE Event Schema
-   Equipment / Measurement / Analysis / Diagnosis 데이터 모델
-   Agent Run
-   Evidence
-   Knowledge Document
-   Maintenance History
-   Human Feedback
-   Long-term Memory 확장
-   DB 관계
-   Error Response
-   API Versioning
