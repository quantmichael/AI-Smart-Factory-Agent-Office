# AI Smart Factory Agent Office

## 01. Project Overview

**문서 버전:** v0.1\
**프로젝트 유형:** AI Native Final Project / 제조설비 AI Agent\
**기준 데이터 소스:** Paderborn University Bearing DataCenter\
**설계 원칙:** 데이터셋과 RAG 지식베이스는 교체 가능한 모듈로 구성한다.

------------------------------------------------------------------------

## 1. 프로젝트 한 줄 정의

산업설비의 센서 데이터를 ML/DL로 분석하여 이상을 탐지하고, RAG 기반
기술문서 검색과 LangGraph 기반 AI Agent가 원인 후보·점검 순서·조치안을
제시하며, 전체 과정을 **AI Smart Factory Agent Office**에서 실시간으로
시각화하는 산업설비 진단 플랫폼이다.

## 2. 문제 정의

제조 현장에서는 진동, 전류, 온도, 회전속도 등 다양한 센서 데이터가
지속적으로 발생한다. 그러나 센서값 자체만으로 설비 상태와 원인을
판단하기 어렵다.

본 프로젝트는 다음 질문에 답하는 End-to-End 시스템을 목표로 한다.

-   어떤 설비에서 이상이 발생했는가?
-   평상시와 얼마나 다른가?
-   어떤 고장 가능성이 있는가?
-   판단의 기술적 근거는 무엇인가?
-   무엇을 추가로 점검해야 하는가?
-   어떤 순서로 조치해야 하는가?
-   과거에도 비슷한 문제가 있었는가?

## 3. 핵심 목표

1.  산업설비 시계열 센서 데이터 파이프라인 구축
2.  ML/DL 기반 이상탐지 또는 고장분류
3.  장비·진동진단·고장·정비 문서 RAG 구축
4.  LangChain으로 LLM, Retriever, Vector DB, Tool 연결
5.  LangGraph로 State, Node, Edge, 조건분기, 반복검색 구현
6.  AI Agent가 ML/DL 결과와 RAG 근거를 결합해 진단·점검·조치안 생성
7.  전체 Agent 동작을 AI Smart Factory Agent Office에서 시각화
8.  향후 다른 산업설비 데이터와 문서로 교체 가능한 범용 구조 구현

## 4. 기준 데이터와 RAG

초기 Reference Dataset은 **Paderborn Bearing DataCenter**로 한다.

데이터와 RAG는 반드시 같은 진단 도메인에서 결합한다.

### ML/DL 데이터

-   진동 센서 데이터
-   모터 전류
-   운전 조건
-   정상/손상 상태
-   손상 정보 및 실험 정보

### RAG Knowledge Base

-   Paderborn Dataset Documentation
-   Test Rig / Measurement 문서
-   Bearing Damage Fact Sheet
-   진동진단 기술문서
-   베어링 고장 분석 문서
-   유지보수 및 Troubleshooting 문서
-   고장 사례 및 점검 자료

더 적합한 데이터와 RAG 자료를 확보하면 해당 모듈을 교체한다.

## 5. 전체 서비스 흐름

``` text
Sensor / Dataset
      ↓
Data Ingestion
      ↓
Preprocessing / Feature Extraction
      ↓
ML/DL Anomaly Detection / Fault Classification
      ↓
LangGraph Agent Workflow
      ↓
RAG Technical Knowledge Retrieval
      ↓
Diagnosis / Verification
      ↓
Cause Candidates
      ↓
Additional Inspection
      ↓
Recommended Action
      ↓
Report / Alert
      ↓
AI Smart Factory Agent Office
```

## 6. Agent Workflow

초기에는 불필요한 Multi-Agent 복잡도를 피하고 하나의 LangGraph 안에서
역할별 Node로 구성한다.

-   **Data Node:** 센서 데이터 및 상태 수집
-   **Detection Node:** ML/DL 추론
-   **RAG Node:** 관련 기술문서·고장사례 검색
-   **Diagnosis Node:** ML/DL 결과와 RAG 근거 결합
-   **Verification Node:** 근거 충분성 판단
-   **Maintenance Node:** 점검 순서와 권장 조치 생성
-   **Report Node:** 근거가 포함된 최종 결과 생성

