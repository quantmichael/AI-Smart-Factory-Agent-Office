# AI Smart Factory Agent Office

## 04. RAG Design

**문서 버전:** v0.1\
**선행 문서:** `01_PROJECT_OVERVIEW.md`, `02_SYSTEM_ARCHITECTURE.md`,
`03_DATA_ML_DL_DESIGN.md`\
**목적:** 센서 ML/DL 분석 결과를 실제 기술 근거와 연결하는 RAG
지식베이스, 문서 수집·가공·검색·검증·인용 구조를 정의한다.

------------------------------------------------------------------------

## 1. RAG 설계의 핵심 원칙

본 프로젝트에서 RAG는 부가 기능이 아니다.

핵심 구조는 다음과 같다.

``` text
Sensor Dataset
      ↓
ML/DL Detection
      ↓
Structured Analysis Result
      ↓
RAG Technical Evidence
      ↓
LangGraph Diagnosis / Verification
      ↓
Inspection / Recommended Action
```

가장 중요한 원칙은 **ML/DL 데이터와 RAG 문서가 동일한 진단 도메인에서
연결되어야 한다**는 것이다.

초기 Reference Domain은 `rolling bearing condition monitoring`이다.

------------------------------------------------------------------------

## 2. 초기 Knowledge Pack

초기 RAG Corpus는 하나의 `Bearing Knowledge Pack`으로 구성한다.

``` text
knowledge/
└── bearing/
    ├── dataset_docs/
    ├── damage_fact_sheets/
    ├── test_rig_docs/
    ├── vibration_diagnosis/
    ├── bearing_failure/
    ├── inspection/
    ├── maintenance/
    └── failure_cases/
```

Paderborn 공식 데이터는 26개 damaged state와 6개 healthy state를
제공하고, 손상 상태에 대한 uniform fact sheet와 measurement log를
데이터와 함께 제공한다.

Paderborn 손상 분류는 41개 설명 기준을 계층적으로 구성하며,
bearing/application/damage 정보를 포함한다. Damage는 ISO 15243 기준의
type/subtype, location, geometry, occurrence 등을 기술한다.

따라서 Sensor Dataset과 RAG Corpus 사이에 다음 연결고리를 만들 수 있다.

``` text
Bearing ID
Operating Condition
Damage Type
Damage Location
Damage Geometry
Measurement
       ↕
Fact Sheet / Measurement Log
       ↕
External Diagnostic / Maintenance Knowledge
```

------------------------------------------------------------------------

## 3. 문서 Source Tier

RAG는 출처 신뢰도를 Metadata에 기록한다.

### Tier 1 --- Dataset Primary Source

최우선.

-   Paderborn Bearing DataCenter
-   Data Sets and Download
-   Bearing Damage documentation
-   Test Rig and Measurement Equipment
-   Operating Conditions
-   Dataset publication
-   Damage Fact Sheets
-   Measurement Logs

용도:

``` text
"이 데이터가 무엇인가?"
"어떤 장비와 센서인가?"
"어떤 손상인가?"
"어떤 조건에서 측정했는가?"
```

### Tier 2 --- Manufacturer / Technical Primary Source

예:

-   SKF Vibration Diagnostic Guide
-   SKF Bearing Damage and Failure Analysis
-   제조사 유지보수/점검 자료

용도:

``` text
"이 진동 특징은 무엇을 의미할 수 있는가?"
"어떤 원인을 점검해야 하는가?"
"어떤 정비 절차가 권장되는가?"
```

### Tier 3 --- Standards / High-quality Engineering Reference

예:

-   ISO 15243 관련 공개 설명자료
-   공식 기술기관 자료
-   검증 가능한 연구 논문

### Tier 4 --- Secondary Reference

보조 용도로만 사용.

-   교육자료
-   기술 블로그
-   기타 설명자료

최종 진단 근거는 가능한 한 Tier 1\~3을 우선한다.

------------------------------------------------------------------------

## 4. 핵심 Reference Documents

초기 Knowledge Pack에 우선 포함할 자료군:

### Paderborn

1.  Bearing DataCenter overview
2.  Data Sets and Download
3.  Bearing Damage documentation
4.  Test Rig and Measurement Equipment
5.  Operating Conditions
6.  Benchmark publication
7.  개별 Bearing Damage Fact Sheets
8.  Measurement Logs

### SKF / Bearing Technical Knowledge

