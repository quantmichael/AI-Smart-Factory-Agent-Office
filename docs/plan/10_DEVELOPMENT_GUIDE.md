# AI Smart Factory Agent Office

## 10. Development Guide

**문서 버전:** v0.1\
**프로젝트:** AI Smart Factory Agent Office\
**목적:** 확정된 설계를 기준으로 작은 STEP 단위의 구현·검증 원칙을
정리한다.

------------------------------------------------------------------------

# 1. 개발 원칙

개발은 설계 문서를 기준으로 단계별로 진행하고, 각 단계의 결과를 검증한다.

우선순위:

``` text
1. 설계 준수
2. End-to-End 동작
3. Interface 안정성
4. 테스트 가능성
5. 코드 명확성
6. 확장성
7. 시각적 완성도
```

복잡한 기술을 사용하는 것 자체가 목표가 아니다.

------------------------------------------------------------------------

# 2. 프로젝트 한 줄 정의

> 제조설비 센서 데이터를 ML/DL로 분석하고, 기술문서 RAG를 근거로
> LangGraph AI Agent가 이상 원인 후보를 검토하고 점검·조치안을 생성하며,
> 전체 실행 과정을 AI Smart Factory Agent Office에서 실시간으로
> 시각화하는 서비스.

------------------------------------------------------------------------

# 3. 핵심 End-to-End Flow

``` text
Sensor Dataset
    ↓
Data Adapter
    ↓
Preprocessing / Feature Extraction
    ↓
ML/DL Detection
    ↓
Standard Analysis Result
    ↓
LangGraph
    ↓
RAG Retrieval
    ↓
Diagnosis Candidate
    ↓
Evidence Verification
    ↓
Conditional Branch / Retry
    ↓
Inspection Plan
    ↓
Recommended Action
    ↓
Final Report
    ↓
Agent Event
    ↓
AI Smart Factory Agent Office
```

이 E2E 흐름을 기준으로 구현 우선순위를 판단한다.

------------------------------------------------------------------------

# 4. 반드시 읽어야 할 설계 문서

작업을 시작하기 전에 다음 문서를 읽고 구조를 이해한다.

``` text
docs/
└── plan/
    ├── 01_PROJECT_OVERVIEW.md
    ├── 02_SYSTEM_ARCHITECTURE.md
    ├── 03_DATA_ML_DL_DESIGN.md
    ├── 04_RAG_DESIGN.md
    ├── 05_LANGGRAPH_AGENT_DESIGN.md
    ├── 06_AGENT_OFFICE_UI.md
    ├── 07_API_DB_SPEC.md
    ├── 08_EVALUATION_TEST_PLAN.md
    ├── 09_TEAM_ROLES.md
    └── 10_DEVELOPMENT_GUIDE.md
```

위 경로는 현재 Repository의 설계 문서 위치를 따른다.

------------------------------------------------------------------------

# 5. 문서 우선순위

설계 충돌이 발견되면 임의로 결정하지 않는다.

우선순위:

``` text
현재 STEP 작업 계획
    ↓
10_DEVELOPMENT_GUIDE.md
    ↓
세부 설계 문서 02~08
    ↓
01_PROJECT_OVERVIEW.md
```

명백한 충돌이나 구현 불가능성이 있으면 변경 전 보고한다.

------------------------------------------------------------------------

# 6. Architecture 불변 원칙

다음 원칙은 특별한 승인 없이 변경하지 않는다.

### A. Data Source 분리

``` text
Dataset
→ Data Adapter
→ Standard Internal Format
```

Paderborn 전용 로직을 전체 시스템에 퍼뜨리지 않는다.

### B. ML/DL 표준 출력

모든 모델은 `Standard Analysis Result`로 변환한다.

### C. RAG 분리

``` text
Document Ingestion
Retrieval
Evidence
```

을 Agent Logic과 분리한다.

### D. LangGraph가 Orchestrator

Workflow 분기와 상태 관리는 LangGraph 계층이 담당한다.

### E. UI는 Backend State를 반영

Agent Office 애니메이션을 가짜 Timer 기반으로 진행시키지 않는다.

### F. RAG Citation은 실제 Evidence Metadata 기반

LLM이 Citation을 임의 생성하지 않는다.

