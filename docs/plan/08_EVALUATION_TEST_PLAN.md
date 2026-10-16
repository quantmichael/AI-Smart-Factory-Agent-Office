# AI Smart Factory Agent Office

## 08. Evaluation & Test Plan

**문서 버전:** v0.1\
**선행 문서:** `01_PROJECT_OVERVIEW.md` \~ `07_API_DB_SPEC.md`\
**목적:** 데이터, ML/DL, RAG, LangGraph, Agent, API, UI 및 End-to-End
Workflow의 품질을 하나의 평가 체계로 검증한다.

------------------------------------------------------------------------

## 1. 평가 목표

본 프로젝트의 성공 여부는 ML/DL 정확도 하나로 판단하지 않는다.

최종 평가는 다음 전체 체인을 대상으로 한다.

``` text
Sensor Data
    ↓
ML/DL Detection
    ↓
RAG Retrieval
    ↓
Evidence Verification
    ↓
LangGraph Branching
    ↓
Diagnosis / Inspection / Action
    ↓
Citation
    ↓
Agent Office Visualization
```

핵심 질문은 다음과 같다.

> **"센서 이상이 발생했을 때 시스템이 실제 데이터를 분석하고, 신뢰
> 가능한 근거를 찾아, 올바른 Workflow로 분기하며, 근거가 연결된
> 점검·조치안을 사용자에게 보여주는가?"**

------------------------------------------------------------------------

## 2. 평가 영역

총 8개 영역으로 나눈다.

``` text
A. Data Pipeline
B. ML/DL
C. RAG
D. LangGraph
E. AI Agent
F. API / Backend
G. UI / Agent Office
H. End-to-End / User Test
```

------------------------------------------------------------------------

# A. DATA PIPELINE

## 3. 데이터 검증

확인 항목:

-   파일 정상 로딩
-   Measurement 수
-   Sensor Channel
-   Sampling Rate
-   Operating Condition
-   Label
-   Bearing ID
-   Missing / NaN / Inf
-   Signal length
-   Metadata mapping

자동 결과:

``` text
artifacts/
├── data_profile.json
├── data_profile.csv
└── data_validation_report.json
```

------------------------------------------------------------------------

## 4. Data Leakage Test

가장 중요한 ML 테스트 중 하나다.

검사:

``` text
동일 Bearing ID가 Train/Test에 동시에 존재하는가?
동일 Measurement에서 생성된 Window가 Train/Test에 섞였는가?
```

기본 정책:

``` text
Group Split by Bearing ID
```

불가피한 경우 Measurement 기준 Group Split을 사용하고 문서화한다.

------------------------------------------------------------------------

# B. ML / DL

## 5. Binary Classification 평가

초기 Task:

``` text
Healthy vs Damaged
```

Metric:

-   Accuracy
-   Precision
-   Recall
-   F1-score
-   ROC-AUC
-   Confusion Matrix

이상 상태를 놓치는 문제를 확인하기 위해 Recall을 반드시 기록한다.

------------------------------------------------------------------------

## 6. 모델 비교

초기 비교:

``` text
Random Forest Baseline
        vs
1D CNN
```

고도화:

``` text
Isolation Forest / Autoencoder
```

비교표:

  Model             Accuracy   Recall   F1   Inference Time Notes
  --------------- ---------- -------- ---- ---------------- -------
  RF                                                        
  1D CNN                                                    
  Anomaly Model          N/A                                

성능뿐 아니라 추론속도와 교육적 설명 가능성도 기록한다.

------------------------------------------------------------------------

## 7. Generalization Test

가능하면 운전조건이 달라질 때 성능을 확인한다.

예:

``` text
Train
1500 rpm / 0.7 Nm / 1000 N
900 rpm / 0.7 Nm / 1000 N
1500 rpm / 0.1 Nm / 1000 N

Test
1500 rpm / 0.7 Nm / 400 N
```

이 결과는 "모델이 특정 조건만 외웠는가?"를 판단하는 참고자료로 사용한다.

------------------------------------------------------------------------

## 8. ML Output Contract Test

모든 모델은 `Standard Analysis Result`를 반환해야 한다.

검사:

``` text
status 존재
predicted_class 존재
confidence 형식 정상
features schema 정상
model_id 존재
measurement_id 추적 가능
```

------------------------------------------------------------------------

# C. RAG

## 9. RAG 평가셋

최소 20\~30개 질문으로 시작한다.

분류:

``` text
Dataset Context
Damage Fact
Diagnostic Knowledge
Inspection
Maintenance
Unanswerable
Conflicting Evidence
```

예:

