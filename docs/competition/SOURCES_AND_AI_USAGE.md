# Sources and AI Usage

확인일: 2026-10-01

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

## Repository Distribution Policy

- 원본 Paderborn RAR/MAT와 재배포 권한이 확인되지 않은 웹/PDF Knowledge source, Chroma index, Runtime DB, upload, log는 Git에서 제외합니다. 저장소에 포함하는 소형 Paderborn 문서는 Source Manifest의 비상업·저작자표시 조건을 따릅니다.
- 모델 및 bounded evaluation artifact는 출처와 제한사항을 함께 제공합니다.
- 프로젝트 전체에 적용할 별도 license는 아직 선언되어 있지 않습니다. 외부 자산은 각 원 권리자의 조건을 유지합니다.
