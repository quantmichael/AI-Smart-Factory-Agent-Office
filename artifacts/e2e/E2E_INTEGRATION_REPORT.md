# STEP 14 E2E Integration Report — MVP-RC1

- Generated: 2026-09-18T22:40:02.760254+00:00
- Readiness: `ready`
- Normal: `run_3f6eb5b5c4714823aa61f29159399267` / `COMPLETED`
- Abnormal + Multimodal: `run_15db7993a01b45deafe48d2a25cee614` / `COMPLETED`
- Controlled RAG Retry: `run_retry_a006a8dc882d4cfa` / `COMPLETED`
- Controlled HITL: `run_hitl_fddd2e5da9674620` / `COMPLETED`
- Memory on second run: `True`
- Refresh/reconnect/restart: `True`
- Citation trace: `True`
- Ground-truth leakage audit: `True`
- P0 bugs: `0`

Retry and HITL routing decisions are explicitly controlled test conditions. They
still use the actual Paderborn measurement, active ML artifact, and bearing_v1
vector database. The inspection image is simulated and is not synchronized with
the Paderborn vibration measurement.