1.  Vibration Diagnostic Guide
2.  Bearing Damage and Failure Analysis
3.  ISO 15243 bearing damage 관련 공개 기술자료
4.  Bearing inspection / vibration monitoring 자료

SKF Vibration Diagnostic Guide는 문제의 **Detection과 Cause Analysis를
구분**하며, vibration amplitude와 frequency를 이용해 machinery problem을
분석하는 기본 틀을 제공한다.

SKF Bearing Damage and Failure Analysis 자료는 vibration monitoring,
temperature monitoring, lubrication, shutdown inspection 및 bearing
damage 진행과 관련된 실무적 점검 정보를 제공한다.

------------------------------------------------------------------------

## 5. 문서 수집 Manifest

RAG 문서는 임의로 폴더에 넣지 않는다.

`document_manifest.csv` 또는 DB에서 관리한다.

예:

``` csv
document_id,title,source,source_tier,document_type,equipment_type,component,version,language,license,origin
PBD-001,Bearing Damage,Paderborn,1,dataset_doc,bearing,bearing,current,en,source-specific,...
SKF-001,Vibration Diagnostic Guide,SKF,2,diagnostic_guide,rotating_machine,bearing,...,en,source-specific,...
```

필수 관리 항목:

``` text
document_id
title
publisher
source_tier
document_type
equipment_type
component
fault_type
language
version/date
license
origin
ingested_at
checksum
```

------------------------------------------------------------------------

## 6. Document Type

초기 Enum:

``` text
dataset_doc
fact_sheet
measurement_log
test_rig_doc
research_paper
diagnostic_guide
failure_analysis
inspection_guide
maintenance_guide
failure_case
standard_reference
```

Document Type은 Retrieval Filter에서 사용한다.

------------------------------------------------------------------------

## 7. Parsing Pipeline

``` text
Source Document
      ↓
Download / Register
      ↓
Checksum
      ↓
Parser
      ↓
Text Cleaning
      ↓
Section Detection
      ↓
Chunking
      ↓
Metadata Enrichment
      ↓
Embedding
      ↓
Vector DB
```

### PDF

우선순위:

1.  Text-based PDF parser
2.  Table extraction
3.  필요할 때만 OCR

스캔 문서가 아닌데 OCR을 기본 적용하지 않는다.

### HTML

본문 영역을 추출하고 navigation/footer 등 불필요한 텍스트를 제거한다.

### Fact Sheet

일반 PDF와 동일하게 처리하지 않고 가능한 경우 구조화된 필드를 별도로
추출한다.

예:

``` json
{
  "bearing_id": "...",
  "damage_type": "...",
  "damage_location": "...",
  "damage_geometry": "...",
  "damage_origin": "real|artificial",
  "operating_context": "..."
}
```

------------------------------------------------------------------------

## 8. Chunking Strategy

기술문서는 고정 글자 수만으로 자르지 않는다.

### 기본

**Section-aware chunking**을 우선한다.

``` text
Document
 ├── Section
 │    ├── Paragraph
 │    ├── Table
 │    └── List
```

### 권장 초기값

실제 Retrieval 평가 전 임시 기준:

``` text
chunk size: 약 500~900 tokens
overlap: 약 80~150 tokens
```

단, 다음 자료는 별도 처리한다.

### Fact Sheet

Bearing 하나의 손상 설명이 짧으면 한 Fact Sheet를 하나 또는 소수 Chunk로
유지한다.

### Troubleshooting Table

행 단위 의미가 깨지지 않도록 table-aware chunking.

### Procedure

점검 절차의 순서를 보존한다.

------------------------------------------------------------------------

## 9. Metadata Schema

RAG 품질에서 매우 중요하다.

``` json
{
  "chunk_id": "SKF-001-sec03-ch02",
  "document_id": "SKF-001",
  "title": "Vibration Diagnostic Guide",
  "publisher": "SKF",
  "source_tier": 2,
  "document_type": "diagnostic_guide",
  "equipment_type": "rotating_machine",
  "component": "bearing",
  "bearing_type": null,
  "bearing_code": null,
  "fault_type": ["imbalance", "misalignment", "looseness"],
  "damage_location": null,
  "operating_condition": null,
  "section": "...",
  "page": 10,
  "language": "en",
  "source_origin": "...",
  "version": "...",
  "content_hash": "..."
}
```

Paderborn Fact Sheet는 추가로:

``` text
bearing_id
damage_type
damage_subtype
damage_location
damage_geometry
damage_occurrence
real_or_artificial
```

