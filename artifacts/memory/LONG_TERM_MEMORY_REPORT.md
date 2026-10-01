# Long-term Equipment Memory Validation

- Generated at: 2026-09-18T15:19:08.923082+00:00
- Equipment: `paderborn-bearing-test-rig`
- Run 1: `run_926e92947d494112b506eddb7725d156` using `paderborn:K001:N09_M07_F10:01`
- Run 1 stored memories: 3
- Run 2: `run_0f0df9ed116643b5a7670dcf504334db` using `paderborn:K001:N09_M07_F10:02`
- Run 2 retrieved memories: 2
- Equipment isolation: PASS
- Automatic maintenance creation: disabled
- Technical RAG storage: `artifacts/vector_db` / `bearing_v1`
- Equipment memory storage: isolated SQLite database

The current ML analysis still uses only the current measurement. Historical
records are passed as a separate `EQUIPMENT_HISTORY` diagnosis context and are
not represented as technical-document evidence.