``` text
START
  ↓
Load Sensor Data
  ↓
Run ML/DL
  ↓
Abnormal?
 ├─ NO → Store Normal State → END
 └─ YES
      ↓
   RAG Search
      ↓
   Diagnose
      ↓
Evidence Sufficient?
 ├─ NO → Additional Retrieval / Request Information
 │           ↓
 │       Update State
 │           ↓
 │        Diagnose
 └─ YES
      ↓
   Inspection Plan
      ↓
   Recommended Action
      ↓
   Report / Alert
      ↓
     END
```

## 7. AI Smart Factory Agent Office

최종 UI는 **Modern Smart Factory Dashboard + Pixel/Isometric Agent
Office + LangGraph Live View**로 구성한다.

중요한 원칙은 UI 애니메이션 자체가 Agent가 아니라는 점이다. 실제 Backend
LangGraph State가 변경될 때 UI도 함께 변경된다.

### Smart Factory Dashboard

-   설비 상태
-   센서 상태
-   이상 Score
-   최근 Alert
-   Agent 작업 상태

### Pixel / Isometric Agent Office

-   설비 및 센서
-   Agent 작업 위치
-   경고 상태
-   분석 진행 상태
-   Agent 간 업무 전달 시각화

### LangGraph Live View

-   현재 Node
-   State
-   Tool 실행
-   RAG 검색
-   조건분기
-   재검색
-   최종 판단 과정

## 8. MVP 필수 범위

-   데이터 로딩 및 전처리
-   ML 또는 DL 모델 최소 1개
-   이상/고장 분석
-   기술문서 RAG
-   Vector DB
-   LangChain Retrieval
-   LangGraph Workflow
-   조건분기 최소 1개
-   RAG 근거가 포함된 진단 결과
-   점검 및 조치안
-   Web UI
-   외부 배포 가능한 구조

## 9. 고도화 범위

-   ML/DL 모델 비교
-   실시간 데이터 스트리밍
-   Multimodal 이미지 입력
-   Long-term Memory
-   설비별 이력관리
-   Human-in-the-loop
-   Agent Office 애니메이션
-   LangGraph Live View 고도화
-   자동 알림
-   필요 시 Multi-Agent 확장

## 10. 범용화 원칙

특정 베어링 데이터셋 전용 서비스로 만들지 않는다.

``` text
Data Source
    ↓
Data Adapter
    ↓
ML/DL Model
    ↓
Standard Analysis Result
    ↓
LangGraph Agent
    ↓
Knowledge Base
```

향후 Bearing, Motor, Pump, Fan, Gearbox, Conveyor, Mixer/Agitator 등으로
확장할 수 있도록 한다.

## 11. 프로젝트 성공 기준

다음 End-to-End Workflow가 실제로 동작하면 1차 MVP를 성공으로 본다.

> 센서 데이터 입력 → ML/DL 이상 탐지 → LangGraph 진단 시작 → RAG
> 기술문서 검색 → ML/DL 결과와 근거 결합 → 원인 후보 및 추가 점검 제시 →
> 권장 조치와 출처 제시 → AI Smart Factory Agent Office에 전체 과정 표시

기능 수보다 **하나의 완전한 End-to-End Workflow**를 먼저 완성한다.

## 12. 현재 확정 사항

  항목          결정
  ------------- ----------------------------------------------------------------
  프로젝트명    AI Smart Factory Agent Office
  분야          제조설비 이상탐지·고장진단 AI Agent
  기준 데이터   Paderborn Bearing DataCenter
  데이터 정책   더 좋은 데이터+RAG 조합 확보 시 교체
  RAG           기술문서·진단가이드·고장사례·정비자료
  ML/DL         센서 기반 이상탐지/고장분류
  Agent         LangChain + LangGraph
  UI            Dashboard + Pixel/Isometric Agent Office + LangGraph Live View
  개발 전략     End-to-End MVP 우선 후 고도화
  산출물        Markdown (.md)

## 13. 다음 문서

다음 산출물은 **`02_SYSTEM_ARCHITECTURE.md`**이다.

여기서 Frontend, Backend, ML/DL Service, RAG Service, LangGraph Agent,
Vector DB, Application DB, API, Agent State, 배포 구조 및 데이터/RAG
교체 구조를 구체화한다.