``` text
Q01
특정 Bearing ID의 손상 정보는 무엇인가?

Expected:
Paderborn Fact Sheet

Q02
관찰된 진동 특성과 관련된 가능한 원인은 무엇인가?

Expected:
Vibration Diagnostic Guide

Q03
해당 후보를 확인하기 위한 점검은 무엇인가?

Expected:
Inspection / Failure Analysis document
```

------------------------------------------------------------------------

## 10. Retrieval Metric

최소:

``` text
Hit@K
Recall@K
MRR
Expected Source Hit
Empty Result Rate
```

초기 `K`:

``` text
K = 3
K = 5
```

를 비교한다.

------------------------------------------------------------------------

## 11. Metadata Filter Test

검사:

``` text
equipment_type
component
fault_type
document_type
source_tier
```

잘못된 Domain 문서가 상위 검색되는지 확인한다.

------------------------------------------------------------------------

## 12. Citation Correctness

각 최종 Citation에 대해 검사:

``` text
실제 Document인가?
실제 Chunk인가?
Page/Section Metadata가 존재하는가?
주장이 해당 Evidence에 의해 뒷받침되는가?
```

LLM이 만든 가짜 문서명/페이지는 실패로 처리한다.

------------------------------------------------------------------------

## 13. Grounding 평가

Agent 응답 문장을 다음으로 분류한다.

``` text
SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED
```

중요 주장:

-   고장 후보
-   원인 설명
-   점검 절차
-   조치안

에 대해 Unsupported Claim을 측정한다.

------------------------------------------------------------------------

## 14. Unanswerable Test

Knowledge Base에 답이 없는 질문을 의도적으로 포함한다.

기대 결과:

``` text
근거 부족을 인식
→ 추가 검색
→ 그래도 없으면 제한된 답변
```

실패:

``` text
근거가 없는데 확정적 답변 생성
```

------------------------------------------------------------------------

## 15. Conflicting Evidence Test

서로 다른 가능성을 지지하는 문서를 제공한다.

기대:

``` text
CONFLICTING
→ counter evidence retrieval
→ 단정하지 않음
→ 추가 점검 제안
```

------------------------------------------------------------------------

# D. LANGGRAPH

## 16. Graph Path Test

주요 Path를 각각 테스트한다.

### Path 1 --- Normal

``` text
Load
→ Detection
→ NORMAL
→ Save
→ END
```

### Path 2 --- Abnormal + Sufficient

``` text
Detection
→ ABNORMAL
→ RAG
→ Diagnosis
→ SUFFICIENT
→ Inspection
→ Action
→ Report
```

### Path 3 --- Partial

``` text
RAG
→ Diagnosis
→ PARTIAL
→ Refine Query
→ RAG
→ SUFFICIENT
```

### Path 4 --- Insufficient

``` text
RAG
→ INSUFFICIENT
→ Human Check / Limited Report
```

### Path 5 --- Conflicting

``` text
Diagnosis
→ CONFLICTING
→ Counter Evidence
→ Diagnose
```

------------------------------------------------------------------------

## 17. Retry Test

검사:

``` text
retrieval_retry_count 증가
max_retrieval_retry 준수
무한 Loop 없음
```

한도 초과 후:

``` text
LIMITED
또는
WAITING_HUMAN
```

으로 이동해야 한다.

------------------------------------------------------------------------

## 18. Deterministic Routing Test

다음은 LLM 없이 재현 가능해야 한다.

``` text
normal/abnormal routing
retry limit
schema validation
error routing
```

동일 입력에서 Route가 달라지면 실패로 본다.

------------------------------------------------------------------------

## 19. State Integrity Test

각 Node 후 검사:

``` text
필수 State가 사라지지 않는가?
run_id 유지?
equipment_id 유지?
Evidence ID 유지?
retry count 정상?
current_node 정상?
```

------------------------------------------------------------------------

# E. AI AGENT

## 20. Diagnosis Candidate Test

각 Candidate는 최소 다음을 가져야 한다.

``` text
cause
confidence_level
supporting_evidence_ids
requires_confirmation
```

근거 없는 Candidate는 최종 결과에서 제거하거나 낮은 신뢰 상태로
명시한다.

------------------------------------------------------------------------

## 21. Inspection Plan Test

검사:

``` text
각 Step의 목적이 있는가?
어떤 Candidate를 확인하는지 연결되는가?
Evidence가 있는가?
순서가 보존되는가?
```

------------------------------------------------------------------------

## 22. Recommended Action Test

검사:

``` text
Action Level 유효
Reason 존재
Evidence 연결
위험한 작업 자동실행 없음
승인 필요 여부 표시
```

------------------------------------------------------------------------

## 23. Human-in-the-loop Test

