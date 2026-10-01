# STEP 10 Agent API & SSE Report

- Generated: `2026-09-18T09:04:25.598796+00:00`
- Execution: real local Paderborn measurements through FastAPI, LangGraph, ML, RAG, and SSE
- Reconnect contract: `after_sequence` query parameter
- WAITING policy: deliver persisted events, then close; reconnect after human input
- Heartbeat: SSE comment, not persisted

## Event → UI State Mapping

| Event | UI state update |
|---|---|
| `node_started` | Mark the mapped `agent_role` as working |
| `detection_normal` / `detection_abnormal` | Update analysis summary and detection state |
| `retrieval_completed` | Update RAG evidence count |
| `evidence_status_changed` | Update evidence status and retry count |
| `human_input_required` | Set workflow to WAITING and show the pending request |
| `human_input_received` / `workflow_resumed` | Clear the modal and resume the same run |
| `report_generated` | Mark the report as available |
| `workflow_completed` | Mark all applicable work complete |
| `workflow_error` | Show the persisted workflow error state |

## Verified Runs

| Scenario | Run ID | Events | Status | Evidence | Report |
|---|---|---:|---|---:|---|
| Normal | `run_92be75bdf57b4776965c121d19f5019c` | 16 | COMPLETED | 0 | ready |
| Abnormal | `run_e9653a741cdc4c1eb0da2eb2302fa7c7` | 32 | COMPLETED | 9 | ready |
| HITL | `run_be15bafeaa9743cea050e00049ac6768` | 41 | COMPLETED | 9 | ready |

No timer-generated or replayed progress is used. The event files are parsed from the actual SSE responses.
