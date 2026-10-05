# KAMP CNC Expansion PoC

## Purpose

This Proof of Concept verifies domain expansion of the Data Adapter and Knowledge/RAG layers using KAMP CNC manufacturing data and its official Guidebook. It is fully isolated from the existing Paderborn Production E2E application.

This PoC does not change, import into, or write to the Production Backend, Frontend, database, Checkpoint, Memory, Artifact, ML model, `bearing_v1`, Chroma, or deployment configuration.

## Verified results

| Check | Result |
|---|---:|
| Dataset | 1,085 rows / 43 columns |
| PASS | 986 |
| FAIL | 99 |
| Adapter conversion | 1,085 / 1,085 |
| Feature mismatch | 0 |
| Validation failure | 0 |
| Adapter + RAG tests | 29 / 29 passed |
| Knowledge Pack | `kamp_cnc_v1` |
| Knowledge chunks | 49 |
| FAIL Observation retrieval | 3 / 3 |
| Abstention checks | 3 / 3 |
| Production modifications | 0 |
| Production DB writes | 0 |
| Production Chroma writes | 0 |

## Flow

```text
KAMP CNC Data
    -> KAMPCNCAdapter
    -> Ground Truth Context
    -> kamp_cnc_v1 RAG
    -> Evidence / Abstention
```

## Ground truth and claim boundaries

- `passorfail` is KAMP Dataset Ground Truth.
- `passorfail=0` means PASS / 양품.
- `passorfail=1` means FAIL / 불량.
- Label mapping: `0 = PASS`, `1 = FAIL`.
- The CNC status in this PoC is not an ML prediction.
- CNC ML training and accuracy/F1 evaluation were not performed.
- This PoC does not claim field generalization performance.
- Sensor Features alone do not establish a specific fault cause.
- The only RAG Knowledge Source is the official KAMP Guidebook for this dataset.
- This is a PoC fully independent of the Production E2E workflow.
- Retrieval scores represent text similarity, not accuracy, confidence, or failure probability.

## Paired observations

The source contains multiple observations with the same `SerialNo`. The paired rows have different Feature vectors. The Adapter preserves every original row as an individual Observation and records pair-related data-quality metadata.

Rows are not merged, deduplicated, selected, or relabeled. The official material does not explain why these observations share an identifier and timestamp, so this PoC does not infer their origin or statistical independence.

## Adapter

`KAMPCNCAdapter` maps all 40 Process Features without feature selection or constant-column removal. It creates deterministic row-level sample IDs and fails closed on invalid labels, missing metadata or Features, nonnumeric Feature values, and unparseable timestamps.

Ground truth is represented separately from prediction:

```json
{
  "raw_label": 0,
  "status": "PASS",
  "source_type": "dataset_ground_truth",
  "prediction": false
}
```

## Guidebook RAG

The independent `kamp_cnc_v1` Knowledge Pack uses page- and section-aware Guidebook chunks with deterministic signed SHA-256 hashing vectors and cosine similarity. It does not call an external embedding or LLM API and does not use Production `bearing_v1` or Chroma.

The retriever returns:

- `EVIDENCE_FOUND` when Guidebook evidence meets the calibrated threshold.
- `INSUFFICIENT_EVIDENCE` when the Guidebook cannot support the requested claim.
- `OUT_OF_SCOPE` for unrelated, automatic-control, or maintenance-command requests.

A PASS Observation means product-quality PASS only. It is not expanded into “normal equipment” or “no fault.” A FAIL Observation supplies retrieval context but does not prove tool wear or another specific cause.

## KAMP attribution

국문 출처:

> 중소벤처기업부, Korea AI Manufacturing Platform(KAMP), 정밀가공 품질보증 AI 데이터셋, 스마트제조혁신추진단(㈜인터엑스), 2022.12.23.

- Official KAMP: https://www.kamp-ai.kr/
- Dataset provider: 스마트제조혁신추진단
- Performing organization: ㈜인터엑스
- Registration date: 2022-12-23

The Guidebook use notice requires KAMP attribution for research or official use and asks users to send cited content/documents to `kamp@kaist.ac.kr`.

## Publication safety

The raw CSV and downloaded Guidebook PDF are intentionally excluded from Git because redistribution permission has not been independently confirmed. The downloaded PDF also contains a document-specific identifier and downloader information.

Generated files containing substantial Guidebook text or actual source-row examples are also excluded:

- `knowledge/kamp_cnc_v1/chunks.json`
- `knowledge/kamp_cnc_v1/index.json`, pending review as a source-derived index
- `results/adapter_examples.json`
- `results/rag_retrieval_examples.json`

The public candidate includes implementation code, contracts, tests, reproducible build scripts, aggregate audits/reports, the metadata-only manifest, and this README. Running the build locally with authorized source files regenerates the excluded Knowledge Pack files.

## Reproduce locally

The RAG ingestion step requires `pypdf`. No external API credentials are required.

```bash
python3 -m unittest discover -s poc/kamp_cnc/tests -v
python3 -m poc.kamp_cnc.scripts.run_adapter_compatibility --output summary
python3 -m poc.kamp_cnc.scripts.build_rag_poc --output ingestion
```

## Not verified

- CNC ML performance or generalization
- Physical independence or origin of paired observations
- Product-level label resolution
- External technical Knowledge Sources or cross-document retrieval
- Generative answer synthesis with an LLM
- Production integration