시나리오:

``` text
Evidence 부족
→ Agent가 추가 점검 요청
→ Workflow WAITING_HUMAN
→ 사용자 입력
→ State Update
→ Workflow Resume
```

MVP에서 구현하지 못하면 고도화 항목으로 명시하되 Graph 설계는 유지한다.

------------------------------------------------------------------------

# F. API / BACKEND

## 24. API Test

최소 Endpoint:

``` text
GET equipment
GET measurements
POST analysis
POST agent run
GET agent run
GET event stream
GET evidence
GET report
```

검사:

``` text
200 정상 응답
400 invalid request
404 unknown ID
500 내부 오류 처리
schema validation
```

------------------------------------------------------------------------

## 25. SSE Test

검사:

``` text
Event 순서
sequence 증가
run_id 일치
node_started / completed
workflow_completed
connection close
```

재연결 시 현재 Run State를 복원할 수 있어야 한다.

------------------------------------------------------------------------

## 26. Persistence Test

페이지를 새로고침하거나 Backend를 재조회했을 때:

``` text
Run
Analysis
Evidence
Final Report
```

가 추적 가능해야 한다.

------------------------------------------------------------------------

# G. UI / AGENT OFFICE

## 27. Backend/UI Synchronization

가장 중요한 UI Test다.

예:

``` text
Backend current_node = retrieve_knowledge

Expected UI:
RAG Agent = WORKING
RAG Library = ACTIVE
Live View = retrieve_knowledge
Timeline = retrieval started
```

Backend와 다른 Agent가 움직이면 실패다.

------------------------------------------------------------------------

## 28. Event Mapping Test

각 Event에 대한 UI 결과를 자동 또는 수동 검증한다.

``` text
detection_abnormal
retrieval_completed
evidence_status_changed
human_input_required
workflow_completed
workflow_error
```

------------------------------------------------------------------------

## 29. UI Usability Test

사용자에게 다음 과제를 준다.

``` text
1. 현재 이상 설비 찾기
2. ML 결과 찾기
3. 현재 Agent 작업 확인
4. 진단 후보 확인
5. 근거 문서 열기
6. 점검 순서 확인
7. 권장 조치 확인
```

완료 여부와 시간을 기록한다.

------------------------------------------------------------------------

# H. END-TO-END

## 30. E2E Acceptance Scenario 01 --- Normal

``` text
Given:
Healthy sample

When:
Diagnosis Run 실행

Then:
ML = normal
RAG 불필요
정상 상태 저장
Agent Office 정상 표시
Workflow Completed
```

------------------------------------------------------------------------

## 31. E2E Acceptance Scenario 02 --- Abnormal

``` text
Given:
Damaged sample

When:
Diagnosis Run 실행

Then:
ML detects abnormal
RAG retrieves evidence
Diagnosis candidates generated
Evidence verified
Inspection plan generated
Recommended action generated
Citations displayed
Agent Office reflects every major state
```

------------------------------------------------------------------------

## 32. E2E Acceptance Scenario 03 --- RAG Retry

Demo에서 특히 중요하다.

``` text
Given:
초기 검색만으로 근거가 부족한 Scenario

Then:
Evidence = PARTIAL
→ refine_query
→ second retrieval
→ Evidence improves
→ workflow continues
```

LangGraph를 사용한 이유가 화면에서 명확하게 보여야 한다.

------------------------------------------------------------------------

## 33. E2E Acceptance Scenario 04 --- Human Check

``` text
Evidence insufficient
→ additional information requested
→ WAITING_HUMAN
→ user response
→ resume
```

시간 부족 시 P1 기능으로 둔다.

------------------------------------------------------------------------

# USER TEST

## 34. 사용자 테스트 목표

최종 프로젝트에서는 실제 사용자 피드백을 수집한다.

최소 목표:

``` text
5명 이상
```

테스트 대상 후보:

-   개발자
-   제조업 종사자
-   설비 관련 경험자
-   AI 교육생
-   일반 사용자

전문가 여부를 별도 기록한다.

------------------------------------------------------------------------

## 35. 사용자 테스트 질문

5점 척도 예:

``` text
1. 현재 설비 상태를 이해하기 쉬웠다.
2. AI가 어떤 과정을 수행하는지 이해할 수 있었다.
3. ML/DL 분석 결과를 이해하기 쉬웠다.
4. 진단 근거를 확인하기 쉬웠다.
5. 점검 순서가 명확했다.
6. AI의 결과를 무조건적인 확정 진단으로 오해하지 않았다.
7. Agent Office가 시스템 동작을 이해하는 데 도움이 되었다.
8. 실제 제조설비 업무에 적용 가능성이 있다고 느꼈다.
```

