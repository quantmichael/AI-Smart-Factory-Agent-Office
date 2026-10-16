# KAMP CNC Guidebook RAG 근거 보고서 — K2-1

## Knowledge Pack 개요

- Pack: `kamp_cnc_v1`
- 권한이 있는 원본 문서: 1
- Source: KAMP `정밀가공 품질보증 AI 데이터셋 분석실습 가이드북`
- 원본 PDF 페이지 수: 58
- Indexing 대상 분석 페이지: 31페이지, PDF 5-17 및 23-40페이지
- 제외: 표지/목차, 환경 설정 18-22페이지, 설치/부록 41-58페이지
- Chunk: 49
- Chunk metadata: source ID, document title, provider, page, section, chunk ID, text

원본 PDF는 수정하지 않았습니다. Pack은 `poc/kamp_cnc/knowledge/kamp_cnc_v1` 아래에만 저장되며 Production `bearing_v1` 또는 Chroma storage를 읽거나 기록하지 않습니다.

## 검색

- 방식: 결정론적 signed SHA-256 hashing vector, 512 dimensions, cosine similarity
- 외부 embedding: 없음
- 외부 LLM API: 없음
- 검색 threshold: `0.15845555`
- Score 의미: 텍스트 유사도만 의미하며 accuracy, confidence 또는 고장 확률이 아님

원하는 결과 label에 맞춰 threshold를 조정하지 않았습니다. 지원되는 Guidebook topic 네 가지와 관련 없는 control 세 가지를 검색 전에 code에 선언했습니다. 지원 topic의 최저 top score는 `0.19662980`, 관련 없는 control의 최고 top score는 `0.12028131`이며 고정 threshold는 두 값의 중간값입니다. Control이 분리되지 않았다면 threshold를 강제로 설정하지 않고 pack 생성이 실패하도록 했습니다.

## FAIL Observation 수직 단면 검증

실제 CSV의 FAIL row 세 개를 `KAMPCNCAdapter`로 변환하고 검색 전에 확인했습니다.

- Ground Truth status: FAIL
- Ground Truth source: `dataset_ground_truth`
- Prediction: `false`
- Query mode: `FAIL_EVIDENCE_CONTEXT`
- Cause inference allowed: `false`

세 query 모두 `EVIDENCE_FOUND`를 반환했습니다. 반환된 각 excerpt가 기록된 PDF page에서 추출한 정규화 text에 포함되는지 결정론적으로 확인했습니다.

Observation Feature 값은 `feature_context`에 보존됩니다. Query Builder는 관련 Feature family를 검색 context로 사용하지만 값을 마모, 고장 또는 유지보수 진단으로 변환하지 않습니다.

## 근거 검증

### A. 공구 마모 및 부하 증가

- Status: `EVIDENCE_FOUND`
- Page: PDF 6페이지
- Section: `1.1 분석 배경 - 공정 개요 및 이슈사항`
- Guidebook 근거: 가공이 진행되면서 공구가 마모되고 공구가 받는 부하가 증가합니다.

### B. 마모된 공구 및 가공 불량

- Status: `EVIDENCE_FOUND`
- Page: PDF 6페이지
- Section: `1.1 분석 배경 - 공정 개요 및 이슈사항`
- Guidebook 근거: 마모된 공구를 사용하면 가공 안정성이 낮아지고 가공 불량이 발생할 수 있습니다.

### C. 공정 데이터 및 품질 상태

- Status: `EVIDENCE_FOUND`
- Pages: topic query에서는 PDF 12페이지 및 40페이지, 원본 정의는 7페이지에도 존재
- Guidebook 근거: Spindle Speed, Spindle Load, Servo Load는 제품 가공 상태 및 품질/label 분석과 관련하여 사용하는 공정 변수입니다. 이 보고서는 correlation을 causality로 취급하지 않습니다.

### D. 점검 및 조치

- Status: `EVIDENCE_FOUND`
- Page: PDF 7페이지
- Section: `1.1 분석 배경 - 문제해결 및 분석 목표`
- Guidebook 근거: 작업자는 model 판단을 바탕으로 가공 설정과 가공 공구의 상태를 점검하고 불량품에 조치할 수 있습니다.

RAG 결과는 이를 Guidebook 근거로 제시합니다. 장비 제어 또는 유지보수 명령을 내리지 않으며 선택한 Observation이 공구 마모를 입증한다고 주장하지 않습니다.

## PASS 대조군

실제 unpaired PASS row 한 개를 테스트했습니다.

- Query mode: `PASS_CONTROL_CONTEXT`
- 검색 결과: `EVIDENCE_FOUND`
- 생성한 원인 후보: 아니요
- “장비 정상” 또는 “고장 없음”으로 확대: 아니요

PASS는 제공된 데이터셋에서 제품 품질이 PASS라는 의미이며 장비 상태 진단이 아닙니다.

## 답변 보류

| 요청 | 결과 | 이유 |
|---|---|---|
| 관련 없는 날씨/여행 query | `OUT_OF_SCOPE` | KAMP CNC Guidebook 범위 밖 |
| Sensor 값으로 특정 고장 확정 | `INSUFFICIENT_EVIDENCE` | Feature와 Guidebook만으로 특정 고장 원인을 확정할 수 없음 |
| 장비 정지 또는 공구 자동 교체 | `OUT_OF_SCOPE` | 이 PoC는 제어 또는 유지보수 명령을 내리지 않음 |

## 테스트

- 전체 PoC 테스트: 29
- 통과: 29
- 실패: 0
- RAG 전용 테스트: 14
- 기존 Adapter 테스트: 15
- Production 테스트 변경 또는 실행: 아니요

테스트는 ingestion, 필수 Chunk metadata, 결정론적 검색, 실제 FAIL Observation query build, provenance, page/section 보존, PASS control 동작, 지원하지 않는 query에 대한 답변 보류, 특정 고장 확정 요청에 대한 답변 보류, 자동 제어 요청에 대한 답변 보류, page text 검증, Ground Truth 의미, Production 격리, threshold 분리를 다룹니다.

## 판정

- **K2-1: PASS**
- **외부 기술 Knowledge 확장: 별도 단계로 GO**

Vertical slice는 격리되고 원본을 보존하는 검색을 입증합니다. 외부 KORLOY 또는 기타 공식 기술 자료는 문서별 provenance, source별 claim, conflict handling, 변경하지 않은 답변 보류 규칙을 갖춘 새로운 versioned Knowledge Pack으로만 추가해야 합니다. K2-1에는 외부 문서를 추가하지 않았습니다.
