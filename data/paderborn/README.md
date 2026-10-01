# Paderborn Bearing DataCenter Dataset

## Source

- Publisher: Paderborn University, Chair of Design and Drive Technology (KAt)
- Official dataset page: <https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter/data-sets-and-download>
- Official download index: <https://groups.uni-paderborn.de/kat/BearingDataCenter/>
- Purpose: reference sensor measurements for bearing-condition analysis in this noncommercial educational project
- Download date: recorded per run in `metadata/dataset_files.json`

## License and citation

The official Bearing DataCenter page identifies the dataset as Creative Commons
Attribution-NonCommercial 4.0 International (CC BY-NC 4.0). Attribution to the
dataset owner and the benchmark publication is required. Commercial use needs a
separate license review and, where required, permission from the publisher.

Do not assume that this project configuration authorizes commercial use or
redistribution of the original archives.

## Directories

- `raw/`: unchanged official RAR archives and the official version note; ignored by Git
- `metadata/`: acquisition inventory and SHA-256 checksums
- `docs/`: reserved for dataset-specific extracted documentation when archive inspection is performed

The application reads the root from `PADERBORN_DATA_ROOT`. From the backend
directory, the default `../data/paderborn` resolves to this folder.

## Inspect and validate

From the project root:

```bash
backend/.venv/bin/python scripts/inspect_paderborn_dataset.py --root data/paderborn
```

The command writes bounded metadata-only artifacts to
`artifacts/data/paderborn_inspection.json` and
`artifacts/data/paderborn_validation.json`. It validates raw arrays but never
serializes them into the artifacts.

Adapter usage:

```python
from app.data.adapters.paderborn import PaderbornDatasetAdapter

adapter = PaderbornDatasetAdapter("../data/paderborn")
summary = adapter.list_measurements()[0]
measurement = adapter.load_measurement(summary.measurement_id)
```

`list_measurements()` is metadata-only. Raw arrays are loaded only by
`load_measurement()`.

## Profile the local subset

From the project root:

```bash
backend/.venv/bin/python scripts/profile_paderborn_dataset.py \
  --root data/paderborn \
  --output artifacts/profiling
```

The command validates the adapter first, profiles the local measurements, and
writes the STEP 03 report, tabular summaries, split plan, STEP 04 input
specification, and representative figures under `artifacts/profiling/`. It does
not train a model.

## Train the STEP 04 baseline

After profiling has produced the fixed input specification:

```bash
backend/.venv/bin/python scripts/train_ml_baseline.py \
  --root data/paderborn \
  --input-spec artifacts/profiling/step04_input_spec.json \
  --output artifacts/ml/baseline_v1
```

The command creates a measurement-group split, trains the fixed Random Forest,
evaluates window/measurement/bearing views, and writes the model and audit
artifacts. The current three-bearing subset cannot support unseen-bearing
evaluation because only `K001` is healthy.

Run `python3 scripts/download_project_sources.py --dataset all --extract` from
the project root to acquire, archive-test, and extract all sources. Partial
downloads use a `.part` suffix and are resumed when the server supports byte
ranges. Omit `--extract` when disk space is limited.
