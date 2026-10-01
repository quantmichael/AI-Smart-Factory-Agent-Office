# STEP 02A Dataset Validation

Validated on 2026-09-18 (Asia/Seoul).

## Acquired representative archives

| Bearing state | Category | Archive | Extracted MAT files | Fact sheet | Measurement log |
|---|---|---:|---:|---:|---:|
| K001 | Healthy | K001.rar | 80 | 1 | 1 |
| KA01 | Artificial outer-ring damage | KA01.rar | 80 | 1 | 1 |
| KI01 | Artificial inner-ring damage | KI01.rar | 80 | 1 | 1 |

All three official RAR archives opened and extracted without an archive error.
The extracted set contains 240 non-empty MATLAB v5 files covering the four
official operating-condition codes, 20 measurements per condition and bearing
state. Representative MAT files were identified as little-endian MATLAB v5
files and were approximately 8.7 MB each.

All six embedded PDFs opened with Poppler and produced non-empty extracted
text. The source archives and their SHA-256 values are listed in
`checksums.sha256`.

## Acquisition status

The official index contains 32 bearing-state archives. Three representative
archives are local and 29 remain downloadable. The source package is therefore
marked `partial`, not complete. Run the resumable official-source command below
to acquire the remainder:

```bash
python3 scripts/download_project_sources.py --dataset all --skip-documents --extract
```

No third-party mirror was used.
