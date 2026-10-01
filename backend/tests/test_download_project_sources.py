from importlib import util
from pathlib import Path
import sys


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts/download_project_sources.py"
SPEC = util.spec_from_file_location("download_project_sources", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
download_project_sources = util.module_from_spec(SPEC)
sys.modules[SPEC.name] = download_project_sources
SPEC.loader.exec_module(download_project_sources)


def test_dataset_target_modes() -> None:
    assert tuple(download_project_sources.dataset_targets("none")) == ()
    assert tuple(download_project_sources.dataset_targets("sample")) == (
        "K001.rar",
        "KA01.rar",
        "KI01.rar",
    )
    assert len(tuple(download_project_sources.dataset_targets("all"))) == 32


def test_signature_validation(tmp_path: Path) -> None:
    pdf = tmp_path / "guide.pdf"
    rar = tmp_path / "dataset.rar"
    html = tmp_path / "source.html"
    invalid = tmp_path / "invalid.pdf"

    pdf.write_bytes(b"%PDF-1.7\ncontent")
    rar.write_bytes(b"Rar!\x1a\x07\x00content")
    html.write_bytes(b"<!DOCTYPE html><html></html>")
    invalid.write_bytes(b"not a PDF")

    assert download_project_sources.valid_file(pdf, "pdf")
    assert download_project_sources.valid_file(rar, "rar")
    assert download_project_sources.valid_file(html, "html")
    assert not download_project_sources.valid_file(invalid, "pdf")


def test_sha256_is_stable(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"official-source")

    assert download_project_sources.sha256(source) == (
        "c13f57a826ba58f1d170a58078a2bca6a78de42adf9283a4bc301e0f6b843fcb"
    )
