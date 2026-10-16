# AI Smart Factory Agent Office

## 09. Team Roles & Collaboration Plan

**문서 버전:** v0.1\
**선행 문서:** `01_PROJECT_OVERVIEW.md` \~ `08_EVALUATION_TEST_PLAN.md`\
**팀 구성:** 5인\
**목적:** 빠른 MVP 구축과 팀 전체의 AI Native 학습, 개인별 포트폴리오
성과를 동시에 확보할 수 있도록 역할과 협업 방식을 정의한다.

------------------------------------------------------------------------

## 1. 팀 운영 원칙

본 프로젝트는 기능을 5등분하여 각자 자기 부분만 개발하는 방식으로
진행하지 않는다.

기본 전략은 다음과 같다.

``` text
전체 구조 공동 이해
      ↓
Reference MVP 확보
      ↓
공통 Mini Project
      ↓
전문 Module 담당
      ↓
Cross Review
      ↓
통합
      ↓
E2E 검증
```

핵심 원칙:

1.  모든 팀원이 전체 End-to-End 구조를 이해한다.
2.  모든 팀원이 최소 한 번은 ML/DL → RAG → LangGraph 흐름을 직접
    실행한다.
3.  이후 각자 전문 Module의 Owner가 된다.
4.  Module Owner는 구현뿐 아니라 테스트와 문서화까지 책임진다.
5.  특정 한 사람만 이해하는 Black Box를 만들지 않는다.
6.  개인 기여가 GitHub와 발표자료에서 명확하게 남도록 한다.

------------------------------------------------------------------------

## 2. 현재 팀 상황을 반영한 운영

현재 팀은 5명이며 구성원별 세부 역할은 아직 최종 확정하지 않는다.

팀 상황:

``` text
5인 Final Project Team
├── 취업 준비 구성원 3명
└── 창업/서비스 관점 구성원 2명
```

역할 배정 시 특히 취업 준비 구성원에게는 이력서·면접·포트폴리오에서 설명
가능한 기술적 Ownership을 부여한다.

------------------------------------------------------------------------

## 3. 초기 Reference MVP 전략

프로젝트 초반에는 전체 방향과 인터페이스를 빠르게 확인하기 위해
**Reference MVP**를 먼저 만든다.

Reference MVP 범위:

``` text
Paderborn Sample
      ↓
Feature Extraction
      ↓
Baseline ML
      ↓
AnalysisResult
      ↓
RAG Retrieval
      ↓
LangGraph
      ↓
Diagnosis
      ↓
Simple Web UI
```

목적은 완성품을 대신 만드는 것이 아니라:

-   전체 구조 검증
-   기술 연결부 확인
-   팀원에게 실행 가능한 기준 제공
-   Module Interface 확정
-   개발 작업 단위 분리

이다.

------------------------------------------------------------------------

## 4. 공통 Mini Project

전문 역할 배정 전에 팀원 모두가 동일한 작은 실습을 수행한다.

### 공통 실습 목표

``` text
① Paderborn Sample 1개 읽기
② RMS/Kurtosis 등 Feature 확인
③ 준비된 Baseline Model로 추론
④ 기술문서 1~2개 Vector DB에 넣기
⑤ 질문으로 Chunk 검색
⑥ LangGraph Node 3~4개 연결
⑦ ML 결과 → RAG → 간단한 진단 결과 생성
```

완성도보다 **전체 흐름을 직접 경험하는 것**이 목적이다.

------------------------------------------------------------------------

## 5. 모든 팀원이 알아야 할 공통 기술

최소 공통 영역:

``` text
Git / GitHub
Python
FastAPI 기본
ML/DL Pipeline 개념
RAG 기본 구조
Embedding / Vector DB
LangChain 기본
LangGraph State / Node / Edge
Structured Output
REST API
Agent Tool 개념
E2E Workflow
```

Frontend 담당도 RAG/LangGraph가 어떻게 동작하는지 이해해야 하고, ML
담당도 최종 UI에서 자신의 결과가 어떻게 사용되는지 알아야 한다.

------------------------------------------------------------------------

# ROLE MODEL

## 6. 권장 역할 구조

세부 담당자는 팀 회의 후 확정한다.

### Role A --- Architecture / Integration / Web

주요 책임:

