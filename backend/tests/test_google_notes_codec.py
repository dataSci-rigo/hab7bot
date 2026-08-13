from app.integrations.google.notes_codec import TaskMetadata, decode, encode


def test_round_trips_metadata_and_free_notes() -> None:
    metadata = TaskMetadata(
        role_name="Engineer", quadrant="Q2", is_big_rock=True, project_title="Migrate DB"
    )
    encoded = encode(metadata, "Some free-text notes")

    decoded_metadata, free_notes = decode(encoded)

    assert decoded_metadata == metadata
    assert free_notes == "Some free-text notes"


def test_round_trips_metadata_with_no_free_notes() -> None:
    metadata = TaskMetadata(role_name="Engineer", quadrant="Q1")
    encoded = encode(metadata, None)

    decoded_metadata, free_notes = decode(encoded)

    assert decoded_metadata == metadata
    assert free_notes is None


def test_decode_plain_notes_without_marker() -> None:
    metadata, free_notes = decode("just some notes, never synced")
    assert metadata == TaskMetadata()
    assert free_notes == "just some notes, never synced"


def test_decode_none_notes() -> None:
    metadata, free_notes = decode(None)
    assert metadata == TaskMetadata()
    assert free_notes is None


def test_decode_malformed_marker_falls_back_to_raw_notes() -> None:
    notes = "[compass] not valid json"
    metadata, free_notes = decode(notes)
    assert metadata == TaskMetadata()
    assert free_notes == notes