### G. 안전 관련 자동 실행 금지

MVP에서는 실제 설비 정지나 위험한 정비 명령을 자동 실행하지 않는다.

------------------------------------------------------------------------

# 7. Reference Domain

초기 Reference Domain:

``` text
Rolling Bearing Condition Monitoring
```

초기 Reference Dataset:

``` text
Paderborn University Bearing DataCenter
```

단, 전체 Architecture는 특정 Dataset에 종속되지 않아야 한다.

향후:

``` text
Motor
Pump
Fan
Gearbox
Mixer
Conveyor
```

등으로 교체/확장 가능해야 한다.

------------------------------------------------------------------------

# 8. Reference Knowledge Base

초기 Knowledge Pack:

``` text
bearing_v1
```

구성 개념:

``` text
Paderborn dataset/test documentation
Paderborn damage Fact Sheets
bearing vibration diagnostic documents
bearing failure analysis documents
inspection / maintenance technical documents
```

RAG 문서 자체를 코드에 하드코딩하지 않는다.

------------------------------------------------------------------------

# 9. 기술 Stack

초기 기준:

### Frontend

``` text
Next.js
React
TypeScript
Tailwind CSS
```

### Backend

``` text
Python
FastAPI
Pydantic
```

### ML/DL

``` text
pandas
NumPy
SciPy
scikit-learn
PyTorch 또는 TensorFlow
```

DL Framework는 실제 기존 환경과 팀 선택을 확인한 뒤 하나를 사용한다.

### Agent

``` text
LangChain
LangGraph
OpenAI GPT API
```

### RAG

``` text
Embedding
Vector DB
Chroma 또는 Qdrant
```

초기 MVP에서는 하나만 선택한다.

### Application DB

``` text
SQLite → Prototype
PostgreSQL → Final
```

기존 Repository 또는 배포환경이 이미 결정되어 있으면 먼저 분석하고
불필요한 변경을 하지 않는다.

------------------------------------------------------------------------

# 10. Repository 작업 전 필수 행동

각 STEP 시작 전:

``` text
1. Repository tree 확인
2. 기존 README 확인
3. Dependency 확인
4. 환경설정 확인
5. 관련 Test 확인
6. 관련 설계 문서 확인
7. 변경 범위 제안
```

기존 코드가 있을 경우 전체를 다시 만들지 않는다.

------------------------------------------------------------------------

# 11. 기존 코드 우선

기존 구현이 있으면:

``` text
Analyze
→ Reuse
→ Refactor only when necessary
→ Extend
```

순서를 따른다.

다음 행동은 피한다.

``` text
기존 기능 전체 삭제
무조건 새 Framework 도입
불필요한 대규모 Directory 재구성
동작하는 코드를 이유 없이 재작성
```

------------------------------------------------------------------------

# 12. STEP 단위 개발

한 번에 전체 프로젝트를 구현하지 않는다.

단계별 작업은 다음 범위로 나눈다.

``` text
STEP 01 — Project scaffold
STEP 02 — Data Adapter 및 데이터·문서 준비
STEP 03 — Data profiling
STEP 04 — ML Baseline
STEP 05 — ML API
STEP 06 — RAG ingestion
STEP 07 — RAG retrieval
STEP 08 — LangGraph core
STEP 09 — Agent actions 및 HITL
STEP 10 — Agent API 및 SSE
STEP 11 — Agent Office UI
STEP 12 — Long-term memory
STEP 13 — Multimodal inspection
STEP 14 — E2E integration
STEP 15 — Evaluation 및 deploy
```

STEP 번호와 범위는 개발 진행에 따라 조정할 수 있지만, 한 STEP은 가능한
한 하나의 명확한 목표를 가진다.

------------------------------------------------------------------------

# 13. STEP 실행 규칙

각 STEP은 다음 순서로 진행한다.

``` text
READ
→ PLAN
→ IMPLEMENT
→ TEST
→ REPORT
```

### READ

관련 파일과 문서를 읽는다.

### PLAN

수정할 파일과 구현 전략을 짧게 정리한다.

### IMPLEMENT

해당 STEP 범위만 구현한다.

### TEST

실행 가능한 테스트를 수행한다.

### REPORT

변경 내용과 검증 결과를 정리한다.

