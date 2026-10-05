# KAMP CNC Guidebook RAG Evidence Report — K2-1

## Knowledge pack

- Pack: `kamp_cnc_v1`
- Authorized source documents: 1
- Source: KAMP `정밀가공 품질보증 AI 데이터셋 분석실습 가이드북`
- Source PDF pages: 58
- Indexed analysis pages: 31 pages, PDF pages 5-17 and 23-40
- Excluded: cover/contents, environment setup pages 18-22, and installation/appendix pages 41-58
- Chunks: 49
- Chunk metadata: source ID, document title, provider, page, section, chunk ID, text

The source PDF was not modified. The pack is stored only under `poc/kamp_cnc/knowledge/kamp_cnc_v1` and does not read or write Production `bearing_v1` or Chroma storage.

## Retrieval

- Method: deterministic signed SHA-256 hashing vectors, 512 dimensions, cosine similarity
- External embeddings: none
- External LLM API: none
- Retrieval threshold: `0.15845555`
- Score meaning: text similarity only, not accuracy, confidence, or fault probability

The threshold was not adjusted against desired result labels. Four supported Guidebook topics and three unrelated controls were declared in code before retrieval. The lowest supported top score was `0.19662980`; the highest unrelated-control top score was `0.12028131`. The fixed threshold is their midpoint. The controls were separable; otherwise pack creation would fail rather than force a threshold.

## FAIL Observation vertical slice

Three actual CSV FAIL rows were transformed with `KAMPCNCAdapter` and checked before retrieval:

- Ground truth status: FAIL
- Ground truth source: `dataset_ground_truth`
- Prediction: `false`
- Query mode: `FAIL_EVIDENCE_CONTEXT`
- Cause inference allowed: `false`

All three queries returned `EVIDENCE_FOUND`. Each returned excerpt was deterministically checked against the normalized text extracted from its recorded PDF page.

The Observation Feature values are retained in `feature_context`; the Query Builder uses the relevant Feature families as search context but does not convert values into a wear, failure, or maintenance diagnosis.

## Evidence verification

### A. Tool wear and load increase

- Status: `EVIDENCE_FOUND`
- Page: PDF page 6
- Section: `1.1 분석 배경 - 공정 개요 및 이슈사항`
- Guidebook evidence: as machining progresses, tool wear occurs and the load received by the tool increases.

### B. Worn tool and machining defects

- Status: `EVIDENCE_FOUND`
- Page: PDF page 6
- Section: `1.1 분석 배경 - 공정 개요 및 이슈사항`
- Guidebook evidence: using a worn tool lowers machining stability and can cause machining defects.

### C. Process data and quality state

- Status: `EVIDENCE_FOUND`
- Pages: PDF pages 12 and 40 in the topic query; page 7 also contains the source definition
- Guidebook evidence: Spindle Speed, Spindle Load, and Servo Load are process variables used in relation to product machining state and quality/label analysis. The report does not treat correlation as causality.

### D. Inspection and action

- Status: `EVIDENCE_FOUND`
- Page: PDF page 7
- Section: `1.1 분석 배경 - 문제해결 및 분석 목표`
- Guidebook evidence: based on a model judgment, the worker can examine machining settings and the condition of the machining tool and take action on defective products.

The RAG result presents this as Guidebook evidence. It does not issue a machine-control or maintenance command and does not claim that the selected Observation proves tool wear.

## PASS control

One actual unpaired PASS row was tested.

- Query mode: `PASS_CONTROL_CONTEXT`
- Retrieval result: `EVIDENCE_FOUND`
- Cause candidates generated: no
- Expanded to “normal equipment” or “no fault”: no

PASS means product-quality PASS in the supplied dataset. It is not an equipment-health diagnosis.

## Abstention

| Request | Result | Reason |
|---|---|---|
| Unrelated weather/travel query | `OUT_OF_SCOPE` | Outside the KAMP CNC Guidebook scope |
| Confirm a specific fault from sensor values | `INSUFFICIENT_EVIDENCE` | Features and the Guidebook cannot confirm a specific fault cause |
| Stop equipment or automatically replace a tool | `OUT_OF_SCOPE` | This PoC does not issue control or maintenance commands |

## Tests

- Total PoC tests: 29
- Passed: 29
- Failed: 0
- RAG-specific tests: 14
- Existing Adapter tests: 15
- Production tests modified or executed: no

Tests cover ingestion, required Chunk metadata, deterministic retrieval, actual FAIL Observation Query building, provenance, page/section preservation, PASS control behavior, unsupported-query abstention, specific-fault abstention, automatic-control abstention, page-text verification, ground-truth semantics, Production isolation, and threshold separation.

## Verdict

- **K2-1: PASS**
- **External technical Knowledge expansion: GO as a separate phase**

The vertical slice demonstrates isolated, source-preserving retrieval. External KORLOY or other official technical material should be added only in a new versioned Knowledge Pack with per-document provenance, source-specific claims, conflict handling, and unchanged abstention rules. No external document was added in K2-1.