등을 저장한다.

------------------------------------------------------------------------

## 10. Vector DB

초기 MVP:

``` text
Chroma
```

또는

``` text
Qdrant
```

중 하나를 사용한다.

선택 기준:

-   Metadata filtering
-   local development
-   Docker deployment
-   팀 학습 난이도
-   향후 확장성

초기 개발 편의성이 중요하면 Chroma로 시작하고, 운영형 구조를 강조하려면
Qdrant를 검토한다.

------------------------------------------------------------------------

## 11. Embedding

초기에는 한 종류의 Embedding Model로 통일한다.

요구조건:

-   English technical document 검색 성능
-   Metadata filter와 병행
-   재색인 비용이 과도하지 않을 것

Embedding Model ID를 Index Metadata에 기록한다.

``` text
embedding_model
embedding_dimension
indexed_at
index_version
```

Embedding Model 변경 시 기존 Vector Index와 혼용하지 않는다.

------------------------------------------------------------------------

## 12. Retrieval Pipeline

초기 Retrieval:

``` text
Analysis Result
      ↓
Query Builder
      ↓
Metadata Filter
      ↓
Vector Search
      ↓
Top-K
      ↓
Evidence Filtering
      ↓
Agent
```

고도화:

``` text
Vector Search
      +
Keyword / BM25
      ↓
Hybrid Retrieval
      ↓
Reranker
      ↓
Final Evidence
```

처음부터 Hybrid + Reranker까지 모두 구현하지 않는다.

------------------------------------------------------------------------

## 13. ML/DL Result → RAG Query

이 프로젝트의 핵심 연결부다.

입력 예:

``` json
{
  "status": "abnormal",
  "predicted_class": "damaged",
  "confidence": 0.91,
  "features": {
    "rms": "...",
    "kurtosis": "...",
    "dominant_frequency": "..."
  },
  "rpm": 1500,
  "bearing_type": "6203"
}
```

Query Builder가 검색 목적을 분리한다.

### Query A --- Dataset Evidence

``` text
Find Paderborn documentation and fact sheets relevant to
6203 bearing damage under the current measurement context.
```

### Query B --- Diagnostic Evidence

``` text
Find technical references explaining bearing vibration patterns
consistent with elevated RMS/kurtosis and the observed frequency characteristics.
```

### Query C --- Inspection / Action

``` text
Find recommended inspection checks and maintenance actions
for the candidate bearing damage mechanisms.
```

하나의 거대한 Query보다 목적별 Retrieval을 권장한다.

------------------------------------------------------------------------

## 14. Evidence Object

Retriever 결과를 LLM 문자열로 바로 합치지 않는다.

표준 Evidence Object:

``` json
{
  "evidence_id": "EV-001",
  "chunk_id": "SKF-001-sec03-ch02",
  "document_id": "SKF-001",
  "title": "Vibration Diagnostic Guide",
  "publisher": "SKF",
  "source_tier": 2,
  "document_type": "diagnostic_guide",
  "page": 10,
  "section": "...",
  "content": "...",
  "retrieval_score": 0.82,
  "query_type": "diagnostic",
  "source_origin": "..."
}
```

Agent State에는 이 Object 목록을 저장한다.

------------------------------------------------------------------------

## 15. Diagnosis와 Retrieval 분리

Retriever가 진단하지 않는다.

``` text
Retriever:
관련 문서 검색

Diagnosis Node:
검색 근거 + ML 결과를 이용해 원인 후보 생성
```

이 경계를 명확하게 유지한다.

------------------------------------------------------------------------

## 16. Evidence Sufficiency

LangGraph의 중요한 Conditional Edge다.

Diagnosis 이후 `verify_evidence` Node가 다음을 검사한다.

``` text
관련 문서가 존재하는가?
출처 Tier가 충분한가?
ML 결과와 문서 근거가 실제로 연결되는가?
원인 후보에 직접 근거가 있는가?
점검/조치 근거가 있는가?
상충하는 근거가 있는가?
```

결과:

``` text
SUFFICIENT
PARTIAL
INSUFFICIENT
CONFLICTING
```

### 분기

``` text
SUFFICIENT
    ↓
Inspection Plan

PARTIAL
    ↓
Refine Query → Retrieve Again

INSUFFICIENT
    ↓
Request Additional Information / Human Check

CONFLICTING
    ↓
Retrieve More / Escalate
```

------------------------------------------------------------------------

## 17. Retry Policy