-   전체 Architecture
-   Reference MVP
-   Frontend/Backend 연결
-   공통 Interface
-   Integration
-   단계별 개발 작업 구조
-   최종 E2E 관리

주요 산출물:

``` text
System Architecture
API Contract
Reference Implementation
Integration Build
Deployment Build
```

------------------------------------------------------------------------

## 7. Role B --- Data & ML/DL Owner

주요 책임:

-   Paderborn Data Adapter
-   Data Profiling
-   Signal preprocessing
-   Feature engineering
-   Train/Validation/Test split
-   Random Forest baseline
-   1D CNN
-   Anomaly Detection 확장
-   Model evaluation
-   Inference Interface

Portfolio 핵심:

``` text
Industrial Time-Series
Signal Processing
ML/DL
Anomaly Detection
Model Evaluation
FastAPI Integration
```

------------------------------------------------------------------------

## 8. Role C --- RAG / Knowledge Engineering Owner

주요 책임:

-   기술문서 수집
-   Document Manifest
-   Parser
-   Chunking
-   Metadata
-   Embedding
-   Vector DB
-   Retrieval
-   Citation
-   RAG Evaluation

Portfolio 핵심:

``` text
RAG Pipeline
Technical Document Processing
Vector Search
Metadata Filtering
Retrieval Evaluation
Grounded Generation
```

------------------------------------------------------------------------

## 9. Role D --- LangGraph / AI Agent Owner

주요 책임:

-   AgentState
-   Node
-   Conditional Edge
-   Tool Calling
-   RAG retry
-   Evidence verification
-   Human-in-the-loop
-   Structured Output
-   Checkpoint 확장
-   Agent Event

Portfolio 핵심:

``` text
LangGraph
AI Agent
Stateful Workflow
Tool Calling
Conditional Routing
Human-in-the-loop
Agent Observability
```

------------------------------------------------------------------------

## 10. Role E --- Agent Office / QA / Deployment Owner

주요 책임:

-   Agent Office UI
-   LangGraph Live View
-   Sensor Visualization
-   SSE Event 연결
-   Evidence/Diagnosis UI
-   E2E Test
-   사용자 테스트
-   Deployment
-   Demo Scenario

Portfolio 핵심:

``` text
React / Next.js
Real-time UI
SSE
AI Workflow Visualization
E2E Testing
Deployment
AI UX
```

------------------------------------------------------------------------

## 11. 역할은 경계가 아니라 Ownership

예를 들어 RAG 담당자만 RAG 코드를 볼 수 있는 구조는 금지한다.

``` text
Owner
= 최종 책임자

Reviewer
= 다른 Module 담당자

Team
= 전체 구조 이해
```

각 핵심 Module은 최소:

``` text
1 Owner
+
1 Reviewer
```

를 둔다.

------------------------------------------------------------------------

## 12. Cross Review 권장 구조

예:

``` text
ML/DL
Owner: B
Reviewer: D

RAG
Owner: C
Reviewer: B

LangGraph
Owner: D
Reviewer: C

Agent Office
Owner: E
Reviewer: A

Integration
Owner: A
Reviewer: E
```

실제 사람 이름은 역할 확정 후 입력한다.

------------------------------------------------------------------------

## 13. 취업 준비 구성원의 Portfolio 전략

취업 준비 구성원은 단순히:

``` text
"팀 프로젝트에 참여했습니다."
```

라고 설명하지 않도록 한다.

각자 다음 구조로 설명할 수 있어야 한다.

``` text
Problem
→ My Module
→ Technical Decision
→ Implementation
→ Evaluation
→ Integration
→ Result
```

예:

``` text
"제조설비 진동 데이터의 이상탐지 모델을 담당했고,
Bearing 단위 Group Split으로 데이터 누수를 방지했습니다.
Random Forest와 1D CNN을 비교하고,
결과를 표준 AnalysisResult API로 LangGraph Agent에 연결했습니다."
```

------------------------------------------------------------------------

## 14. 공통 Portfolio Story

팀 전체가 설명할 수 있어야 하는 문장:

> 제조설비 센서 데이터를 ML/DL로 분석하고, RAG 기술문서를 근거로
> LangGraph AI Agent가 고장 가능성을 검토하고 점검·조치안을 생성하며,
> 전체 Agent Workflow를 실시간 Smart Factory Agent Office UI로 시각화한
> 프로젝트.

