"""Serializes Compass-specific task metadata (role, quadrant, is_big_rock,
project) into the Google Task's `notes` field, and parses it back out —
Google Tasks has no equivalent fields, so without this a round-trip through
Google Tasks would silently drop that metadata. See SPEC §5.

Format: a single JSON line prefixed by a marker, followed by any free-text
notes the user wrote. JSON (not "key=value" tokens) specifically because
role/project names can contain spaces.
"""
import json
from dataclasses import dataclass

_MARKER = "[compass]"


@dataclass
class TaskMetadata:
    role_name: str | None = None
    quadrant: str | None = None
    is_big_rock: bool = False
    project_title: str | None = None


def encode(metadata: TaskMetadata, free_notes: str | None) -> str:
    payload = {
        "role": metadata.role_name,
        "quadrant": metadata.quadrant,
        "is_big_rock": metadata.is_big_rock,
        "project": metadata.project_title,
    }
    header = f"{_MARKER} {json.dumps(payload)}"
    return f"{header}\n{free_notes}" if free_notes else header


def decode(notes: str | None) -> tuple[TaskMetadata, str | None]:
    if not notes or not notes.startswith(_MARKER):
        return TaskMetadata(), notes

    header, _, rest = notes.partition("\n")
    raw = header[len(_MARKER) :].strip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return TaskMetadata(), notes

    metadata = TaskMetadata(
        role_name=payload.get("role"),
        quadrant=payload.get("quadrant"),
        is_big_rock=bool(payload.get("is_big_rock", False)),
        project_title=payload.get("project"),
    )
    return metadata, (rest or None)