RAG 검색이 실패했다고 무한 반복하지 않는다.

예:

``` text
max_retrieval_retry = 2
```

2회 재검색 후에도 근거가 부족하면:

``` text
"현재 확보된 자료만으로 원인을 충분히 뒷받침하기 어렵습니다."
```

라고 상태를 명시한다.

------------------------------------------------------------------------

## 18. Citation / Evidence Display

최종 결과에는 최소 다음을 표시한다.

``` text
진단 후보
근거 요약
문서 제목
발행기관
페이지/섹션
Source Tier
```

UI 예:

``` text
Possible Cause
Bearing damage related vibration pattern

Evidence
[1] SKF — Vibration Diagnostic Guide, p.xx
[2] Paderborn — Bearing Damage Fact Sheet, Bearing ID ...
```

LLM이 존재하지 않는 출처를 만들어내지 않도록 Citation은 Retrieval 결과의
Metadata에서만 생성한다.

------------------------------------------------------------------------

## 19. Hallucination 방지

다음 규칙을 Prompt 및 Node에 적용한다.

1.  Evidence에 없는 고장 원인을 확정하지 않는다.
2.  `가능성이 있다`, `추가 확인 필요`와 `확인됨`을 구분한다.
3.  ML Prediction을 실제 고장 확인 결과로 표현하지 않는다.
4.  Source Metadata에 없는 페이지나 문서명을 생성하지 않는다.
5.  근거가 부족하면 부족하다고 답한다.
6.  위험한 정비 작업은 전문가 확인을 요구한다.

------------------------------------------------------------------------

## 20. Fact Sheet와 외부 문서 결합

중요한 설계 포인트다.

``` text
Paderborn Fact Sheet
        ↓
"What damage is associated with this experimental bearing?"
        ↓
External Technical Knowledge
        ↓
"What can cause this type of damage?"
"What should be inspected?"
"What action is normally considered?"
```

즉 Paderborn Fact Sheet는 **Dataset Ground Truth / Experimental
Context**, SKF 등의 문서는 **Diagnostic / Maintenance Knowledge** 역할을
한다.

둘을 동일한 문서처럼 취급하지 않는다.

------------------------------------------------------------------------

## 21. ISO 15243 연결

Paderborn Bearing Damage 체계는 damage를 ISO 15243 기준 type/subtype
등으로 설명한다.

SKF의 공개 bearing damage 자료 역시 ISO 15243의 failure mode
classification을 설명한다.

따라서 가능한 경우 다음 공통 Metadata를 사용한다.

``` text
iso_15243_category
damage_type
damage_subtype
damage_location
```

이 공통 Vocabulary가 Dataset과 RAG 사이의 중요한 Bridge가 된다.

------------------------------------------------------------------------

## 22. RAG Evaluation Dataset

RAG도 평가해야 한다.

최소 20\~30개의 평가 질문을 작성한다.

예:

``` text
Q1. 현재 Paderborn bearing ID의 damage type은 무엇인가?
Expected Source: Paderborn Fact Sheet

Q2. 특정 진동 특성이 어떤 rotating machinery problem과 관련될 수 있는가?
Expected Source: Diagnostic Guide

Q3. 해당 bearing damage에서 추가로 확인할 점검 항목은 무엇인가?
Expected Source: Failure Analysis / Inspection Guide
```

각 질문마다:

``` text
expected_document
expected_section
expected_keywords
answerable
```

를 저장한다.

------------------------------------------------------------------------

## 23. RAG 평가 Metric

초기에는 다음을 사용한다.

### Retrieval

-   Hit@K
-   Recall@K
-   MRR 또는 Rank 확인
-   expected source 포함 여부

### Answer Grounding

-   Citation correctness
-   Evidence support
-   Unsupported claim count
-   Answer completeness

### 운영 평가

-   Retrieval latency
-   Empty result rate
-   Retry rate

------------------------------------------------------------------------

## 24. Human Evaluation

기술문서 RAG는 자동 Metric만으로 끝내지 않는다.

평가자는 다음 질문에 답한다.

``` text
검색된 문서가 질문과 관련 있는가?
진단 근거가 실제 문서 내용과 일치하는가?
점검안이 근거와 연결되는가?
근거가 부족할 때 시스템이 과도하게 단정하지 않는가?
출처를 쉽게 확인할 수 있는가?
```

가능하면 제조/설비 관련 경험자 평가를 추가하되, MVP의 필수조건으로
두지는 않는다.

