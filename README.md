# AI Smart Factory Agent Office

저장된 제조설비 측정 데이터를 ML로 분석하고, 기술문서 Evidence를 이용해 진단·점검·조치 권고까지 연결하는 **Evidence-grounded AI Agent MVP**입니다.

> 현재 입력은 Paderborn의 저장 Measurement Replay입니다. 실제 공장 센서의 연속 수집이나 PLC 자동제어 기능은 포함하지 않습니다.

![현재 통합 관제 화면 · 진단 대기 상태](artifacts/ui/agent_office/integrated_control_20261016.png)

### Live Demo
https://factory.aipath.kr

> 심사 및 검증을 위한 외부 접속 주소입니다.

## Final Deliverables | 최종 제출 산출물

AI Native Final Project의 공식 제출 산출물입니다.

| 번호 | 제출 산출물 | 내용 | 링크 |
|---|---|---|---|
| ① | 프로젝트 기획서 | 문제 정의, 목표, AI 활용 방식 및 추진 계획 | [기획서](docs/01_%E1%84%91%E1%85%B3%E1%84%85%E1%85%A9%E1%84%8C%E1%85%A6%E1%86%A8%E1%84%90%E1%85%B3_%E1%84%80%E1%85%B5%E1%84%92%E1%85%AC%E1%86%A8%E1%84%89%E1%85%A5.md) |
| ② | 기능 요구 명세서 | 기능·비기능 요구사항, 시스템 아키텍처, AI 활용 명세 및 RTM | [요구 명세서](docs/02_%E1%84%80%E1%85%B5%E1%84%82%E1%85%B3%E1%86%BC_%E1%84%8B%E1%85%AD%E1%84%80%E1%85%AE_%E1%84%86%E1%85%A7%E1%86%BC%E1%84%89%E1%85%A6%E1%84%89%E1%85%A5.md) |
| ③ | 배포 URL | 실제 서비스 접속 및 기능 시연 | [Live Demo](https://factory.aipath.kr) |
| ④ | GitHub 저장소 URL | 소스코드, 구현 구조 및 개발 결과 | [현재 저장소](./) |
| ⑤ | 사용자 피드백 기록 | Google Forms 설문 분석 및 피드백 기반 UI 개선 결과 | [피드백 기록](docs/03_%E1%84%89%E1%85%A1%E1%84%8B%E1%85%AD%E1%86%BC%E1%84%8C%E1%85%A1_%E1%84%91%E1%85%B5%E1%84%83%E1%85%B3%E1%84%87%E1%85%A2%E1%86%A8_%E1%84%80%E1%85%B5%E1%84%85%E1%85%A9%E1%86%A8.md) |
| ⑥ | 서면 심사용 발표자료 | 프로젝트 주요 성과와 AI 기술 활용 및 사용자 검증 결과 | [발표자료 PDF](docs/04_%E1%84%8E%E1%85%AC%E1%84%8C%E1%85%A9%E1%86%BC_%E1%84%87%E1%85%A1%E1%86%AF%E1%84%91%E1%85%AD%E1%84%8C%E1%85%A1%E1%84%85%E1%85%AD.pdf) |
| ⑦ | 시연영상 | 주요 기능과 Agent Workflow 시연(3분 이내) | [시연영상 MP4](docs/05_%E1%84%89%E1%85%B5%E1%84%8B%E1%85%A7%E1%86%AB%E1%84%8B%E1%85%A7%E1%86%BC%E1%84%89%E1%85%A1%E1%86%BC.mp4) |

### 평가자 안내

- **서비스 접속:** [Live Demo](https://factory.aipath.kr)
- **프로젝트 문서:** 기획서, 기능 요구 명세서, 사용자 피드백 기록
- **서면 심사:** 최종 발표자료 PDF
- **기능 시연:** 3분 이내 시연영상
- **소스코드:** [현재 GitHub 저장소](./)
- **팀 역할·산출물:** [팀원별 역할 및 업무분장](docs/06_%E1%84%90%E1%85%B5%E1%86%B7%E1%84%8B%E1%85%AF%E1%86%AB%E1%84%87%E1%85%A7%E1%86%AF_%E1%84%8B%E1%85%A7%E1%86%A8%E1%84%92%E1%85%A1%E1%86%AF_%E1%84%86%E1%85%B5%E1%86%BE_%E1%84%8B%E1%85%A5%E1%86%B8%E1%84%86%E1%85%AE%E1%84%87%E1%85%AE%E1%86%AB%E1%84%8C%E1%85%A1%E1%86%BC.md)

평가용 계정 정보는 보안을 위해 별도로 제공하며,
GitHub 저장소에는 공개하지 않습니다.

본 시스템은 저장된 Paderborn Measurement를 기반으로
ML 이상탐지, RAG 기술문서 검색, LangGraph 진단 Workflow,
HITL 검토 및 최종 보고서 생성을 지원하는 MVP입니다.
실시간 현장 센서 수집과 자동 설비 제어는 포함하지 않습니다.

> **링크 확인 안내:** 위 5개 산출물 파일의 GitHub 경로는 2026-10-16 기준 확인했습니다.

### 팀 역할과 산출물 분류

| 팀원 | 담당 영역 | 관련 소스 |
|---|---|---|
| 이승훈 | 시스템 통합·Backend API·배포 | `backend/app/api/v1/`, `backend/app/core/` |
| 남병광 | Paderborn 데이터·ML | `backend/app/data/`, `backend/app/ml/` |
| 김보미 | 기술문서·RAG | `backend/app/rag/` |
| 이혜경 | LangGraph·HITL·Memory | `backend/app/agent/`, `backend/app/memory/` |
| 김시율 | Agent Office UI·사용자 경험 | `frontend/src/` |

역할별 관련 시험 결과와 문서는 [팀원별 역할 및 업무분장](docs/06_%E1%84%90%E1%85%B5%E1%86%B7%E1%84%8B%E1%85%AF%E1%86%AB%E1%84%87%E1%85%A7%E1%86%AF_%E1%84%8B%E1%85%A7%E1%86%A8%E1%84%92%E1%85%A1%E1%86%AF_%E1%84%86%E1%85%B5%E1%86%BE_%E1%84%8B%E1%85%A5%E1%86%B8%E1%84%86%E1%85%AE%E1%84%87%E1%85%AE%E1%86%AB%E1%84%8C%E1%85%A1%E1%86%BC.md)에 정리했습니다. 이 표는 기능 영역별 산출물 분류이며, 개인별 수행 기록은 문서의 확인 자료와 연결해 관리합니다.

### 팀 협업 및 개발 기록

본 프로젝트는 팀원별 역할 분담을 기반으로 기획, 개발, 테스트 및 시스템 개선을 수행했습니다.

프로젝트 진행 과정에서 생성된 회의 기록, 개발 협업 내역, 사용자 테스트 및 개선 활동 자료는 다음에서 확인할 수 있습니다.

| 구분 | 주요 내용 | 자료 |
|---|---|---|
| Discord 협업 기록 | 개발 진행 상황 공유, 기술 논의 및 문제 해결 과정 | [협업 기록](docs/team_collaboration/Discord_capture/) |
| 팀 회의 기록 | 프로젝트 주제 선정, 개발 진행 점검 및 회의 자료 | [회의 자료](docs/team_collaboration/Meetings/) |
| 사용자 테스트 및 설문 | Google Forms 설문, 사용자 응답 및 분석 자료 | [설문 및 분석 자료](docs/team_collaboration/실사용자테스트_설문및분석자료/) |
| 앱 테스트 및 개선 | 시스템 점검, 오류 확인 및 수정·보완 사항 | [앱 테스트 기록](docs/team_collaboration/앱테스트_리포트/) |

협업 자료는 프로젝트 진행 과정과 팀원들의 참여 활동을 확인하기 위한 보조 증빙이며, 공식 제출 산출물과 구분됩니다.

## 1. Problem

제조설비 이상이 발견된 뒤 기술문서 검색, 원인 검토, 점검 계획 작성, 조치 판단이 서로 분리되어 있으면 담당자의 경험과 반복적인 수작업에 크게 의존합니다. 판단 근거와 실행 이력을 함께 추적하기도 어렵습니다.

## 2. Solution

AI Smart Factory Agent Office는 하나의 Measurement에서 다음 흐름을 연결합니다.

- 저장 신호 Replay와 Feature Extraction
- Random Forest 정상·손상 분류
- 손상 경로의 RAG 기술 근거 검색
- Evidence 기반 진단과 근거 충족 검증
- 점검 계획과 조치 권고
- 중요 조치의 Human-in-the-Loop 검토
- Final Report, Run History, Checkpoint, Equipment Memory 저장
- AgentEvent SSE 기반 진행 상태 표시

## 3. End-to-End Agent Workflow

```mermaid
flowchart TD
    A[Recorded Paderborn Measurement] --> B[Feature Extraction]
    B --> C[Random Forest Detection]
    C --> D{Normal or Abnormal}
    D -->|NORMAL| E[Skip RAG and Diagnosis]
    E --> F[Normal Report]
    D -->|ABNORMAL| G[RAG Retrieval]
    G --> H[Evidence and Citation]
    H --> I[Diagnosis]
    I --> J[Evidence Verification]
    J --> K[Inspection Plan]
    K --> L[Action Recommendation]
    L --> M{Human Review Required}
    M -->|No| N[Final Report]
    M -->|Yes| O[HITL Waiting]
    O --> P[Approve, Revise, or Reject]
    P --> Q[Checkpoint Resume]
    Q --> N
    F --> R[Run History and Memory]
    N --> R
```

## 4. Representative Scenarios

| 시나리오 | 실제 입력 | 검증 경로 |
|---|---|---|
| A · 정상 | `paderborn:K001:N09_M07_F10:01` | ML `normal` → RAG 생략 → Normal Report → `COMPLETED` |
| B · 손상 | `paderborn:KA01:N09_M07_F10:01` | ML `abnormal` → RAG → Evidence → Diagnosis → Inspection → Action → Final Report |
| C · HITL 시연 | `paderborn:KA01:N09_M07_F10:02` + `HITL_CONTROLLED` | 실제 Measurement와 ML·RAG를 사용하고, 공개된 통제 조건으로 중요 조치 검토를 발생시켜 `WAITING → Human Input → Resume → COMPLETED`를 확인 |

시나리오 C의 통제 조건은 HITL과 Checkpoint Resume 시연용입니다. 설비 정지 명령을 실행하거나 원본 Measurement의 정답을 변경하지 않습니다.

## 5. AI Agent 6 Elements

| 요소 | 현재 구현 |
|---|---|
| Goal | Measurement를 분석하고 추적 가능한 진단 지원 보고서를 완성합니다. |
| Planning | `backend/app/agent/graph.py`의 LangGraph node와 conditional edge가 실행 순서를 결정합니다. |
| Reasoning | `backend/app/agent/reasoning.py`가 Evidence 기반 후보와 검증 결과를 구조화합니다. |
| Tool Use | Paderborn Adapter, ML inference, Chroma retrieval, Vision observation, Memory repository를 호출합니다. |
| Memory | Run/Event DB, LangGraph Checkpoint, Equipment Memory를 목적별 SQLite 저장소에 분리합니다. |
| Feedback | Evidence 재검색, 추가정보 요청, HITL 승인·수정·거절, SSE 상태 갱신을 다음 상태에 반영합니다. |

현재 검증된 핵심 경로는 외부 LLM의 자유 생성에 의존하지 않고 결정론적 reasoner와 planner를 사용합니다.

## 6. Architecture

```text
Next.js Frontend
  └─ REST / SSE
FastAPI Backend
  ├─ Paderborn Data Adapter / Replay API
  ├─ Feature Pipeline / Random Forest
  ├─ RAG / Chroma / Evidence
  ├─ LangGraph / HITL / Checkpoint
  ├─ Run History / Equipment Memory
  └─ Optional Vision Observation

Storage
  ├─ Model artifact and evaluation files
  ├─ Chroma vector collection
  └─ Run, Checkpoint, Memory, Vision SQLite stores
```

Source of truth는 Measurement Adapter, `AnalysisResult`, `EvidenceObject`, LangGraph `AgentState`, Equipment Memory, `VisualObservation`, persisted Run/Event로 분리되어 있습니다.

## 7. Technology Stack

| 영역 | 기술 |
|---|---|
| Backend | Python 3.11+, FastAPI, Pydantic, Uvicorn |
| ML | scikit-learn, RandomForestClassifier, NumPy, SciPy, joblib |
| Agent | LangGraph 1.2.x |
| RAG | Chroma 1.x, local HashingVectorizer |
| Storage | SQLite, Chroma persistence |
| Frontend | Next.js 16.3.5, React 19, TypeScript 5.9 |
| Test | pytest, Node test runner, TypeScript compiler, Next.js production build |

정확한 Python 호환 범위는 [backend/requirements.txt](backend/requirements.txt), Frontend 버전은 [frontend/package.json](frontend/package.json)을 기준으로 합니다.

## 8. Data

- Source: [Paderborn University Bearing DataCenter](https://mb.uni-paderborn.de/en/kat/research/bearing-datacenter)
- Official dataset page: [Data Sets and Download](https://mb.uni-paderborn.de/en/kat/research/bearing-datacenter/data-sets-and-download)
- Official download index: [KAt BearingDataCenter](https://groups.uni-paderborn.de/kat/BearingDataCenter/)
- 현재 대표 subset: `K001`, `KA01`, `KI01`
- Measurement: 240건
- Class: healthy 80건, damaged 160건
- 채널: `vibration_1`, `phase_current_1`, `phase_current_2`, `speed`, `torque`, `force`, temperature metadata
- UI Replay: 저장된 MAT 신호와 운전값을 동일 normalized timeline에서 재생

Paderborn Dataset과 Dataset에 포함된 Fact Sheet·Measurement Log는
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) 조건을 따릅니다.
비상업적 이용과 재배포에는 출처표시, 라이선스 링크, 변경 여부 표시가 필요하며,
상업적 이용은 Paderborn University 측의 별도 허가를 확인해야 합니다.

원본 RAR/MAT 학습데이터는 저장소에 포함하지 않습니다. 공식 원본에서 로컬로 내려받는
방법은 [Setup](#16-setup), 상세한 출처·재배포 범위는
[Sources / Attribution](#22-sources--attribution)을 참조하십시오. 현장 Sensor, MQTT,
OPC-UA, API 입력이 확보되면 Measurement Adapter 앞단을 교체·확장할 수 있으나,
해당 실시간 수집기는 현재 구현되어 있지 않습니다.

## 9. ML

| 항목 | 현재 값 |
|---|---|
| Model ID | `bearing_rf_binary_v1` |
| Algorithm | `RandomForestClassifier` v1.0 |
| Model Artifact | `artifacts/ml/baseline_v1/model.joblib` |
| Training Data | Paderborn `K001`, `KA01`, `KI01` |
| Training Type | Paderborn 측정데이터를 이용한 별도 Random Forest supervised training (사전학습 모델 Fine-tuning 아님) |
| Input | 3개 신호 채널에서 추출한 36개 Feature |
| Window | 1초, overlap 0% |
| Split | Measurement ID 기준 stratified group split |
| Train / Test | 180 / 60 Measurements, 718 / 239 Windows |

현재 test split의 Accuracy와 F1은 1.0이지만, 세 Bearing ID가 train/test 양쪽에 모두 포함되어 있습니다. 따라서 이는 대표 subset 내부 재현 결과이며 unseen-bearing 또는 현장 일반화 성능 100%를 의미하지 않습니다. UI confidence 역시 calibration을 거친 실제 고장 확률이 아닙니다.

## 10. RAG / Knowledge

| 항목 | 현재 값 |
|---|---|
| Knowledge Pack | `bearing_v1` v1.0 |
| Documents | 15 |
| Chunks / Embeddings | 183 / 183 |
| Vector DB | Chroma, collection `bearing_v1` |
| Embedding | `sklearn-hashing-vectorizer-v1` |
| Dimension / Distance | 384 / cosine |

검색 결과는 문서명, 발행기관, 페이지, 섹션과 함께 `EvidenceObject`로 변환됩니다. UI의 검색 점수는 `1 - cosine distance` 기반 상대 순위 신호이며 정답 확률이나 진단 신뢰도가 아닙니다.

## 11. Human-in-the-Loop

`SHUTDOWN_CHECK`, `SCHEDULE_MAINTENANCE`, 또는 High priority 조치는 사람 검토가 필요하도록 정책이 적용됩니다.

```text
RUNNING → WAITING → Human decision → RUNNING → COMPLETED
```

Backend는 `POST /api/v1/agent/runs/{run_id}/human-input`으로 승인·수정 요청·거절을 받고, 동일 `run_id`와 LangGraph thread의 Checkpoint에서 Workflow를 재개합니다. 추가 정보가 필요한 경우에도 별도의 Human Request로 일시정지합니다.

## 12. Safety

- No direct PLC control
- No automatic equipment shutdown
- No interlock bypass
- No automatic maintenance execution
- 중요한 권고는 Human Approval이 필요할 수 있음

본 시스템은 설비 자동제어가 아닌 **의사결정 지원 시스템**입니다.

## 13. Traceability

Run, ordered Agent Event, Human Request, Evidence/Citation, LangGraph Checkpoint, Equipment Memory, Vision metadata, Final Report를 분리 저장합니다. 진단 이력 조회는 Workflow를 다시 실행하거나 Memory를 추가하지 않고 저장된 상태와 보고서를 복원합니다. SSE는 센서 스트리밍이 아니라 Agent Event 진행 상태를 전달합니다.

## 14. Existing Assets vs New Development

### External / Existing Assets

- Paderborn Bearing DataCenter Dataset 및 관련 공식 자료
- SKF 기술문서 원문
- Python, FastAPI, scikit-learn, LangGraph, Chroma, SQLite
- Next.js, React, TypeScript

### Newly Developed for This Project

- Paderborn Measurement Adapter와 저장 신호 Replay
- 36-Feature pipeline 연동과 ML inference service
- Knowledge manifest, ingestion, retrieval, Evidence traceability
- LangGraph 진단 Workflow와 bounded retry
- Diagnosis, Evidence Verification, Inspection Plan, Action Recommendation
- HITL policy, Human Request, Checkpoint Resume
- Equipment Memory, Run History, AgentEvent SSE
- Agent Office와 History / Knowledge / Model / System 화면
- 선택형 이미지 품질 관찰과 센서·RAG Evidence 분리

오픈소스 프레임워크 자체는 신규 개발분으로 주장하지 않습니다.

## 15. Project Structure

```text
backend/              FastAPI, ML, RAG, Agent, Memory, Vision, tests
frontend/             Next.js application and frontend tests
config/               frozen MVP interface and demo scenarios
data/                 dataset metadata and local raw-data location
knowledge/            source manifest and local knowledge locations
artifacts/ml/         active model and evaluation artifacts
artifacts/rag/        bounded RAG evaluation artifacts
artifacts/ui/         demo screenshots
docs/supporting/     supporting reports and evidence documents
scripts/              acquisition, ingestion, evaluation, verification tools
```

## 16. Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- npm 10+
- Paderborn/SKF 공식 자료 다운로드를 위한 인터넷 연결
- RAR 추출이 가능한 로컬 도구

### Environment and source preparation

저장소 루트에서 실행합니다.

대표 학습데이터 3종(`K001`, `KA01`, `KI01`)과 RAG 문서를 함께 내려받고 압축을 해제합니다.

```bash
cp .env.example .env
python3 scripts/download_project_sources.py --dataset sample --extract
```

필요한 자산만 내려받으려면 다음 명령을 사용합니다.

```bash
# RAG 문서만 다운로드
python3 scripts/download_project_sources.py --dataset none

# 대표 학습데이터 3종만 다운로드·압축 해제
python3 scripts/download_project_sources.py --dataset sample --skip-documents --extract

# 전체 Paderborn 학습데이터 32종만 다운로드·압축 해제
python3 scripts/download_project_sources.py --dataset all --skip-documents --extract
```

다운로드 스크립트는 아래 공식 배포처만 사용합니다.

- Paderborn Dataset: <https://groups.uni-paderborn.de/kat/BearingDataCenter/>
- Paderborn Dataset 안내: <https://mb.uni-paderborn.de/en/kat/research/bearing-datacenter/data-sets-and-download>
- Paderborn Benchmark Paper: <https://mb.uni-paderborn.de/fileadmin-mb/kat/PDF/Veroeffentlichungen/20160703_PHME16_CM_bearing.pdf>
- SKF 문서 URL과 파일별 조건: [Source Manifest](knowledge/bearing_v1/manifests/SOURCE_MANIFEST.md)

원본 RAR/MAT, 다운로드한 웹페이지·외부 기술문서 및 생성된 Chroma Vector DB는 로컬에서만
사용하고 Git에 포함하지 않습니다. Paderborn 압축파일에서 추출한 소형 Fact Sheet와
Measurement Log PDF만 원본 그대로 저장소에 포함하며, CC BY-NC 4.0 조건을 유지합니다.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cd ..
backend/.venv/bin/python scripts/ingest_knowledge_pack.py --pack bearing_v1
```

활성 Random Forest artifact는 `artifacts/ml/baseline_v1/model.joblib`에 포함됩니다. 직접 재학습하려면 [data/paderborn/README.md](data/paderborn/README.md)의 절차를 따릅니다.

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm ci
```

## 17. Run

터미널 1:

```bash
cd backend
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

터미널 2:

```bash
cd frontend
npm run dev
```

- UI: <http://localhost:3000>
- Backend health: <http://localhost:8000/api/v1/health>
- OpenAPI: <http://localhost:8000/docs>

## 18. Test

```bash
cd backend
.venv/bin/pytest -q
```

```bash
cd frontend
npm test
npm run lint
npm run build
```

2026-10-16 자동 검증 결과:

- Backend: 162 passed
- Frontend: 33 passed
- TypeScript: passed
- Next.js production build: passed, 7 routes

2026-10-05 시나리오 검증 기록: Runtime A/B/C 모두 `COMPLETED`, Final Report 복원 가능. 세부 증빙은 [TEST_RESULTS.md](docs/supporting/TEST_RESULTS.md)를 참조합니다.

## 19. Known Limitations

- Recorded Data 기반이며 실제 공장 Sensor Streaming이 아닙니다.
- 세 Bearing ID가 train/test에 공유되어 unseen-bearing generalization은 검증되지 않았습니다.
- HashingVectorizer는 다국어 semantic embedding이 아니며 사용자 한국어 검색만 제한적 규칙 기반 영문 query로 변환합니다.
- Vision provider는 해상도·밝기·대비·사용 가능성을 관찰하며 고장 판독 모델이 아닙니다.
- 실제 PLC 제어, 자동 설비 정지, 정비 실행 기능이 없습니다.
- 원본 Dataset, 저작권 기술문서, Chroma index와 Runtime DB는 Git에 포함하지 않습니다.

## 20. KAMP CNC Expansion PoC

기존 Paderborn 기반 Production E2E와 독립적으로, KAMP 「정밀가공 품질보증 AI 데이터셋」을 이용해 다른 제조 도메인으로의 **Data Adapter 및 Knowledge/RAG 확장 가능성**을 별도 PoC로 검증했습니다.

```text
KAMP CNC Data
    ↓
KAMPCNCAdapter
    ↓
Ground Truth Context
    ↓
kamp_cnc_v1 RAG
    ↓
Evidence / Abstention
```

### 검증 결과

- Dataset: **1,085 observations / 43 columns**
- Ground Truth: **PASS 986 / FAIL 99**
- CNC Adapter: **1,085 / 1,085 observations 변환**
- Feature mismatch: **0**
- Validation failure: **0**
- Adapter + RAG Tests: **29 / 29 passed**
- Knowledge Pack: **`kamp_cnc_v1` / 49 chunks**
- FAIL Observation Retrieval: **3 / 3**
- Abstention Checks: **3 / 3**
- Production Code / DB / Chroma 변경: **0**

### 검증 범위

- `passorfail`의 `0=PASS`, `1=FAIL`은 KAMP 데이터셋이 제공하는 **Ground Truth**입니다.
- CNC 상태는 본 PoC에서 새로 학습한 ML Prediction이 아닙니다.
- CNC 전용 ML 모델의 학습 및 Accuracy/F1 평가는 수행하지 않았습니다.
- 현장 일반화 검증은 수행하지 않았으며, 현장 일반화 성능을 주장하지 않습니다.
- Sensor Feature만으로 특정 고장 원인을 확정하지 않습니다.
- RAG Knowledge Source는 해당 KAMP 데이터셋의 **공식 Guidebook**만 사용했습니다.
- Evidence가 부족하거나 범위를 벗어나는 요청에는 Abstention 정책을 적용했습니다.
- 기존 Paderborn Production E2E와 완전히 독립된 실험입니다.

### Paired Observation

실제 데이터 감사 과정에서 동일 `SerialNo`와 동일 `ReceivedDateTime`을 가진 99개 쌍이 확인되었습니다.

- 각 쌍은 PASS 1개와 FAIL 1개로 구성됩니다.
- 99개 쌍 모두 Feature vector가 서로 달랐습니다.
- 동일 Feature에 Label만 다른 사례는 없었습니다.
- 원본 Row를 병합하거나 Label을 수정하지 않았습니다.
- 복수 Observation의 생성 원인은 공식 자료에서 확인되지 않아 임의로 추론하지 않았습니다.

상세 구현, 데이터 감사, Adapter/RAG 검증 결과는 [`poc/kamp_cnc/README.md`](poc/kamp_cnc/README.md)를 참고하십시오.

## 21. Supporting Documents

- [개발완료보고서](docs/supporting/development_completion_report.md)
- [AI Agent 기술설명서](docs/supporting/agent_technical_description.md)
- [구현 감사 결과](docs/supporting/implementation_audit.md)
- [출처 및 AI 활용 내역](docs/supporting/SOURCES_AND_AI_USAGE.md)
- [테스트 결과](docs/supporting/TEST_RESULTS.md)

## 22. Sources / Attribution

### External data and documents

| 자산 | 공식 출처 | 라이선스·저장소 정책 |
|---|---|---|
| Paderborn Measurement Dataset | [Bearing DataCenter](https://mb.uni-paderborn.de/en/kat/research/bearing-datacenter), [공식 다운로드](https://groups.uni-paderborn.de/kat/BearingDataCenter/) | [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). 원본 RAR/MAT는 Git 제외 |
| Paderborn Fact Sheet / Measurement Log | Dataset 공식 압축파일에 포함 | CC BY-NC 4.0. `data/paderborn/docs/`의 PDF는 원본에서 수정하지 않은 파일이며 프로젝트 코드와 별도 라이선스 적용 |
| Paderborn Benchmark Paper | [Official PDF](https://mb.uni-paderborn.de/fileadmin-mb/kat/PDF/Veroeffentlichungen/20160703_PHME16_CM_bearing.pdf) | 문서에 표시된 별도 CC Attribution 조건 적용. 로컬 다운로드만 허용하고 Git 제외 |
| Paderborn 공식 웹페이지 | [Bearing DataCenter](https://mb.uni-paderborn.de/en/kat/research/bearing-datacenter) | 웹페이지 재배포 조건이 별도로 확인되지 않아 로컬 다운로드만 허용하고 Git 제외 |
| SKF 기술문서 | [파일별 공식 URL과 조건](knowledge/bearing_v1/manifests/SOURCE_MANIFEST.md) | SKF 저작권 자산. 재배포 권한이 확인되지 않아 로컬 다운로드만 허용하고 Git 제외 |
| KAMP 정밀가공 품질보증 AI 데이터셋 / Guidebook | [Korea AI Manufacturing Platform (KAMP)](https://www.kamp-ai.kr/) | 중소벤처기업부·스마트제조혁신추진단(㈜인터엑스), 2022.12.23. 원본 CSV/PDF 및 원문 파생 Chunk/Index는 Git 제외 |

### Required Paderborn attribution

이 저장소에 포함된 Paderborn Dataset 파생 자료와 Fact Sheet·Measurement Log의 출처는
다음과 같습니다.

> Christian Lessmeier et al., KAt-DataCenter, Chair of Design and Drive
> Technology, Paderborn University,
> <https://mb.uni-paderborn.de/en/kat/research/bearing-datacenter>

- License: [Creative Commons Attribution-NonCommercial 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/)
- Included PDF changes: none; files were copied unchanged from the official Dataset archives.
- Commercial use: contact Paderborn University / the Dataset author before use.

### Required KAMP attribution

KAMP CNC Expansion PoC에서 사용한 데이터셋과 공식 Guidebook의 출처는 다음과 같습니다.

> 중소벤처기업부, Korea AI Manufacturing Platform(KAMP),  
> 정밀가공 품질보증 AI 데이터셋,  
> 스마트제조혁신추진단(㈜인터엑스), 2022.12.23.  
> <https://www.kamp-ai.kr/>

KAMP 원본 CSV와 Guidebook PDF 및 원문 파생 Chunk/Index는 Git에 포함하지 않습니다. PoC에는 공개 가능한 구현 코드, 테스트 및 집계된 검증 결과만 포함합니다.

Dataset, 기술문서, 오픈소스 라이브러리, AI 개발도구의 파일별 출처·사용 범위·체크섬은
[SOURCES_AND_AI_USAGE.md](docs/supporting/SOURCES_AND_AI_USAGE.md)와
[canonical source manifest](knowledge/bearing_v1/manifests/source_manifest.json)에 정리했습니다.
외부 자산에는 각 권리자의 라이선스와 이용조건이 계속 적용됩니다. 이 저장소에는 현재
프로젝트 전체에 적용되는 별도 오픈소스 라이선스가 선언되어 있지 않으므로, 저장소 공개가
프로젝트 코드의 자유로운 복제·재사용을 허가한다는 의미는 아닙니다.