------------------------------------------------------------------------

# 14. STEP 범위를 넘지 않는다

예:

STEP이 `Data Adapter`라면:

허용:

``` text
adapter interface
paderborn adapter
unit test
sample loading
```

금지:

``` text
RAG 전체 구현
Frontend redesign
LangGraph 완성
DB 전면 변경
```

다음 STEP의 기반이 꼭 필요한 경우 최소한만 만들고 이유를 기록한다.

------------------------------------------------------------------------

# 15. Interface Contract

다음 Interface는 프로젝트의 핵심 계약이다.

``` text
SensorDatasetAdapter
Measurement
AnalysisResult
EvidenceObject
DiagnosisCandidate
AgentState
AgentEvent
FinalReport
```

내부 구현은 변경 가능하지만 Interface 변경은 신중해야 한다.

Interface 변경 시:

``` text
변경 이유
영향 Module
Migration 필요 여부
Test 결과
```

를 보고한다.

------------------------------------------------------------------------

# 16. SensorDatasetAdapter

개념:

``` python
class SensorDatasetAdapter:
    def list_measurements(self):
        ...

    def load_measurement(self, measurement_id):
        ...

    def get_metadata(self, measurement_id):
        ...
```

Paderborn 전용 파일 파싱은 Adapter 내부로 제한한다.

------------------------------------------------------------------------

# 17. AnalysisResult

최소 개념:

``` json
{
  "analysis_id": "...",
  "measurement_id": "...",
  "model_id": "...",
  "status": "normal | abnormal",
  "predicted_class": "...",
  "confidence": null,
  "anomaly_score": null,
  "signal_features": {},
  "metadata": {}
}
```

실제 Schema는 Pydantic으로 정의한다.

------------------------------------------------------------------------

# 18. EvidenceObject

최소 개념:

``` json
{
  "evidence_id": "...",
  "document_id": "...",
  "chunk_id": "...",
  "title": "...",
  "publisher": "...",
  "document_type": "...",
  "source_tier": 1,
  "page": null,
  "section": null,
  "content": "...",
  "retrieval_score": null,
  "metadata": {}
}
```

------------------------------------------------------------------------

# 19. AgentEvent

최소 개념:

``` json
{
  "event_id": "...",
  "run_id": "...",
  "sequence": 1,
  "event_type": "node_started",
  "node": "run_detection",
  "agent_role": "detection_agent",
  "message": "...",
  "payload": {},
  "created_at": "..."
}
```

Frontend Agent Office는 이 Event를 기준으로 상태를 변경한다.

------------------------------------------------------------------------

# 20. LangGraph 기본 Path

반드시 구현할 핵심:

``` text
START
  ↓
load_sensor_data
  ↓
run_detection
  ↓
check_detection_result
  ├── NORMAL → normal_report → END
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
          ├── SUFFICIENT
          │      ↓
          │   inspection
          │      ↓
          │   action
          │      ↓
          │   report
          │      ↓
          │     END
          │
          ├── PARTIAL → refine_query → retrieve
          │
          └── INSUFFICIENT → limited/human path
```

------------------------------------------------------------------------

# 21. LangGraph 구현 원칙

-   단순 조건을 LLM에 맡기지 않는다.
-   Node는 Single Responsibility를 따른다.
-   Structured Output을 우선한다.
-   Retry Loop에는 최대 횟수가 있어야 한다.
-   State 필드를 암묵적으로 삭제하지 않는다.
-   오류는 State/Error Handler에서 추적한다.
-   Human-in-the-loop 확장을 막는 구조를 만들지 않는다.

------------------------------------------------------------------------

# 22. RAG 구현 원칙

RAG는 단순 PDF Chatbot이 아니다.

``` text
AnalysisResult
→ Query Context
→ Retrieval
→ Evidence
→ Diagnosis
→ Verification
```

을 구현한다.

검색 목적:

``` text
dataset_context
diagnostic
inspection
```

을 분리할 수 있도록 설계한다.

------------------------------------------------------------------------

# 23. RAG에서 금지할 것

``` text
검색하지 않은 문서를 Citation으로 생성
없는 Page 생성
Knowledge Base에 없는 사실을 확정적으로 생성
retrieval 결과 없이 maintenance 절차를 지어냄
```