서술형:

``` text
가장 이해하기 어려웠던 부분은?
가장 유용했던 기능은?
불필요하거나 복잡했던 기능은?
추가되면 좋을 기능은?
```

------------------------------------------------------------------------

## 36. 사용자 피드백 반영

피드백은 수집만 하지 않는다.

``` text
Feedback
    ↓
Issue
    ↓
Priority
    ↓
Change
    ↓
Retest
```

최종 발표에서:

``` text
사용자 의견
→ 실제 변경사항
```

을 한 사례 이상 보여주는 것을 목표로 한다.

------------------------------------------------------------------------

# DEMO / RELEASE

## 37. Release Gate

최종 Demo 전 반드시 통과:

### P0

-   [ ] 정상 Sample E2E 성공
-   [ ] 이상 Sample E2E 성공
-   [ ] ML 결과 실제 모델 기반
-   [ ] RAG 실제 Vector Retrieval
-   [ ] Citation 실제 문서 기반
-   [ ] LangGraph 실제 조건분기
-   [ ] Agent Event 실제 Backend 기반
-   [ ] UI 상태 동기화
-   [ ] 최종 Report 생성
-   [ ] 오류 없이 재현 가능한 Demo Sample 확보

------------------------------------------------------------------------

## 38. Demo Reproducibility

발표 직전 외부 API나 랜덤성 때문에 실패하지 않도록 한다.

-   검증된 Sample 고정
-   Model version 고정
-   Knowledge Pack version 고정
-   Prompt version 고정
-   timeout 처리
-   API 실패 메시지
-   필요한 Cache 검토
-   Demo 전 자동 Smoke Test

Demo Mode는 결과 조작이 아니라 **재현 가능한 실제 입력을 선택하는
기능**이다.

------------------------------------------------------------------------

## 39. 자동 테스트 구조

``` text
tests/
├── data/
├── ml/
├── rag/
├── agent/
├── api/
├── integration/
└── e2e/
```

예:

``` text
test_data_adapter.py
test_feature_extraction.py
test_model_output_schema.py
test_retrieval.py
test_citation.py
test_graph_normal_path.py
test_graph_retry_path.py
test_api_agent_run.py
test_event_sequence.py
test_e2e_abnormal.py
```

------------------------------------------------------------------------

## 40. 평가 결과 저장

``` text
artifacts/evaluation/
├── data_validation.json
├── ml_metrics.json
├── confusion_matrix.*
├── rag_eval.json
├── graph_path_test.json
├── api_test.json
├── user_test.csv
└── final_acceptance.json
```

가능하면 실행 시점과 버전을 함께 기록한다.

------------------------------------------------------------------------

## 41. 최종 프로젝트 KPI

초기 목표치는 실제 Baseline 실행 후 확정한다.

따라서 현재 단계에서 임의로 높은 정확도 목표를 고정하지 않는다.

대신 반드시 측정할 KPI를 먼저 확정한다.

``` text
ML Recall / F1
RAG Hit@K / Recall@K
Citation Correctness
Unsupported Claim Rate
Graph Path Success Rate
E2E Success Rate
API Error Rate
User Task Completion
User Satisfaction
```

Baseline 측정 후 현실적인 Acceptance Threshold를 설정한다.

------------------------------------------------------------------------

## 42. 가장 중요한 평가 원칙

이 프로젝트에서 좋은 결과란:

``` text
"정확도가 99%다"
```

만을 의미하지 않는다.

더 중요한 것은:

``` text
왜 이상이라고 했는가?
        ↓
어떤 자료를 찾았는가?
        ↓
그 자료가 실제로 주장을 뒷받침하는가?
        ↓
근거가 부족하면 시스템이 다시 찾는가?
        ↓
그래도 부족하면 모른다고 말하는가?
        ↓
사용자가 점검과 조치 근거를 확인할 수 있는가?
```

이다.

이 평가 구조가 **AI Smart Factory Agent Office**를 단순 ML 데모나 RAG
챗봇과 구분한다.

------------------------------------------------------------------------

## 43. 다음 문서

다음 산출물:

**`09_TEAM_ROLES.md`**

다음 내용을 정의한다.

-   5인 팀 역할
-   공통 학습 영역
-   ML/DL 담당
-   RAG 담당
-   LangGraph/Agent 담당
-   Frontend/Agent Office 담당
-   Integration/QA/Deployment
-   취업 준비 팀원의 Portfolio 산출물
-   Module Owner와 Cross Review
-   Git Branch / PR 원칙
-   개인 기여도 기록
-   전체 팀이 RAG/LangGraph를 경험하는 공통 Mini Project
