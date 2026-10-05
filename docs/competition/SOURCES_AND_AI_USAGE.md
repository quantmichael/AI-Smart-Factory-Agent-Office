# Sources and AI Usage

확인일: 2026-10-05

이 문서는 외부 자산과 본 프로젝트 신규 개발분을 구분합니다. 확인되지 않은 라이선스는 추측하지 않습니다.

## Dataset and Technical Documents

| Name | Role | Source | License / Terms | Project Usage |
|---|---|---|---|---|
| Paderborn Bearing DataCenter | 저장 베어링 Measurement | [Paderborn University](https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter/data-sets-and-download) | CC BY-NC 4.0으로 확인됨; 출처표시·비상업 조건, 상업 사용은 별도 검토 필요 | K001, KA01, KI01의 240 Measurement를 Replay, Feature Extraction, ML 평가에 사용 |
| Paderborn Fact Sheets / Measurement Logs | Bearing 상태와 측정 metadata | [Official download index](https://groups.uni-paderborn.de/kat/BearingDataCenter/) | Source Manifest에서 CC BY-NC 4.0으로 기록 | Dataset context와 평가용 ground-truth 문서; runtime diagnostic 검색과 분리 |
| Paderborn website pages | 시험설비, 운전조건, 자료 설명 | [Bearing DataCenter](https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter) | 웹사이트 이용조건이 명시적으로 확인되지 않음 | 원문은 Git에서 제외하고 official URL과 manifest만 공개 |
| Condition Monitoring of Bearing Damage in Electromechanical Drive Systems | Paderborn benchmark technical evidence | [Official PDF](https://mb.uni-paderborn.de/fileadmin-mb/kat/PDF/Veroeffentlichungen/20160703_PHME16_CM_bearing.pdf) | Manifest 기록: CC Attribution 3.0 United States | Knowledge ingestion source; 원문 재배포 여부는 원 출처 조건 적용 |
| SKF Vibration Diagnostic Guide | 진동 진단 근거 | [SKF support attachment](https://skftechnicalsupport.zendesk.com/hc/en-us/article_attachments/360042513054) | SKF copyright; 재배포 권한 확인되지 않음 | 원문은 Git 제외, local ingestion과 Source Manifest만 사용 |
| SKF Bearing Damage and Failure Analysis | 손상 원인·점검·정비 근거 | [SKF Media Hub](https://cdn.skfmediahub.skf.com/api/public/093168a92d25cc46/pdf_preview_medium/14219_3_EN_-_Bearing_failures_LOW_pdf_preview_medium.pdf) | SKF Group 2025, all rights reserved | 원문은 Git 제외, local ingestion과 Source Manifest만 사용 |
| KAMP 정밀가공 품질보증 AI 데이터셋 | CNC 공정 Feature와 제품 품질 Ground Truth | [Korea AI Manufacturing Platform (KAMP)](https://www.kamp-ai.kr/); 중소벤처기업부·스마트제조혁신추진단(㈜인터엑스), 등록일 2022-12-23 | 재배포 권한은 독립적으로 확인되지 않음; 원본 CSV는 Git 제외 | 독립된 KAMP CNC PoC에서 1,085 observations / 43 columns, PASS 986 / FAIL 99를 Adapter 호환성 검증에 사용; CNC ML 학습용으로 사용하지 않음 |
| KAMP 정밀가공 품질보증 AI 데이터셋 공식 Guidebook | CNC 데이터 설명과 RAG 근거 | [KAMP](https://www.kamp-ai.kr/); 해당 데이터셋의 공식 Guidebook | 제공된 PoC 문서에 출처표시 및 인용 자료 전달 안내가 기록됨; 상세 조건은 원본 이용 안내 참조. 원본 PDF 및 원문 파생 Chunk/Index는 Git 제외 | 독립된 `kamp_cnc_v1` Knowledge Pack의 유일한 RAG Knowledge Source; 49 chunks를 이용한 Evidence 검색과 Abstention 검증 |

Canonical inventory: `knowledge/bearing_v1/manifests/source_manifest.json`.

## Open-source Libraries and Frameworks

아래 버전은 현재 local environment 또는 lockfile에서 확인했습니다. 전체 transitive dependency는 각 package lock/metadata를 따릅니다.

| Name | Role | Version observed | License confirmed from local package metadata |
|---|---|---:|---|
| FastAPI | Backend API | 0.141.1 | MIT |
| scikit-learn | Random Forest, feature utilities | 1.9.1 | BSD-3-Clause |
| LangGraph | Stateful Agent Workflow / Checkpoint | 1.2.11 | MIT |
| Chroma | Vector DB | 1.5.9 | Apache-2.0 |
| Uvicorn | ASGI server | 0.53.0 | BSD-3-Clause |
| Pydantic | API/domain validation | 2.13.5 | MIT |
| NumPy | numerical arrays | 2.5.3 | package metadata의 복합 license expression 참조 |
| SciPy | signal/statistical functions | 1.18.1 | bundled upstream license 참조 |
| Pillow | image decoding and quality observation | 12.3.0 | MIT-CMU |
| pypdf | PDF parsing | 6.19.0 | BSD-3-Clause |
| Next.js | Frontend framework | 16.3.5 | MIT |
| React / React DOM | UI | package range 19.x | MIT |
| TypeScript | type checking | 5.9.3 | Apache-2.0 |
| SQLite | Runtime persistence | system/runtime component | public domain; 배포 환경의 SQLite build 확인 필요 |

## Models and External APIs

| Name | Role | Source / Terms | Project Usage |
|---|---|---|---|
| `bearing_rf_binary_v1` | 정상·손상 이진 분류 | 본 프로젝트에서 Paderborn 대표 subset으로 학습한 artifact | 36개 Feature 기반 inference; 현장 일반화 성능으로 주장하지 않음 |
| `sklearn-hashing-vectorizer-v1` | deterministic local embedding | 본 프로젝트 구성 + scikit-learn | 384차원 local vector; 외부 embedding API 미사용 |
| `pillow-quality-observer-v1` | 이미지 품질 관찰 | 본 프로젝트 adapter + Pillow | 해상도·밝기·대비·사용 가능성만 관찰; 고장 분류 아님 |
| External runtime API | 해당 없음 | `OPENAI_API_KEY`는 optional configuration slot이며 핵심 검증 경로에서 사용하지 않음 | Runtime 진단은 외부 LLM 호출 없이 동작 |

## AI Development Tools

| Name | Role | Project Usage |
|---|---|---|
| OpenAI Codex | 개발 보조 도구 | 코드 작성·검토, 테스트 실행, 문서 정리 보조. 결과는 저장소 소스와 자동화 테스트로 검증 |
| Chat-based AI workshop prompts | 교육 자료 | `docs/RAG_MVP_PROMPTS.md` 등에서 학습자가 RAG 구축 과정을 따라가는 보조 자료. Runtime 서비스 의존성 아님 |

AI 개발도구의 출력 자체를 평가 근거로 사용하지 않습니다. 현재 Source Code, Artifact, Runtime, 자동화 테스트를 사실 기준으로 삼습니다.

## Existing Assets

- Dataset와 기술문서 원문
- 오픈소스 언어, 프레임워크, 라이브러리, 데이터베이스
- 공식 문서의 기술 지식과 metadata

## Newly Developed Components

- Paderborn Measurement Adapter와 Replay
- Feature Pipeline과 모델 registry/inference integration
- Source Manifest, Chunking, local embedding, Chroma retrieval, Evidence mapping
- LangGraph node/edge/conditional routing과 bounded retry
- Diagnosis, Evidence Verification, Inspection Plan, Recommended Action, Final Report
- HITL policy, Human Request, Checkpoint Resume
- Equipment-scoped Memory, Run History, AgentEvent SSE
- Agent Office와 History, Knowledge, Model, System 화면
- 선택형 Multimodal observation과 공개 API metadata sanitization
- KAMP CNC PoC: KAMPCNCAdapter, Ground Truth 계약, 독립 Guidebook RAG, Evidence/Abstention 처리, 데이터 감사 및 Adapter/RAG 테스트

## KAMP 출처 및 사용 범위

KAMP 관련 내용 추가일: 2026-10-05. 위 확인일과 기존 라이브러리 버전·라이선스 기록은 원문을 유지했습니다. 아래 내용은 제공된 KAMP PoC 문서를 기준으로 정리했으며, 이번 문서 편집에서 원본 이용조건이나 검증을 다시 확인한 것은 아닙니다.

### 필수 KAMP 출처표시

> 중소벤처기업부, Korea AI Manufacturing Platform(KAMP), 정밀가공 품질보증 AI 데이터셋, 스마트제조혁신추진단(㈜인터엑스), 2022.12.23.
> <https://www.kamp-ai.kr/>

- 데이터셋 제공기관: 스마트제조혁신추진단
- 수행기관: ㈜인터엑스
- 등록일: 2022-12-23
- 제공된 PoC 문서에 따르면 Guidebook 이용 안내는 연구·공식 활용 시 KAMP 출처표시와 인용 내용·문서의 `kamp@kaist.ac.kr` 전달을 요구합니다. 실제 이용 시 원본 Guidebook의 안내를 확인해야 하며, 이 문서 작업에서 자료를 전송하지 않았습니다.

### 독립 PoC의 사용 범위와 검증 결과

- 기존 Paderborn Production E2E와 독립된 Data Adapter 및 Knowledge/RAG 확장 검증입니다. Production 코드 수정, DB 쓰기, Chroma 쓰기는 각각 0입니다.
- Dataset: 1,085 observations / 43 columns; Ground Truth: PASS 986 / FAIL 99.
- Adapter 변환: 1,085 / 1,085; Feature mismatch: 0; Validation failure: 0.
- Adapter + RAG tests: 29 / 29 passed; `kamp_cnc_v1`: 49 chunks; FAIL Observation retrieval: 3 / 3; Abstention checks: 3 / 3.
- `KAMPCNCAdapter`는 40개 Process Feature를 유지하고 원본 Row별 Observation을 생성합니다. `passorfail`은 데이터셋 Ground Truth이며 `0=PASS`, `1=FAIL`입니다. ML Prediction과 별도로 표현합니다.
- 동일 `SerialNo`와 동일 `ReceivedDateTime`의 99쌍은 각각 PASS 1개와 FAIL 1개로 구성되며, 모든 쌍의 Feature vector가 서로 다릅니다. 원본 Row를 병합·중복 제거·선택하거나 Label을 수정하지 않았습니다. 생성 원인과 물리적·통계적 독립성은 확인되지 않았습니다.
- CNC ML 학습, Accuracy/F1 평가 및 현장 일반화 검증은 수행하지 않았습니다. PASS는 제품 품질의 양품 판정이며 설비 정상·무고장을 의미하지 않습니다. FAIL 또는 Sensor Feature만으로 특정 고장 원인을 확정하지 않습니다.
- RAG는 해당 데이터셋의 공식 Guidebook만 사용합니다. 독립된 signed SHA-256 hashing vector와 cosine similarity를 사용하며, 외부 embedding/LLM API 및 Production `bearing_v1`·Chroma를 사용하지 않습니다. 검색 점수는 텍스트 유사도이며 정확도·신뢰도·고장 확률이 아닙니다.
- 근거 충족 시 `EVIDENCE_FOUND`, 근거 부족 시 `INSUFFICIENT_EVIDENCE`, 무관한 요청이나 자동제어·정비 명령 요청에는 `OUT_OF_SCOPE`를 반환합니다.

### KAMP 자산의 저장소 배포 정책

- 원본 CSV와 다운로드한 Guidebook PDF는 재배포 권한이 독립적으로 확인되지 않아 Git에서 제외합니다. 제공된 PoC 문서에 따르면 PDF에는 문서별 식별자와 다운로드 사용자 정보도 포함되어 있습니다.
- 상당량의 Guidebook 원문 또는 실제 원본 Row 예시를 포함하는 파일도 Git에서 제외합니다: `poc/kamp_cnc/knowledge/kamp_cnc_v1/chunks.json`, `poc/kamp_cnc/knowledge/kamp_cnc_v1/index.json`, `poc/kamp_cnc/results/adapter_examples.json`, `poc/kamp_cnc/results/rag_retrieval_examples.json`. 원문 파생 Index도 검토 대상이므로 제외합니다.
- 공개 대상은 구현 코드, 계약 정의, 테스트, 재현 스크립트, 집계된 감사·검증 보고서, 원문을 포함하지 않는 metadata-only manifest 및 README입니다. 허가된 원본을 이용한 로컬 실행으로 제외된 Knowledge Pack 파일을 재생성합니다.
- `knowledge/bearing_v1/manifests/source_manifest.json`은 기존 베어링 자료의 inventory입니다. KAMP 상세 사용 범위는 [KAMP CNC PoC README](../../poc/kamp_cnc/README.md)를 참조합니다. KAMP 원본 파일의 체크섬과 별도 manifest 경로는 제공된 자료에서 확인되지 않아 임의로 기록하지 않았습니다.

## Repository Distribution Policy

- KAMP 원본 CSV/PDF, 원문 파생 Chunk/Index 및 원본 Row 예시는 Git에서 제외하며, 세부 범위는 위 KAMP 자산의 저장소 배포 정책을 따릅니다.
- 원본 Paderborn RAR/MAT와 재배포 권한이 확인되지 않은 웹/PDF Knowledge source, Chroma index, Runtime DB, upload, log는 Git에서 제외합니다. 저장소에 포함하는 소형 Paderborn 문서는 Source Manifest의 비상업·저작자표시 조건을 따릅니다.
- 모델 및 bounded evaluation artifact는 출처와 제한사항을 함께 제공합니다.
- 프로젝트 전체에 적용할 별도 license는 아직 선언되어 있지 않습니다. 외부 자산은 각 원 권리자의 조건을 유지합니다.
