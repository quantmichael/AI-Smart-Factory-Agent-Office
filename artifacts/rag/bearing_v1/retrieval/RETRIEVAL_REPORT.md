# bearing_v1 Retrieval Report

- Knowledge pack: `bearing_v1`
- Retriever: vector similarity with metadata filtering
- Embedding: `local/sklearn-hashing-vectorizer-v1`
- Collection: `bearing_v1`
- Evaluation cases: 24
- Hit@3: 0.9130
- Hit@5: 0.9130
- Recall@3: 0.9130
- Recall@5: 0.9130
- MRR: 0.8623
- Empty result rate: 0.0000

## Metadata filters

All searches enforce `knowledge_pack_id=bearing_v1`, `component=bearing`, 
source tier 1-2, and purpose-specific source allowlists. Bearing-specific 
ground-truth sources are available only in EVALUATION mode.

## Failure cases

- `dataset_signals`: expected `PADERBORN_DATASETS_AND_DOWNLOAD`; top-5 returned `PADERBORN_TEST_RIG, PADERBORN_BENCHMARK_PAPER`.
- `paderborn_damage_taxonomy`: expected `PADERBORN_DAMAGE`; top-5 returned `PADERBORN_BENCHMARK_PAPER, SKF_BEARING_DAMAGE_FAILURE_ANALYSIS`.

The vector-only baseline also returned low-score candidates for the unanswerable 
PLC-control case. Scores and the non-empty result are preserved for a later 
evidence-sufficiency threshold; no candidate is promoted to an answer here.

## Query examples

- `DATASET_EVIDENCE`: Paderborn bearing test rig rotational speed load torque radial force operating conditions
- `DIAGNOSTIC_EVIDENCE`: vibration spectrum imbalance dominant running speed 1x
- `INSPECTION_ACTION`: bearing inspection during operation noise vibration temperature lubricant

## Recommended improvements

- Review failed queries, parsing, chunking, and filter scope before changing embeddings.
- Consider a relevance threshold for unanswerable questions in a later verification step.
- Evaluate keyword/hybrid retrieval for exact bearing IDs and fault terminology after this baseline.

Retrieval scores are ranking signals, not probabilities that evidence is true.
