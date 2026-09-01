"""Local JSON storage for generated notes history."""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data"
HISTORY_FILE = DATA_DIRECTORY / "notes_history.json"


class StorageError(Exception):
    """Raised when the local history cannot be read or written safely."""


def _validate_note(item: Any) -> dict | None:
    """Return a trusted history entry, or ignore malformed legacy data."""
    if not isinstance(item, dict):
        return None

    required_fields = ("topic", "notes", "timestamp")
    if not all(isinstance(item.get(field), str) and item[field].strip() for field in required_fields):
        return None

    return {
        "id": str(item.get("id") or uuid.uuid4()),
        "topic": item["topic"].strip(),
        "notes": item["notes"].strip(),
        "timestamp": item["timestamp"],
    }


def load_history() -> list[dict]:
    """Load all valid entries, newest first, from the local JSON history file."""
    if not HISTORY_FILE.exists():
        return []

    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as history_file:
            raw_history = json.load(history_file)
    except (OSError, json.JSONDecodeError) as error:
        raise StorageError("Unable to read saved notes history.") from error

    if not isinstance(raw_history, list):
        raise StorageError("Saved notes history has an unexpected format.")

    history = [entry for item in raw_history if (entry := _validate_note(item))]
    return sorted(history, key=lambda entry: entry["timestamp"], reverse=True)


def _write_history(history: list[dict]) -> None:
    """Write history atomically to avoid a partial file if the app stops mid-save."""
    try:
        DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=DATA_DIRECTORY, delete=False
        ) as temporary_file:
            json.dump(history, temporary_file, ensure_ascii=False, indent=2)
            temporary_path = Path(temporary_file.name)
        os.replace(temporary_path, HISTORY_FILE)
    except OSError as error:
        try:
            if "temporary_path" in locals() and temporary_path.exists():
                temporary_path.unlink()
        except OSError:
            pass
        raise StorageError("Unable to save notes history locally.") from error


def save_note(topic: str, notes: str) -> dict:
    """Add one note to local history and return the newly created entry."""
    entry = {
        "id": str(uuid.uuid4()),
        "topic": topic.strip(),
        "notes": notes.strip(),
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    }
    if not entry["topic"] or not entry["notes"]:
        raise StorageError("A topic and generated notes are required to save history.")

    history = load_history()
    history.insert(0, entry)
    _write_history(history)
    return entry


def clear_history() -> None:
    """Replace saved history with an empty list while retaining a valid JSON file."""
    _write_history([])
