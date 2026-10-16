# AI Smart Factory Agent Office 개발완료보고서

제4회 경남 AI·SW 경진대회 제출용  
제조설비 이상탐지와 고장진단을 위한 근거기반 AI Agent 시스템

## 1 프로젝트 개요 및 문제 정의

### 프로젝트 개요

AI Smart Factory Agent Office는 베어링 측정 데이터를 입력받아 정상과 손상을 분류하고, 손상일 때만 기술문서를 검색해 진단 근거와 점검·조치안을 만드는 의사결정 지원 시스템이다. 현재 MVP는 Paderborn Bearing DataCenter의 저장된 MAT Measurement를 센서 입력처럼 재생한다. 실제 PLC나 실시간 센서 스트림에는 연결되어 있지 않다.

| 구분 | 내용 |
|---|---|
| 주요 사용자 | 설비보전 담당자, 생산기술 담당자, 진단 결과를 검토하는 현장 책임자 |
| 현장 문제 | 신호 수치, 기술문서, 진단 절차가 분리되어 있어 판정 이유와 후속 행동을 함께 확인하기 어렵다 |
| 개발 목표 | 측정 데이터부터 ML 판정, 근거 검색, 진단, 점검계획, 권고조치, 보고서까지 한 흐름으로 연결한다 |
| 시스템 범위 | 이상탐지와 진단 지원. 설비 자동제어와 고장 발생 시점 예측은 범위 밖이다 |

### 기존 방식과 Agent 적용 방식

기존 방식은 담당자가 진동 데이터를 확인한 뒤 별도의 문서에서 기준을 찾고, 판단 과정과 후속 조치를 다시 정리해야 한다. 본 시스템은 ML 결과에 따라 Workflow를 분기하고, 필요한 경로에서만 RAG와 진단 도구를 호출한다. 최종 보고서는 사용한 Measurement, 모델 버전, 기술 근거, 점검계획과 한계를 함께 보존한다.

### 핵심 기능

1. 저장된 Paderborn Measurement와 실제 MAT 채널의 Replay
2. 진동 및 상전류 3채널에서 추출한 36개 Feature 기반 Random Forest 판정
3. 정상은 짧게 종료하고 손상은 RAG 진단으로 전환하는 LangGraph 분기
4. 문서명, 발행기관, 페이지, 섹션을 포함한 Evidence와 Final Report
5. Run History, Checkpoint, Long-term Memory를 이용한 실행 저장과 복원

> 핵심 수치: Measurement 240건 · Feature 36개 · Knowledge Document 15개 · Embedding 183개 · Agent 역할 5개

<!-- PAGE BREAK -->

## 2 AI Agent 시스템 설계

### 전체 Architecture

```text
사용자와 Next.js Dashboard
        │ Measurement 선택 · Replay · 이미지 선택 입력
        ▼
FastAPI API ───────── SSE Event Stream ────────▶ 실시간 Agent Office
        │
        ▼
LangGraph diagnosis_core_v1
        ├─ Paderborn Adapter ─ Feature Extraction ─ Random Forest
        ├─ Chroma bearing_v1 ─ Evidence Retrieval
        ├─ Diagnosis ─ Evidence Verification ─ Inspection ─ Action
        ├─ HITL Policy ─ Human Input ─ Checkpoint Resume
        └─ Final Report
        │
        ▼
SQLite Run/Event · Checkpoint · Equipment Memory · Vision Metadata
```

### 실제 E2E Workflow

```text
Measurement 로드 → 설비 이력 로드 → ML 이상탐지 → 정상·손상 분기
  정상  → 정상 상태 저장 → 정상 보고서 → COMPLETED
  손상  → 선택 이미지 확인 → RAG 질의 → 기술 근거 검색 → 진단
        → 근거 검증 → 점검계획 → 조치권고 → 필요 시 HITL → 최종 보고서
```

### 5개 Agent 역할과 Tool

| Agent 역할 | 판단 또는 실행 | 사용하는 Tool과 Data |
|---|---|---|
| 센서·데이터 | 선택한 Measurement와 운전조건을 로드 | Paderborn MAT adapter, Measurement metadata |
| 이상탐지 | 36개 Feature로 정상·손상을 판정 | RandomForestClassifier artifact |
| 기술지식 | 손상 상태와 신호 특징에 맞는 근거를 검색 | QueryBuilder, Hashing Vectorizer, Chroma |
| 진단 | Evidence로 원인 후보를 만들고 근거 충족도를 확인 | Deterministic reasoner, Evidence verifier |
| 정비지원 | 점검 순서와 권고조치를 만들고 보고서를 완성 | Action planner, HITL policy, report builder |