근거가 없으면:

``` text
INSUFFICIENT
```

상태를 반환한다.

------------------------------------------------------------------------

# 24. ML/DL 구현 원칙

처음부터 복잡한 DL 모델을 만들지 않는다.

순서:

``` text
Data Profiling
→ Preprocessing
→ Feature Extraction
→ Random Forest Baseline
→ Evaluation
→ 1D CNN
→ Compare
```

필요 시 이후:

``` text
Isolation Forest
Autoencoder
```

를 추가한다.

------------------------------------------------------------------------

# 25. ML Data Leakage 방지

Train/Test Split에서:

``` text
same bearing
same measurement windows
```

가 섞이는지 확인한다.

가능하면:

``` text
Group Split by Bearing ID
```

를 사용한다.

Split 방식은 코드와 평가 결과에 기록한다.

------------------------------------------------------------------------

# 26. 임의 Dataset Schema 금지

실제 Paderborn 파일을 확인하기 전:

``` text
sampling rate
MAT variable name
channel name
exact array structure
```

를 추측해서 하드코딩하지 않는다.

먼저 Data Profiling을 수행하고 실제 구조를 기준으로 Adapter를 구현한다.

------------------------------------------------------------------------

# 27. Frontend 구현 원칙

UI는 다음 정보를 우선한다.

``` text
Equipment Status
Sensor Signal
ML Result
Current Agent
Current LangGraph Node
Evidence
Diagnosis
Inspection
Recommended Action
Timeline
```

고급 Pixel/Isometric 그래픽은 E2E가 동작한 후 고도화한다.

------------------------------------------------------------------------

# 28. Agent Office 규칙

다음은 금지한다.

``` text
setTimeout만으로 Agent 진행 연출
Backend와 무관한 가짜 Agent 이동
고정된 가짜 Evidence
고정된 가짜 Diagnosis
```

허용:

``` text
Backend Event
→ Frontend State
→ Animation
```

------------------------------------------------------------------------

# 29. SSE 우선

초기 실시간 상태는 SSE를 사용한다.

``` text
FastAPI
→ AgentEvent
→ SSE
→ React
```

WebSocket은 양방향 실시간 요구가 명확해질 때만 검토한다.

------------------------------------------------------------------------

# 30. API 규칙

Base:

``` text
/api/v1
```

핵심:

``` text
GET  /equipment
GET  /measurements
POST /analysis
POST /agent/runs
GET  /agent/runs/{run_id}
GET  /agent/runs/{run_id}/events/stream
GET  /agent/runs/{run_id}/evidence
GET  /agent/runs/{run_id}/report
```

실제 Route naming은 기존 프로젝트와 충돌이 없는지 확인한다.

------------------------------------------------------------------------

# 31. Database 원칙

MVP에서는 지나친 정규화보다 추적 가능성을 우선한다.

반드시 추적:

``` text
measurement
model version
knowledge pack version
agent run
evidence
events
final report
```

Raw Signal, PDF, Model Artifact를 무조건 DB BLOB로 넣지 않는다.

------------------------------------------------------------------------

# 32. Version Tracking

진단 결과에서 다음을 알 수 있어야 한다.

``` text
어떤 Measurement?
어떤 Model?
어떤 Knowledge Pack?
어떤 Evidence?
어떤 Agent Run?
언제 실행?
```

------------------------------------------------------------------------

# 33. Coding Rule

-   명확한 이름 사용
-   작은 함수
-   중복 최소화
-   Type Hint 적극 사용
-   Pydantic Schema 사용
-   환경변수와 설정 분리
-   Magic Number 최소화
-   Domain Logic과 Framework Code 분리
-   Public Function에 필요한 Docstring
-   과도한 추상화 금지

------------------------------------------------------------------------

# 34. Configuration

환경별 값은 설정으로 분리한다.

예:

``` text
OPENAI_API_KEY
DATABASE_URL
VECTOR_DB_PATH / URL
DATASET_ROOT
KNOWLEDGE_BASE_ROOT
MODEL_ROOT
LOG_LEVEL
```

Secret을 코드나 Git에 저장하지 않는다.

------------------------------------------------------------------------

# 35. Dependency Rule

새 Dependency 추가 전 확인:

``` text
기존 Library로 가능한가?
유지보수되는 Library인가?
프로젝트에 꼭 필요한가?
팀이 이해할 수 있는가?
```

불필요한 Framework 추가를 피한다.

------------------------------------------------------------------------

# 36. Test Rule

코드 변경에는 가능한 범위에서 테스트를 동반한다.

최소:

``` text
Unit Test
Schema Test
Integration Test
```

핵심 Path는 E2E Test를 추가한다.

------------------------------------------------------------------------

# 37. 필수 Graph Test

``` text
Normal Path
Abnormal + Sufficient
Abnormal + Partial + Retry
Insufficient
Retry Limit
Tool Error
```

------------------------------------------------------------------------

# 38. 필수 RAG Test

``` text
Expected document retrieval
Metadata filter
Empty retrieval
Citation mapping
Unsupported claim
```

------------------------------------------------------------------------

# 39. 필수 API Test

``` text
Valid request
Invalid request
Unknown ID
Agent run
Event sequence
Report retrieval
```

------------------------------------------------------------------------

# 40. 완료 보고 형식

각 STEP 완료 후 다음 형식으로 보고한다.

``` text
## STEP Result

### Implemented
- ...

### Changed Files
- ...

### Tests
- command:
- result:

### Validation
- ...

### Known Issues
- ...

### Next STEP Ready
YES / NO
```

------------------------------------------------------------------------

# 41. 테스트 실패 시

테스트가 실패하면 성공했다고 보고하지 않는다.

다음 중 하나로 명확히 구분한다.

``` text
PASS
FAIL
BLOCKED
NOT TESTED
```

`NOT TESTED`는 `PASS`가 아니다.

------------------------------------------------------------------------

# 42. 실행하지 못한 명령

환경 문제로 Test/Build를 실행할 수 없으면:

``` text
실행하지 못한 이유
필요한 환경
재실행할 명령
예상 결과
```

를 남긴다.

------------------------------------------------------------------------

# 43. 오류 수정 범위

현재 STEP에서 발견된 기존 오류가 작업을 막으면 최소 범위로 수정한다.

관련 없는 오류는:

``` text
Known Issue
```

로 기록하고 현재 STEP을 불필요하게 확장하지 않는다.

------------------------------------------------------------------------

# 44. Git Rule

변경은 가능하면 논리적인 작은 단위로 나누어 관리한다.

권장 Commit 개념:

``` text
feat(data): add paderborn dataset adapter
test(data): add adapter validation tests
feat(rag): add evidence metadata schema
```

실제 Commit 수행 여부는 팀 운영 방침에 따른다.

------------------------------------------------------------------------

# 45. AI 생성 코드의 설명 가능성

팀원이 코드의 다음 내용을 설명할 수 있어야 한다.

``` text
왜 이 구조인가?
입력은 무엇인가?
출력은 무엇인가?
실패하면 어떻게 되는가?
어떻게 테스트하는가?
다른 Module과 어떻게 연결되는가?
```

설명할 수 없을 정도로 복잡한 코드는 단순화한다.

------------------------------------------------------------------------

# 46. 안전 / 진단 표현

본 프로젝트는 제조설비 의사결정 지원 시스템이다.

최종 결과는:

``` text
Possible Cause
Evidence
Inspection Recommendation
Recommended Action
Limitation
```

구조를 사용한다.

근거가 부족한 상황에서 확정적인 고장 판정을 생성하지 않는다.

------------------------------------------------------------------------

# 47. Logging

최소:

``` text
run_id
node
tool
duration
error
evidence IDs
workflow route
```

를 추적할 수 있도록 한다.

Secret, API Key, 불필요한 원본 민감정보는 Log에 기록하지 않는다.

------------------------------------------------------------------------

# 48. Performance 원칙

초기에는 극단적 최적화를 하지 않는다.

우선:

``` text
Correct
→ Observable
→ Testable
→ Fast enough
```

순서로 개발한다.

------------------------------------------------------------------------

# 49. Mock 사용 규칙

UI 병렬 개발을 위해 Mock은 허용한다.

단:

``` text
Mock Data
≠
Final Demo Backend Result
```

최종 E2E Demo에서는 실제 ML/RAG/LangGraph Backend 실행을 사용한다.

------------------------------------------------------------------------

