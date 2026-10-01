# Bearing Knowledge Pack v1

This package contains a small, official-source-first document set for grounding
bearing and vibration diagnosis. STEP 06 validates the manifest, parses and
chunks these documents, embeds them locally, and persists the resulting index.
Retrieval and ranking remain a later step.

## Documents and tiers

- Tier 1, Paderborn University: DataCenter overview, dataset/download page,
  damage taxonomy, test rig, operating conditions, publication list, benchmark
  paper, and dataset archive documentation
- Tier 2, SKF: Vibration Diagnostic Guide and Bearing Damage and Failure Analysis

## RAG roles

The source records identify one or more of: `dataset_context`, `ground_truth`,
`damage_taxonomy`, `vibration_diagnosis`, `failure_analysis`, `inspection`, and
`maintenance`.

## Licensing and repository policy

The Paderborn dataset is CC BY-NC 4.0 and requires attribution. The benchmark
paper carries its own attribution license. The website pages and SKF
publications remain copyrighted unless their own terms say otherwise; public
download availability does not grant redistribution rights. Downloaded RAG
HTML and PDFs are therefore kept local and ignored by Git. Review all licenses
again before deployment, redistribution, or commercial use.

## Updating

Use `python scripts/download_project_sources.py` to fetch known official URLs,
skip valid local files, validate signatures, calculate SHA-256 values, and
refresh the manifests. Never substitute a third-party mirror automatically.

The canonical manifest is `manifests/source_manifest.json`; the companion
`manifests/SOURCE_MANIFEST.md` is a human-readable inventory.

## Ingestion

From the project root, validate and estimate the ingestion without changing the
vector database:

```bash
backend/.venv/bin/python scripts/ingest_knowledge_pack.py --pack bearing_v1 --dry-run
```

Create or incrementally update the local Chroma collection:

```bash
backend/.venv/bin/python scripts/ingest_knowledge_pack.py --pack bearing_v1
```

The default collection is `bearing_v1` under `artifacts/vector_db`. The local
embedding implementation is `sklearn-hashing-vectorizer-v1`; it is deterministic
and requires no network or model download. Generated reports are written to
`artifacts/rag/bearing_v1`.

STEP 07 retrieval evaluation is run with:

```bash
backend/.venv/bin/python scripts/evaluate_retrieval.py
```

Its reports are written under `artifacts/rag/bearing_v1/retrieval`. Diagnostic
mode excludes bearing-specific Fact Sheets and Measurement Logs from dataset
evidence; evaluation mode must be selected explicitly to search those sources.