### 일반 ChatGPT와 다른 점

사용자의 자유 질문에 곧바로 문장을 생성하지 않는다. 시스템은 구조화된 `AgentState`를 유지하고 ML 결과에 따라 다음 노드를 선택한다. 검색 결과는 `EvidenceObject`로 변환되어 문서, 페이지, 섹션과 함께 진단 후보에 연결된다. Retry 횟수와 HITL 전환 조건이 코드로 제한되며, 실행 결과는 Run ID와 Checkpoint로 복원된다. 현재 검증된 핵심 경로는 외부 LLM 없이 결정론적 reasoner와 planner를 사용한다.

<!-- PAGE BREAK -->

## 3 핵심 기술 및 실제 구현

### 데이터와 ML

Paderborn adapter는 240개 MAT Measurement를 인덱싱하고, 파일명에서 bearing과 운전조건을 식별한다. UI의 Replay는 저장 신호를 시간축에 맞춰 보여준다. 실제 센서의 연속 수집 기능은 포함하지 않는다.

활성 모델 `bearing_rf_binary_v1`은 RandomForestClassifier v1.0이다. 1초 비중첩 Window에서 `vibration_1`, `phase_current_1`, `phase_current_2`를 사용한다. 각 채널마다 평균, 표준편차, RMS, Peak, Peak-to-Peak, Crest Factor, Skewness, Kurtosis와 4개 주파수 Feature를 계산해 총 36개 Feature를 만든다. 모델은 300개 tree, 최대 깊이 12, balanced class weight 설정을 사용한다.

| 학습·평가 항목 | 실제 값 | 해석 |
|---|---:|---|
| Train/Test Measurement | 180 / 60 | Measurement ID 기준 stratified group split |
| Train/Test Window | 718 / 239 | 같은 Measurement의 Window는 한 split에만 배치 |
| Test Measurement F1 | 1.0 | 현재 대표 subset 내부 결과 |
| 알려진 제한 | 3개 bearing ID 공유 | 처음 보는 bearing에 대한 일반화 성능은 측정하지 않음 |

### RAG와 Evidence

Knowledge Base는 Paderborn 공식 자료와 SKF 기술문서를 포함한 15개 색인 문서, 183개 Chunk/Embedding으로 구성된다. `sklearn-hashing-vectorizer-v1`이 384차원 vector를 생성하고 Chroma `bearing_v1` collection이 cosine distance로 검색한다. Retriever는 목적별 metadata filter를 적용하고 인접 중복 Chunk를 제거한다. UI의 검색 점수는 `1 - cosine distance` 기반 순위 점수이며 정확도나 고장 확률이 아니다.

### Application과 저장 구조

| 영역 | 구현 역할 |
|---|---|
| FastAPI | Measurement, Run, SSE, HITL, Report, Knowledge, Model, System API 제공 |
| LangGraph | 25개 backend node와 조건부 edge로 실행·재검색·HITL·종료 제어 |
| Next.js | 통합 관제, 진단 이력, 기술지식, AI 모델, 시스템 화면 제공 |
| SQLite | Run/Event/Human Request, Checkpoint, Equipment Memory, Vision metadata 분리 저장 |
| SSE | node와 역할별 Event를 전달하고 Frontend가 최대 4회 backoff 재연결 |

<!-- PAGE BREAK -->

## 4 구현 결과 및 검증

### 대표 E2E 결과

| Test Case | 입력 | 실제 경로와 결과 | 저장·복원 |
|---|---|---|---|
| 정상 | `K001 N09_M07_F10 01` | ML `normal` → RAG 생략 → 정상 Report → `COMPLETED`; Evidence 0건, Event 19건 | Run 상세와 Report 재조회 성공 |
| 손상 | `KA01 N09_M07_F10 01` | ML `abnormal` → RAG → Evidence 검증 → 진단·점검·조치 → Report → `COMPLETED`; Evidence 9건, Event 37건 | Run 상세와 Report 재조회 성공 |
| HITL 시연 | `KA01 N09_M07_F10 02` + `HITL_CONTROLLED` | 실제 ML·RAG·진단 후 중요 조치 정책에 따라 `WAITING` → 작업자 `APPROVE` → Checkpoint resume → `COMPLETED`; Evidence 9건, Event 46건 | Run, Report, Human Decision 재조회 성공 |

정상 경로는 불필요한 RAG, 진단, 점검, 조치 노드를 실행하지 않았다. 손상 경로는 진단용 검색과 점검·조치용 검색을 분리하고, 최종 보고서에 9개의 추적 가능한 Citation을 포함했다. 새 프로세스에서 두 Run을 다시 조회했을 때 상세 상태와 Final Report가 복원되었으며, 이력 조회만으로 Long-term Memory가 증가하지 않았다.

