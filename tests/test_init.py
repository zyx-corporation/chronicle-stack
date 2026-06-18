import pytest

from chronicle.errors import ChronicleNotInitializedError
from chronicle.services.chronicle_service import ChronicleService


def test_init_creates_chronicle(tmp_path):
    service = ChronicleService(tmp_path)
    metadata = service.init("Test Chronicle")

    assert metadata.title == "Test Chronicle"
    assert metadata.chronicle_id.startswith("chr_")
    assert service.paths.events_file.exists()
    assert service.paths.metadata_file.exists()
    assert service.paths.ai_indexes_dir.exists()

    events = service.jsonl.read_all()
    assert len(events) == 1
    assert events[0].event_type.value == "chronicle_created"


def test_require_initialized_raises_when_missing(tmp_path):
    service = ChronicleService(tmp_path)
    with pytest.raises(ChronicleNotInitializedError):
        service.require_initialized()
