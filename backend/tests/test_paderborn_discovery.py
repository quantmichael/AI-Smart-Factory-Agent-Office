from pathlib import Path

from app.data.adapters.paderborn import PaderbornDatasetAdapter


def test_discovery_builds_metadata_only_index(
    paderborn_fixture: Path, monkeypatch
) -> None:
    adapter = PaderbornDatasetAdapter(paderborn_fixture)
    monkeypatch.setattr(
        "app.data.adapters.paderborn.loadmat",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("raw load not expected")),
    )

    measurements = adapter.list_measurements()

    assert len(measurements) == 2
    assert {item.bearing_id for item in measurements} == {"K001", "KA01"}
    assert all(item.source_reference.endswith(".mat") for item in measurements)