개인은 여기서 자신의 Module을 깊게 설명한다.

------------------------------------------------------------------------

# DEVELOPMENT WORKFLOW

## 15. 개발 단계

### Phase 0 --- Design

현재 단계.

``` text
Project Overview
Architecture
Data/ML
RAG
LangGraph
UI
API/DB
Evaluation
Team Roles
```

### Phase 1 --- Reference MVP

전체 E2E를 최소 기능으로 연결한다.

### Phase 2 --- Common Mini Project

팀원 전원이 직접 핵심 흐름을 구현/실행한다.

### Phase 3 --- Module Development

각 Owner가 Module을 고도화한다.

### Phase 4 --- Cross Review

서로 코드와 설계를 검토한다.

### Phase 5 --- Integration

최종 Branch에 통합한다.

### Phase 6 --- Evaluation

자동 평가 + 사용자 테스트.

### Phase 7 --- Release / Demo

배포, 발표, Demo.

------------------------------------------------------------------------

## 16. Git Branch 전략

과도하게 복잡한 Git Flow는 사용하지 않는다.

권장:

``` text
main
develop

feature/ml-...
feature/rag-...
feature/agent-...
feature/ui-...
feature/api-...
```

흐름:

``` text
feature/*
    ↓ PR
develop
    ↓ release check
main
```

------------------------------------------------------------------------

## 17. PR 원칙

PR에 최소 다음을 기록한다.

``` text
What
Why
How
Test
Affected Modules
Screenshot / Result (필요 시)
```

예:

``` text
What:
RAG metadata filter 추가

Why:
다른 component 문서가 상위 검색되는 문제

Test:
20개 evaluation query에서 expected source 확인
```

------------------------------------------------------------------------

## 18. Definition of Done

Module의 완료는 "코드가 돌아간다"가 아니다.

최소:

``` text
Implementation
Test
Documentation
Interface 확인
Integration 확인
```

을 완료해야 한다.

------------------------------------------------------------------------

## 19. Interface Freeze

초기 Reference MVP 이후 다음 Interface를 우선 고정한다.

``` text
SensorDatasetAdapter
AnalysisResult
EvidenceObject
AgentState
AgentEvent
FinalReport
API Contract
```

내부 구현은 바뀌어도 이 계약은 쉽게 변경하지 않는다.

이렇게 해야 5명이 병렬 개발할 수 있다.

------------------------------------------------------------------------

## 20. 팀 Sync Meeting

짧게 운영한다.

권장 질문:

``` text
어제/지난 작업에서 무엇을 완료했는가?
현재 Blocker는 무엇인가?
Interface 변경이 필요한가?
오늘 E2E에 무엇을 연결할 것인가?
```

긴 기능 설명보다 통합 위험을 먼저 공유한다.

------------------------------------------------------------------------

## 21. 주간 Integration Day

주기적으로 각 Module을 합친다.

확인:

``` text
ML → API
API → LangGraph
LangGraph → RAG
LangGraph → Event
Event → UI
Report → Citation
```

마지막 주에 한 번에 합치는 방식은 피한다.

------------------------------------------------------------------------

# 단계별 개발과 협업

## 22. 개발 도구 활용 원칙

개발 도구를 활용하되 설계 검토와 결과 검증은 팀이 함께 수행한다.

작업 방식:

``` text
설계 문서
      ↓
단계별 작업 계획
      ↓
Implementation
      ↓
팀 검토
      ↓
Test
      ↓
Commit
```

------------------------------------------------------------------------

## 23. 단계별 작업 범위

전체 개발 범위를 다음과 같이 작은 작업 단위로 나눈다.

``` text
STEP 01 — Repository scaffold
STEP 02 — Data Adapter
STEP 03 — Data profiling
STEP 04 — Feature pipeline
...
```

------------------------------------------------------------------------

## 24. AI 생성 코드 Review

AI가 만든 코드도 반드시:

``` text
실행
테스트
코드리뷰
Dependency 확인
Security 확인
```

을 거친다.

팀원이 설명하지 못하는 코드는 그대로 Merge하지 않는 것을 원칙으로 한다.

------------------------------------------------------------------------

# CONTRIBUTION TRACKING

## 25. 개인 기여도 기록

`docs/contributions/`를 둔다.

``` text
docs/contributions/
├── member_a.md
├── member_b.md
├── member_c.md
├── member_d.md
└── member_e.md
```