------------------------------------------------------------------------

## 25. Knowledge Base Versioning

문서가 추가되면 RAG 결과가 바뀔 수 있다.

따라서 다음을 기록한다.

``` text
knowledge_pack_version
document_manifest_version
embedding_model
chunking_version
indexed_at
```

진단 결과에도 사용한 Knowledge Pack 버전을 기록한다.

------------------------------------------------------------------------

## 26. Knowledge Pack 교체 구조

향후 Paderborn/Bearing에서 다른 설비로 이동할 때:

``` text
Current:
Bearing Dataset
+
Bearing Knowledge Pack

Future:
Pump Dataset
+
Pump Knowledge Pack
```

Agent Workflow 자체는 최대한 유지한다.

공통 Interface:

``` text
Dataset Adapter
ML/DL AnalysisResult
Domain Knowledge Pack
RAG Retriever
LangGraph Agent
```

------------------------------------------------------------------------

## 27. 초기 폴더 구조

``` text
rag/
├── manifests/
│   └── document_manifest.csv
├── documents/
│   └── bearing/
│       ├── dataset_docs/
│       ├── fact_sheets/
│       ├── diagnostic_guides/
│       ├── failure_analysis/
│       ├── inspection/
│       └── maintenance/
├── ingestion/
│   ├── loaders/
│   ├── parsers/
│   └── metadata/
├── chunking/
├── embeddings/
├── retrieval/
├── evaluation/
└── indexes/
```

------------------------------------------------------------------------

## 28. MVP 구현 순서

``` text
STEP 1
Paderborn 공식 문서 및 Fact Sheet 확보

STEP 2
SKF 등 신뢰도 높은 기술문서 확보

STEP 3
document_manifest 작성

STEP 4
PDF/HTML Parser 구현

STEP 5
Section-aware Chunking

STEP 6
Metadata 생성

STEP 7
Embedding + Vector DB

STEP 8
기본 Retrieval 테스트

STEP 9
ML/DL AnalysisResult 기반 Query Builder

STEP 10
Evidence Object 구현

STEP 11
LangGraph retrieve_knowledge Node 연결

STEP 12
verify_evidence Node 연결

STEP 13
Citation UI 연결

STEP 14
RAG Evaluation
```

------------------------------------------------------------------------

## 29. MVP 완료 기준

-   [ ] Paderborn Dataset Documentation 수집
-   [ ] Bearing Damage Fact Sheet 확보
-   [ ] 최소 2종 이상의 신뢰도 높은 외부 기술자료 확보
-   [ ] Document Manifest 작성
-   [ ] Parser 동작
-   [ ] Chunking 동작
-   [ ] Metadata 저장
-   [ ] Vector DB Index 생성
-   [ ] 기본 Semantic Retrieval 성공
-   [ ] ML/DL 결과 기반 Query 생성
-   [ ] Dataset Evidence 검색
-   [ ] Diagnostic Evidence 검색
-   [ ] Inspection/Action Evidence 검색
-   [ ] Citation 포함 결과 생성
-   [ ] Evidence 부족 시 재검색
-   [ ] RAG 평가 질문셋 구축
-   [ ] 최소 Retrieval 평가 수행

------------------------------------------------------------------------

## 30. RAG의 최종 역할

본 프로젝트의 RAG는 단순한 "매뉴얼 챗봇"이 아니다.

``` text
Sensor Signal
    ↓
ML/DL detects abnormal pattern
    ↓
RAG retrieves technical evidence
    ↓
LangGraph verifies evidence
    ↓
Agent forms diagnostic hypotheses
    ↓
Agent proposes additional inspection
    ↓
Agent provides evidence-grounded action guidance
```

즉 최종 시스템의 역할 분리는 다음과 같다.

``` text
ML/DL    = Detect
RAG      = Ground / Explain
LangGraph = Control / Verify / Branch
AI Agent = Diagnose / Coordinate / Recommend
```

------------------------------------------------------------------------

## 31. 다음 문서

다음 산출물:

**`05_LANGGRAPH_AGENT_DESIGN.md`**

다음 내용을 구체화한다.

-   Agent State Schema
-   Node별 입력/출력
-   Conditional Edge
-   RAG 재검색
-   Tool Calling
-   Error State
-   Human-in-the-loop
-   Long-term Memory 연결
-   Agent Event
-   AI Smart Factory Agent Office 실시간 상태 연결
-   End-to-End Graph