# 50. MVP 우선순위

## P0

``` text
Data Adapter
Data Profiling
ML Baseline
Analysis API
RAG Ingestion
RAG Retrieval
Evidence Object
LangGraph Basic
Conditional Branch
Diagnosis
Evidence Verification
Retry
Final Report
Agent Event
SSE
Basic Agent Office
E2E
```

## P1

``` text
1D CNN
Human-in-the-loop
RAG Evaluation UI
Advanced Agent Animation
PostgreSQL
Deployment hardening
```

## P2

``` text
Multimodal
Long-term Memory
Maintenance Workflow Automation
Multi-Agent
Advanced Isometric Graphics
```

------------------------------------------------------------------------

# 51. 구현 순서

권장 전체 순서:

``` text
01 Project Scaffold
02 Data Adapter
03 Data Profiling
04 ML Baseline
05 ML API
06 RAG Ingestion
07 RAG Retrieval
08 LangGraph Base
09 Agent Diagnosis
10 Evidence Verify / Retry
11 API / SSE
12 Agent Office Base
13 Backend / UI Sync
14 E2E
15 Evaluation / Deploy
```

------------------------------------------------------------------------

# 52. 다음 STEP 진입 조건

다음 STEP으로 넘어가기 전:

``` text
현재 STEP 목표 완료
관련 Test 통과
Interface 깨지지 않음
Known Issue 기록
실행 방법 확인
```

중 하나라도 핵심적으로 충족하지 못하면 다음 STEP을 억지로 진행하지
않는다.

------------------------------------------------------------------------

# 53. 개발 착수 전 확인

전체 개발에 앞서 현재 상태를 확인한다.

먼저:

``` text
1. Repository를 분석한다.
2. 현재 구현 상태를 요약한다.
3. 설계 문서와 기존 코드 차이를 찾는다.
4. Dependency와 실행 방법을 확인한다.
5. 위험요소/Blocker를 찾는다.
6. STEP 01 수행 준비 상태를 보고한다.
```

이후 합의된 STEP 범위에 따라 개발한다.

------------------------------------------------------------------------

# 54. 확인과 협의가 필요한 경우

다음 경우 임의 판단보다 팀 내 협의를 우선한다.

``` text
설계 문서 간 중대한 충돌
실제 Dataset 구조가 설계 예상과 다름
License 문제 가능성
기존 Architecture를 깨야 하는 상황
외부 유료 Service 추가 필요
보안상 위험한 변경
Interface의 Breaking Change
```

사소한 구현 세부사항은 합리적으로 결정하고 결과에 기록한다.

------------------------------------------------------------------------

# 55. 프로젝트 완료 정의

프로젝트가 완료되었다고 판단하려면 최소 다음 E2E가 실제로 동작해야 한다.

``` text
사용자가 Measurement 선택
        ↓
실제 센서 데이터 로드
        ↓
실제 ML/DL 모델 추론
        ↓
이상 판단
        ↓
실제 Vector DB RAG 검색
        ↓
실제 Evidence 확보
        ↓
LangGraph 진단
        ↓
근거 검증
        ↓
필요 시 재검색
        ↓
점검/조치안
        ↓
Citation 포함 Report
        ↓
Agent Event
        ↓
Agent Office 실시간 표현
```

------------------------------------------------------------------------

# 56. 최종 원칙

이 프로젝트의 목표는 기술 이름을 많이 넣는 것이 아니다.

최종 시스템은 다음 질문에 답할 수 있어야 한다.

> **"왜 이 Agent가 지금 이 행동을 했는가?"**

그 답은 항상 다음에서 찾을 수 있어야 한다.

``` text
Sensor Data
Model Result
Retrieved Evidence
Graph State
Conditional Route
Agent Event
Final Report
```

------------------------------------------------------------------------

# 57. 초기 개발 단계

첫 번째 개발 단계는 프로젝트 기본 구조를 확정하는 작업이다.

목표:

``` text
Repository 분석
프로젝트 기본 구조 확정
Backend/Frontend 실행 환경
공통 Config
공통 Schema
Test Framework
Health Check
최소 실행 가능한 Skeleton
```

STEP 01에서는 아직 ML/RAG/LangGraph 전체 기능을 구현하지 않는다.
