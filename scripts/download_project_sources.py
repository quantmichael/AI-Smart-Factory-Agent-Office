#!/usr/bin/env python3
"""Download and validate the official STEP 02A dataset and RAG sources.

Only URLs owned by Paderborn University or SKF are used. Large dataset
archives are resumable through a temporary ``.part`` file and are never
placed under version control.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
PADERBORN_DOWNLOAD_ROOT = "https://groups.uni-paderborn.de/kat/BearingDataCenter"
PADERBORN_ARCHIVES = (
    "K001.rar", "K002.rar", "K003.rar", "K004.rar", "K005.rar", "K006.rar",
    "KA01.rar", "KA03.rar", "KA04.rar", "KA05.rar", "KA06.rar", "KA07.rar",
    "KA08.rar", "KA09.rar", "KA15.rar", "KA16.rar", "KA22.rar", "KA30.rar",
    "KB23.rar", "KB24.rar", "KB27.rar", "KI01.rar", "KI03.rar", "KI04.rar",
    "KI05.rar", "KI07.rar", "KI08.rar", "KI14.rar", "KI16.rar", "KI17.rar",
    "KI18.rar", "KI21.rar",
)


@dataclass(frozen=True)
class Source:
    source_id: str
    title: str
    publisher: str
    url: str
    local_path: str
    source_type: str
    license_name: str
    license_status: str
    source_tier: str
    rag_role: tuple[str, ...]
    file_type: str
    notes: str = ""


DOCUMENT_SOURCES = (
    Source(
        "PADERBORN_OVERVIEW",
        "Bearing DataCenter overview",
        "Paderborn University, KAt",
        "https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter",
        "knowledge/bearing_v1/paderborn/bearing_datacenter_overview.html",
        "official_web_page",
        "Website terms not specified",
        "local-use-only-review-before-redistribution",
        "Tier 1",
        ("dataset_context",),
        "html",
    ),
    Source(
        "PADERBORN_DATASETS_AND_DOWNLOAD",
        "Data Sets and Download",
        "Paderborn University, KAt",
        "https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter/data-sets-and-download",
        "knowledge/bearing_v1/paderborn/data_sets_and_download.html",
        "official_web_page",
        "Website terms not specified",
        "local-use-only-review-before-redistribution",
        "Tier 1",
        ("dataset_context", "ground_truth"),
        "html",
    ),
    Source(
        "PADERBORN_DAMAGE",
        "Bearing Damage",
        "Paderborn University, KAt",
        "https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter/bearing-damage",
        "knowledge/bearing_v1/paderborn/bearing_damage.html",
        "official_web_page",
        "Website terms not specified",
        "local-use-only-review-before-redistribution",
        "Tier 1",
        ("damage_taxonomy", "ground_truth"),
        "html",
    ),
    Source(
        "PADERBORN_TEST_RIG",
        "Test Rig and Measurement Equipment",
        "Paderborn University, KAt",
        "https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter/test-rig-and-measurement-equipment",
        "knowledge/bearing_v1/paderborn/test_rig_and_measurement_equipment.html",
        "official_web_page",
        "Website terms not specified",
        "local-use-only-review-before-redistribution",
        "Tier 1",
        ("dataset_context",),
        "html",
    ),
    Source(
        "PADERBORN_OPERATING_CONDITIONS",
        "Operating Conditions",
        "Paderborn University, KAt",
        "https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter/operating-conditions",
        "knowledge/bearing_v1/paderborn/operating_conditions.html",
        "official_web_page",
        "Website terms not specified",
        "local-use-only-review-before-redistribution",
        "Tier 1",
        ("dataset_context", "ground_truth"),
        "html",
    ),
    Source(
        "PADERBORN_PUBLICATION",
        "Publication and References",
        "Paderborn University, KAt",
        "https://mb.uni-paderborn.de/en/kat/research/bearing-datacenter/publication-and-references",
        "knowledge/bearing_v1/paderborn/publication_and_references.html",
        "official_web_page",
        "Website terms not specified",
        "local-use-only-review-before-redistribution",
        "Tier 1",
        ("dataset_context",),
        "html",
    ),
    Source(
        "PADERBORN_BENCHMARK_PAPER",
        "Condition Monitoring of Bearing Damage in Electromechanical Drive Systems",
        "Paderborn University, KAt",
        "https://mb.uni-paderborn.de/fileadmin-mb/kat/PDF/Veroeffentlichungen/20160703_PHME16_CM_bearing.pdf",
        "knowledge/bearing_v1/paderborn/paderborn_bearing_benchmark_paper.pdf",
        "official_publication",
        "CC Attribution 3.0 United States",
        "attribution-required",
        "Tier 1",
        ("dataset_context", "ground_truth"),
        "pdf",
    ),
    Source(
        "SKF_VIBRATION_DIAGNOSTIC_GUIDE",
        "Vibration Diagnostic Guide (CM5003 EN)",
        "SKF",
        "https://skftechnicalsupport.zendesk.com/hc/en-us/article_attachments/360042513054",
        "knowledge/bearing_v1/vibration_diagnosis/skf_vibration_diagnostic_guide.pdf",
        "manufacturer_technical_guide",
        "SKF copyright; redistribution not granted",
        "local-use-only-review-before-redistribution",
        "Tier 2",
        ("vibration_diagnosis",),
        "pdf",
        "Official SKF Technical Support attachment. The CDN URL in STEP 02A returned HTTP 404 at acquisition time.",
    ),
    Source(
        "SKF_BEARING_DAMAGE_FAILURE_ANALYSIS",
        "Bearing Damage and Failure Analysis (PUB BU/I3 14219/3 EN)",
        "SKF",
        "https://cdn.skfmediahub.skf.com/api/public/093168a92d25cc46/pdf_preview_medium/14219_3_EN_-_Bearing_failures_LOW_pdf_preview_medium.pdf",
        "knowledge/bearing_v1/failure_analysis/skf_bearing_damage_failure_analysis.pdf",
        "manufacturer_technical_guide",
        "SKF Group 2025; all rights reserved",
        "local-use-only-review-before-redistribution",
        "Tier 2",
        ("failure_analysis", "inspection", "maintenance"),
        "pdf",
        "Current 2025 official SKF edition. The older CDN URL in STEP 02A returned HTTP 404 at acquisition time.",
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collection_sha256(paths: Iterable[Path]) -> str | None:
    files = sorted(path for path in paths if path.is_file())
    if not files:
        return None
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(ROOT)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def valid_file(path: Path, file_type: str) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    with path.open("rb") as stream:
        prefix = stream.read(16)
    if file_type == "pdf":
        return prefix.startswith(b"%PDF-")
    if file_type == "rar":
        return prefix.startswith(b"Rar!\x1a\x07")
    if file_type == "html":
        return b"<html" in prefix.lower() or b"<!doctype" in prefix.lower()
    return True


def download(url: str, target: Path, file_type: str) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    if valid_file(target, file_type):
        return "skipped-valid"

    partial = target.with_name(f"{target.name}.part")
    start = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": "AI-Smart-Factory-Agent-Office/0.1 source-acquisition"}
    if start:
        headers["Range"] = f"bytes={start}-"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        status = getattr(response, "status", 200)
        content_type = response.headers.get_content_type()
        if status not in (200, 206):
            raise RuntimeError(f"HTTP {status} for {url}")
        if file_type == "pdf" and content_type not in ("application/pdf", "application/octet-stream"):
            raise RuntimeError(f"unexpected PDF Content-Type {content_type} for {url}")
        mode = "ab" if status == 206 and start else "wb"
        with partial.open(mode) as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
    if not valid_file(partial, file_type):
        raise RuntimeError(f"downloaded file failed {file_type} signature validation: {url}")
    os.replace(partial, target)
    return "downloaded"


def dataset_targets(mode: str) -> Iterable[str]:
    if mode == "none":
        return ()
    if mode == "sample":
        return ("K001.rar", "KA01.rar", "KI01.rar")
    return PADERBORN_ARCHIVES


def extract_archives(names: Iterable[str]) -> None:
    bsdtar = shutil.which("bsdtar")
    if not bsdtar:
        raise RuntimeError("bsdtar is required for RAR integrity checks and extraction")
    raw = ROOT / "data/paderborn/raw"
    extracted = raw / "extracted"
    docs = ROOT / "data/paderborn/docs"
    extracted.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    for name in names:
        archive = raw / name
        if not valid_file(archive, "rar"):
            continue
        subprocess.run(
            [bsdtar, "-tf", str(archive)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        subprocess.run(
            [bsdtar, "-xf", str(archive), "-C", str(extracted)],
            check=True,
        )
        bearing_state = archive.stem
        source_dir = extracted / bearing_state
        target_dir = docs / bearing_state
        target_dir.mkdir(parents=True, exist_ok=True)
        for document in (
            source_dir / f"{bearing_state}.pdf",
            source_dir / f"measuring_log_{bearing_state}.pdf",
        ):
            if valid_file(document, "pdf"):
                shutil.copy2(document, target_dir / document.name)


def write_dataset_metadata(accessed_at: str) -> dict[str, object]:
    raw = ROOT / "data/paderborn/raw"
    records = []
    checksum_lines = []
    for name in (*PADERBORN_ARCHIVES, "readme_versions.txt"):
        path = raw / name
        expected_type = "rar" if name.endswith(".rar") else "text"
        is_valid = valid_file(path, expected_type)
        record: dict[str, object] = {
            "name": name,
            "official_url": f"{PADERBORN_DOWNLOAD_ROOT}/{name}",
            "local_path": str(path.relative_to(ROOT)),
            "present": path.is_file(),
            "valid_signature": is_valid,
        }
        if path.is_file():
            file_hash = sha256(path)
            record.update(size_bytes=path.stat().st_size, sha256=file_hash)
            checksum_lines.append(f"{file_hash}  {name}")
        records.append(record)

    metadata_dir = ROOT / "data/paderborn/metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    checksums = metadata_dir / "checksums.sha256"
    checksums.write_text("\n".join(checksum_lines) + ("\n" if checksum_lines else ""), encoding="utf-8")
    inventory = {
        "source": PADERBORN_DOWNLOAD_ROOT,
        "accessed_at": accessed_at,
        "expected_archive_count": len(PADERBORN_ARCHIVES),
        "present_archive_count": sum(bool(item["present"]) for item in records if str(item["name"]).endswith(".rar")),
        "extracted_bearing_states": sorted(
            path.name for path in (raw / "extracted").glob("*") if path.is_dir()
        ),
        "extracted_mat_file_count": sum(1 for _ in (raw / "extracted").glob("*/*.mat")),
        "extracted_fact_sheet_count": sum(1 for _ in (ROOT / "data/paderborn/docs").glob("*/*.pdf") if not _.name.startswith("measuring_log_")),
        "extracted_measurement_log_count": sum(1 for _ in (ROOT / "data/paderborn/docs").glob("*/measuring_log_*.pdf")),
        "files": records,
    }
    (metadata_dir / "dataset_files.json").write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return inventory


def source_record(source: Source, accessed_at: str) -> dict[str, object]:
    path = ROOT / source.local_path
    present = valid_file(path, source.file_type)
    return {
        "source_id": source.source_id,
        "title": source.title,
        "publisher": source.publisher,
        "source_type": source.source_type,
        "official_url": source.url,
        "local_path": source.local_path,
        "downloaded_at": (
            datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
            if present else None
        ),
        "accessed_at": accessed_at,
        "license": source.license_name,
        "license_status": source.license_status,
        "source_tier": source.source_tier,
        "rag_role": list(source.rag_role),
        "file_type": source.file_type,
        "sha256": sha256(path) if present else None,
        "status": "available" if present else "missing",
        "notes": source.notes,
    }


def write_source_manifest(inventory: dict[str, object], accessed_at: str) -> None:
    dataset_complete = inventory["present_archive_count"] == inventory["expected_archive_count"]
    dataset_files = [
        ROOT / "data/paderborn/raw" / str(item["name"])
        for item in inventory["files"]
        if bool(item["present"])
    ]
    dataset_downloaded_at = None
    if dataset_files:
        dataset_downloaded_at = datetime.fromtimestamp(
            max(path.stat().st_mtime for path in dataset_files), timezone.utc
        ).isoformat(timespec="seconds")
    fact_sheets = list((ROOT / "data/paderborn/docs").glob("*/*.pdf"))
    measurement_logs = [path for path in fact_sheets if path.name.startswith("measuring_log_")]
    fact_sheets = [path for path in fact_sheets if not path.name.startswith("measuring_log_")]
    extracted_count = len(inventory["extracted_bearing_states"])
    records: list[dict[str, object]] = [
        {
            "source_id": "PADERBORN_DATASET",
            "title": "Paderborn University Bearing DataCenter measurement archives",
            "publisher": "Paderborn University, KAt",
            "source_type": "official_dataset_collection",
            "official_url": PADERBORN_DOWNLOAD_ROOT + "/",
            "local_path": "data/paderborn/raw",
            "downloaded_at": dataset_downloaded_at,
            "accessed_at": accessed_at,
            "license": "CC BY-NC 4.0",
            "license_status": "noncommercial-use-with-attribution",
            "source_tier": "Tier 1",
            "rag_role": ["dataset_context", "ground_truth"],
            "file_type": "rar_collection",
            "sha256": collection_sha256(dataset_files),
            "status": "available" if dataset_complete else "partial",
            "notes": "Per-file SHA-256 values are stored in data/paderborn/metadata/checksums.sha256.",
        },
        {
            "source_id": "PADERBORN_DAMAGE_FACT_SHEETS",
            "title": "Paderborn bearing damage fact sheets",
            "publisher": "Paderborn University, KAt",
            "source_type": "dataset_embedded_document_collection",
            "official_url": PADERBORN_DOWNLOAD_ROOT + "/",
            "local_path": "data/paderborn/docs",
            "downloaded_at": accessed_at if fact_sheets else None,
            "accessed_at": accessed_at,
            "license": "CC BY-NC 4.0",
            "license_status": "noncommercial-use-with-attribution",
            "source_tier": "Tier 1",
            "rag_role": ["ground_truth", "damage_taxonomy"],
            "file_type": "pdf_collection",
            "sha256": collection_sha256(fact_sheets),
            "status": "partial" if fact_sheets and not dataset_complete else ("available" if fact_sheets else "missing"),
            "notes": f"Extracted for {extracted_count} of {len(PADERBORN_ARCHIVES)} bearing-state archives.",
        },
        {
            "source_id": "PADERBORN_MEASUREMENT_LOGS",
            "title": "Paderborn measurement logs",
            "publisher": "Paderborn University, KAt",
            "source_type": "dataset_embedded_document_collection",
            "official_url": PADERBORN_DOWNLOAD_ROOT + "/",
            "local_path": "data/paderborn/docs",
            "downloaded_at": accessed_at if measurement_logs else None,
            "accessed_at": accessed_at,
            "license": "CC BY-NC 4.0",
            "license_status": "noncommercial-use-with-attribution",
            "source_tier": "Tier 1",
            "rag_role": ["dataset_context", "ground_truth"],
            "file_type": "pdf_collection",
            "sha256": collection_sha256(measurement_logs),
            "status": "partial" if measurement_logs and not dataset_complete else ("available" if measurement_logs else "missing"),
            "notes": f"Extracted for {extracted_count} of {len(PADERBORN_ARCHIVES)} bearing-state archives.",
        },
    ]
    records.extend(source_record(source, accessed_at) for source in DOCUMENT_SOURCES)

    manifest_dir = ROOT / "knowledge/bearing_v1/manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "manifest_version": "1.0",
        "generated_at": accessed_at,
        "sources": records,
    }
    (manifest_dir / "source_manifest.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# Source Manifest",
        "",
        f"Generated: `{accessed_at}`",
        "",
        "| Source ID | Tier | Status | Publisher | Local path | SHA-256 |",
        "|---|---|---|---|---|---|",
    ]
    for record in records:
        digest = str(record["sha256"] or "-")
        lines.append(
            f"| {record['source_id']} | {record['source_tier']} | {record['status']} | "
            f"{record['publisher']} | `{record['local_path']}` | `{digest}` |"
        )
    lines.extend([
        "",
        "The JSON manifest is canonical and contains URLs, licensing, timestamps, RAG roles, and notes.",
        "Dataset archive checksums are listed in `data/paderborn/metadata/checksums.sha256`.",
        "",
    ])
    (manifest_dir / "SOURCE_MANIFEST.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        choices=("all", "sample", "none"),
        default="all",
        help="download all 32 archives, three representative archives, or no archives",
    )
    parser.add_argument("--skip-documents", action="store_true", help="do not download HTML/PDF sources")
    parser.add_argument(
        "--extract",
        action="store_true",
        help="test and extract the selected valid RAR archives, including embedded PDFs",
    )
    args = parser.parse_args()
    accessed_at = utc_now()
    errors: list[str] = []

    if not args.skip_documents:
        for source in DOCUMENT_SOURCES:
            try:
                outcome = download(source.url, ROOT / source.local_path, source.file_type)
                print(f"{outcome}: {source.source_id}")
            except (OSError, RuntimeError, urllib.error.URLError) as exc:
                message = f"{source.source_id}: {exc}"
                errors.append(message)
                print(f"ERROR: {message}", file=sys.stderr)

    raw = ROOT / "data/paderborn/raw"
    selected_archives = tuple(dataset_targets(args.dataset))
    for name in (*selected_archives, "readme_versions.txt"):
        file_type = "rar" if name.endswith(".rar") else "text"
        try:
            outcome = download(f"{PADERBORN_DOWNLOAD_ROOT}/{name}", raw / name, file_type)
            print(f"{outcome}: {name}")
        except (OSError, RuntimeError, urllib.error.URLError) as exc:
            message = f"{name}: {exc}"
            errors.append(message)
            print(f"ERROR: {message}", file=sys.stderr)

    if args.extract:
        try:
            extract_archives(selected_archives)
            print(f"archive extraction complete: {len(selected_archives)} selected")
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            message = f"archive extraction: {exc}"
            errors.append(message)
            print(f"ERROR: {message}", file=sys.stderr)

    inventory = write_dataset_metadata(accessed_at)
    write_source_manifest(inventory, accessed_at)
    print(
        f"dataset archives: {inventory['present_archive_count']}/{inventory['expected_archive_count']} present"
    )
    if errors:
        print(f"completed with {len(errors)} error(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
