# LangGraph Core Report

- Graph: actual LangGraph `StateGraph`
- Checkpoint: SQLite (`SqliteSaver`, strict serializer allowlist)
- Max workflow retrieval retries: 2
- Reasoning provider: `deterministic-evidence-grounded-v1`

## Normal E2E

- Measurement: `paderborn:K001:N09_M07_F10:01`
- ML status: `normal`
- RAG called: `False`
- Result: `COMPLETED/MONITOR`
- Events: 13

## Abnormal E2E

- Measurement: `paderborn:KA01:N09_M07_F10:01`
- ML status: `abnormal`
- Queries: 2
- Evidence: 9
- Candidates: 1
- Evidence status: `SUFFICIENT`
- Result: `COMPLETED/READY_FOR_INSPECTION`
- Events: 19

## Safety boundaries

- No raw signal arrays are stored in AgentState.
- Diagnostic queries exclude bearing-specific ground-truth documents.
- The local reasoner does not assert a specific physical root cause.
- No inspection plan, maintenance approval, equipment control, HITL, or SSE is implemented.
- Artifacts omit retrieved source content, prompts, secrets, and private reasoning.