### 자동화 검증 결과

| 검증 항목 | 결과 |
|---|---:|
| Backend 전체 테스트 | 162 passed |
| Frontend 전체 테스트 | 28 passed |
| TypeScript 검사 | 통과 |
| Next.js Production Build | 통과, 7개 Route 생성 |
| System Status | 전체 READY |
| Historical Run 복원 | 정상·손상 모두 HTTP 200 |

### 안전 경로 검증

HITL 통합 테스트와 시나리오 C는 `RUNNING → WAITING → 작업자 입력 → RUNNING → COMPLETED` resume를 확인한다. 같은 요청의 중복 처리 방지와 Checkpoint 복원도 테스트한다. 일반 손상 시나리오 B는 정책상 사람 승인이 필요하지 않아 HITL 없이 완료되며, 시나리오 C만 중요 조치가 포함된 공개된 시연 조건으로 HITL을 재현한다. 이미지 기반 관찰은 저장·분석·HITL resume 자동화 테스트를 통과했지만, 이번 실제 Paderborn A/B/C 대표 E2E에는 이미지를 첨부하지 않았다.

### 실제 화면

![AI Smart Factory Agent Office 통합 관제 화면](../../artifacts/ui/agent_office/bilingual_overview_cropped.png)

<!-- PAGE BREAK -->

## 5 활용 효과 한계 및 현장 확장

### 기대 활용

- ML 판정과 문서 근거를 한 Run에서 연결해 담당자가 판정 근거를 다시 추적할 수 있다.
- 정상 경로는 빠르게 종료하고 손상 경로에만 검색과 진단 단계를 사용한다.
- 점검계획과 권고조치는 설비 자동제어 명령이 아니라 작업자의 판단을 돕는 정보로 제공한다.
- 이력, Checkpoint, Memory가 Run 단위로 남아 재조회와 후속 진단 문맥에 사용할 수 있다.

### 현재 MVP의 한계

1. Paderborn 저장 Measurement를 사용하며 실제 PLC, MQTT, Kafka 센서 ingestion은 없다.
2. 모델 평가지표 1.0은 세 bearing ID가 train과 test에 모두 포함된 대표 subset 결과다. 현장 성능 100%를 의미하지 않는다.
3. 모델 confidence는 calibration을 거친 실제 고장 확률이 아니다.
4. RAG는 승인된 영문 문서 범위에서만 근거를 찾으며, 검색 점수는 상대적 유사도다.
5. 정식 현장 사용자 연구와 시간·비용 절감 효과 측정은 수행하지 않았다.
6. Multimodal은 선택 입력과 자동화 테스트가 있으나 실제 시험체 이미지 기반 대표 E2E 검증이 추가로 필요하다.

### Live Sensor 확장 구조

현장 적용 시 `PLC 또는 Sensor Gateway → 수집·품질검사 → Measurement Adapter`를 추가하고, 이후의 Feature Extraction, ML 분기, RAG, LangGraph, HITL, Report 구조는 유지한다. 설비별 데이터 분포가 달라지므로 새 설비 데이터를 이용한 재학습, unseen-equipment 평가, threshold 검토, probability calibration이 선행되어야 한다.

### 데이터와 기술 출처

| 구분 | 출처와 사용 범위 |
|---|---|
| Dataset | Paderborn University Bearing DataCenter, CC BY-NC 4.0, 비상업·출처표시 조건 |
| 진단 문서 | Paderborn 공식 웹·논문 및 SKF Vibration Diagnostic Guide, Bearing Damage and Failure Analysis |
| 문서 배포 | SKF 및 일부 웹 자료는 재배포 권한이 확인되지 않아 Source Manifest와 공식 URL 중심으로 관리 |
| Open Source | Python, FastAPI, scikit-learn, LangGraph, Chroma, SciPy, Next.js, React, TypeScript |
| AI 활용 | Random Forest 분류와 상태 기반 Agent Workflow, RAG 검색을 신규 통합 구현. 외부 LLM 자유 생성은 검증된 핵심 경로에 사용하지 않음 |

### 기존 자산과 신규 개발 구분

Paderborn Dataset과 공개 기술문서는 외부 자산이다. Dataset adapter, Feature pipeline, 모델 artifact와 registry, RAG ingestion/retrieval, LangGraph node와 routing, Evidence schema, HITL, Memory, API, Agent Office UI, 진단 이력 및 시스템 상태 화면은 본 프로젝트에서 구현했다.