각 문서:

``` text
담당 Module
설계 기여
구현 PR
Test
문제 해결 사례
Cross Review
발표 담당
```

------------------------------------------------------------------------

## 26. 기술 의사결정 기록

중요 결정은 ADR 형태로 기록할 수 있다.

``` text
docs/adr/
├── 001-use-langgraph.md
├── 002-rag-vector-db.md
├── 003-sse-over-websocket.md
└── 004-group-split.md
```

면접에서 "왜 이 기술을 사용했는가?"를 설명하는 자료가 된다.

------------------------------------------------------------------------

# COMPETITION / FINAL PROJECT

## 27. 5인 Final Project와 별도 출품 관리

Final Project는 5인 팀 기준으로 개발한다.

외부 경진대회 출품 인원이나 기여 범위는 해당 대회의 공식 규정을 확인하여
별도로 관리한다.

따라서 Repository에는:

``` text
Final Project Team Contribution
```

과 외부 출품용 제출 정보가 혼동되지 않도록 한다.

------------------------------------------------------------------------

## 28. 발표 역할

발표에서 5명이 모두 긴 설명을 할 필요는 없다.

대신 각자의 전문성을 보여줄 증거가 있어야 한다.

예:

``` text
Architecture
ML/DL Evaluation
RAG Evidence
LangGraph Workflow
Agent Office Demo
```

발표자는 전체 Story를 연결하고, 질문이 들어오면 Module Owner가 답할 수
있도록 준비한다.

------------------------------------------------------------------------

# INITIAL ROLE ASSIGNMENT TEMPLATE

## 29. 역할 확정표

현재는 사람 이름을 넣지 않고 Template으로 유지한다.

  Role                         Owner   Reviewer   Main Deliverable
  ---------------------------- ------- ---------- -----------------------
  Architecture / Integration   TBD     TBD        E2E / API Integration
  Data & ML/DL                 TBD     TBD        Model / Evaluation
  RAG                          TBD     TBD        Knowledge Pipeline
  LangGraph / Agent            TBD     TBD        Agent Workflow
  Agent Office / QA            TBD     TBD        UI / E2E / Deploy

팀 회의 후 Owner/Reviewer만 채우면 된다.

------------------------------------------------------------------------

## 30. 역할 배정 기준

사람을 역할에 억지로 맞추지 않는다.

다음을 함께 본다.

``` text
현재 실력
관심 기술
취업 희망 분야
프로젝트에서 배우고 싶은 기술
작업 가능 시간
```

특히 취업 준비 구성원은 희망 직무와 Portfolio Story가 연결되도록
배치한다.

------------------------------------------------------------------------

## 31. Bus Factor 방지

핵심 Module마다 최소 두 명이 내용을 이해한다.

``` text
Owner
+
Reviewer
```

그리고 다음 자료를 남긴다.

``` text
README
실행 방법
환경변수
Test 방법
API Schema
Known Issues
```

------------------------------------------------------------------------

## 32. 팀 성공 기준

좋은 팀 프로젝트의 기준:

``` text
한 사람이 거의 다 만들었다
```

가 아니라,

``` text
빠르게 기준 구조를 만들고
→ 모두가 전체 구조를 이해하고
→ 각자 한 영역을 깊게 개선하고
→ 서로 Review하고
→ 하나의 E2E 제품으로 통합했다
```

가 되어야 한다.

------------------------------------------------------------------------

## 33. 다음 문서

다음 산출물:

**`10_DEVELOPMENT_GUIDE.md`**

이 문서는 지금까지 만든 설계 문서를 실제 개발에 활용할 수 있도록
정리하는 **개발 가이드**다.

포함 내용:

-   개발 원칙
-   프로젝트 목표
-   기술 Stack
-   반드시 읽을 설계 문서
-   Architecture 불변 원칙
-   Coding Rule
-   Repository Rule
-   Interface Contract
-   Test Rule
-   금지사항
-   단계별 개발 순서
-   각 STEP의 완료/검증 기준
-   다음 STEP으로 넘어가는 조건

이후 단계별 작업 계획은 다음과 같이 세분화한다.

``` text
STEP 01 — Repository scaffold
STEP 02 — Data Adapter
STEP 03 — Data profiling
STEP 04 — ML Baseline
...
```
