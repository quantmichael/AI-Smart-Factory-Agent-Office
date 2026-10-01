# STEP 11 Agent Office UI Report

## Scope

The STEP 11 implementation connects the Next.js command-center UI to the real
Agent Run REST/SSE contract. Backend run state remains authoritative; no timer,
animation, sample label, or browser-side script advances the workflow.

## UI

- Route: `/`
- Language: Korean-first bilingual presentation. Operator-facing headings,
  statuses, graph nodes, event labels, tabs, and HITL controls are Korean, while
  established technical terms and backend identifiers remain visible in English
  where they improve traceability during demonstrations.
- Layout: desktop-first command center with equipment/signal context, a central
  five-zone Agent Office and LangGraph view, live run telemetry/timeline, and
  Evidence, Diagnosis, Inspection, Action, and Report tabs.
- Sensor rendering: the browser receives a bounded, downsampled vibration
  preview rather than a raw measurement array.
- Demo selector: one validated healthy measurement and one validated damaged
  measurement. Display labels are never submitted as model inputs.

## Agent Office

- Zones: Sensor / Machine, Detection Lab, RAG Knowledge Library, Diagnosis Desk,
  and Maintenance Desk.
- Roles: `SENSOR_AGENT`, `DETECTION_AGENT`, `RAG_AGENT`, `DIAGNOSIS_AGENT`, and
  `MAINTENANCE_AGENT`.
- States: `IDLE`, `WORKING`, `WAITING`, `RETRYING`, `NEEDS_HUMAN`, `DONE`, and
  `ERROR`, derived only from persisted `AgentEvent` values.
- Visual activity text and CSS animation reflect current nodes and events; they
  do not control workflow progression.

## SSE and Recovery

- EventSource connects to the real run stream with `after_sequence`.
- Disconnect handling re-reads run state and persisted events before reconnect.
- Events are sorted by `sequence` and deduplicated by `event_id` or `sequence`.
- The active run ID is persisted in local storage. Refresh reconstructs state
  from `GET /runs/{run_id}` and `GET /runs/{run_id}/events`.
- Timeline rendering is bounded to the latest 500 events.

## LangGraph View

- Displays the ten STEP 11 nodes and the required live node states.
- Normal and abnormal conditional edges are highlighted from detection events.
- `generate_normal_report` is represented by the shared UI node
  `generate_report`.
- Normal-route RAG/diagnosis nodes are shown as skipped.

## Evidence and Diagnosis

- Evidence cards retain purpose, title, publisher, source tier, page/section,
  snippet, retrieval score, and source URL when supplied by the backend.
- Retrieval score is labelled as a ranking score, not confidence.
- Diagnosis candidates keep ML confidence separate from agent confidence and
  link supporting/contradicting evidence by evidence ID.
- Inspection steps and recommended actions retain their evidence relationships.

## HITL

- A persisted `human_input_required` event opens an actual modal and keeps the
  run visibly `WAITING`.
- Approval decisions and additional-information fields call the canonical
  `POST /api/v1/agent/runs/{run_id}/human-input` endpoint.
- `SHUTDOWN_CHECK` is explicitly presented as an operator review request, never
  as automatic equipment control.
- Successful input resumes the same checkpointed run and the UI continues from
  real `human_input_received` and `workflow_resumed` events.

## Real E2E Verification

- Normal: `run_2abdea8f43164fb9ba91268fb7252954`, completed with 16 persisted
  events; normal edge selected and RAG/diagnosis skipped.
- Abnormal: `run_eb5cb99e47224a40b8b152958621f72e`, completed with 32 persisted
  events; real retrieval, diagnosis, planning, action, and report rendered.
- HITL: `run_d969248c2ebd4dbcb4c06599a1b9775e`, paused at event 31, accepted an
  operator approval, emitted resume events, and completed with 41 events.
- Refresh: a completed abnormal run was reloaded and rebuilt from all 32
  persisted events.
- Responsive: verified at 1440 px desktop and 1100 px laptop widths without
  horizontal page overflow.
- Retry: `PARTIAL` evidence and `RETRYING` transitions are covered by the UI
  reducer test. The current validated real samples did not naturally produce a
  partial-evidence retry during this STEP, so no synthetic live event was used.

## Screenshots

- `normal.png`
- `abnormal_detection.png`
- `rag_retrieval.png`
- `diagnosis.png`
- `hitl.png`
- `final_report.png`

All files are real browser captures from backend-driven runs. The HITL capture
uses the test-only controlled planner in `backend/tools/hitl_demo_app.py` to
exercise the existing real checkpoint/API path with a review-required action;
it does not create browser-side progress or execute equipment control.

## Verification

- Backend: `117 passed`.
- Frontend reducer: `6 passed`.
- TypeScript: `tsc --noEmit` passed.
- Production build: Next.js build passed; `/` is statically prerendered.
- Python compile check: passed.
- Health: HTTP 200 with `status=ok`.
- Browser console: no error or warning during the final E2E inspection.

## Known Issues

- FFT/frequency spectrum remains P1 and was not implemented.
- A real partial-evidence retry screenshot is unavailable because the validated
  measurements did not naturally enter that route. The visual state is tested
  without fabricating an SSE event.
- React development Strict Mode can duplicate idempotent detail GET requests;
  event state remains deduplicated and production behavior is unaffected.
- Automatic recovery of an in-process backend worker after a backend process
  restart remains the STEP 10 limitation; persisted terminal/waiting runs and
  UI refresh recovery work.

## STEP 12 Ready

YES
