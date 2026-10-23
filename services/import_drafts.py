"""
Claude Cowork Import Draft Pipeline
====================================

Implements the design in `CLAUDE_COWORK_INTEGRATION.md`: an authorized Claude
Cowork Skill (running somewhere with filesystem access to wherever the active
Viper database lives — see `integrations/claude-cowork/SKILL.md`) writes
versioned JSON draft files into a `cowork_imports/incoming/` folder colocated
with the `.db` file. Viper never writes anything to its database from a draft
without a human reviewer explicitly approving each proposal (see
`ui/tabs/cowork_import.py`).

Nothing here talks to Teams, Outlook, or the network — this module only
validates/applies/archives local JSON files that something else (the Cowork
Skill) already produced.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from db.models import Case, CommunicationLogEntry, DueOut, TimelineEvent
from ui.constants import COMMUNICATION_TYPES, DUE_OUT_PRIORITIES, DUE_OUT_STATUSES

SCHEMA_VERSION = "viper-import-draft-v1"

INCIDENT_NUMBER_RE = re.compile(r"INC-\d+")
# A CAN email's subject must mention "CAN" and an incident number somewhere,
# in either order — used by the Cowork Skill (and available here for Viper-side
# sanity checks/tests), not a hard Viper-side validation rule.
CAN_SUBJECT_RE = re.compile(r"(?=.*\bCAN\b)(?=.*INC-\d+)", re.IGNORECASE)

REQUIRED_SOURCE_FIELDS = {"kind", "subject", "sender", "received_at", "reference"}

# Allowed fields per proposal `kind`, matching the three record types the
# initial pilot supports (Import Rule set in CLAUDE_COWORK_INTEGRATION.md).
# "confidence" and "evidence_excerpt" are optional on every kind.
_COMMON_OPTIONAL_FIELDS = {"confidence", "evidence_excerpt"}
PROPOSAL_FIELDS: dict[str, dict[str, set[str]]] = {
    "timeline": {
        "required": {"timestamp", "description"},
        "optional": {"type"} | _COMMON_OPTIONAL_FIELDS,
    },
    "communication_log": {
        "required": {"timestamp", "comm_type", "summary"},
        "optional": {"notes"} | _COMMON_OPTIONAL_FIELDS,
    },
    "due_out": {
        "required": {"task"},
        "optional": {"owner", "priority", "status", "due_date"} | _COMMON_OPTIONAL_FIELDS,
    },
}


def looks_like_can_email(subject: str) -> bool:
    """Whether an email subject matches the CAN-report detection rule (contains
    "CAN" and an `INC-#` pattern, in any order)."""
    return bool(CAN_SUBJECT_RE.search(subject or ""))


class DraftValidationError(ValueError):
    """Raised when a draft (or one proposal within it) fails validation."""


@dataclass(frozen=True)
class CoworkImportPaths:
    """The three folders Viper watches/writes, colocated with the active database."""

    root: Path
    incoming: Path
    approved: Path
    rejected: Path


def get_cowork_import_paths(db_path: Path | str) -> CoworkImportPaths:
    root = Path(db_path).resolve().parent / "cowork_imports"
    return CoworkImportPaths(
        root=root, incoming=root / "incoming", approved=root / "approved", rejected=root / "rejected"
    )


def ensure_cowork_import_paths(db_path: Path | str) -> CoworkImportPaths:
    """Resolve the import folders for `db_path`, creating any that don't exist yet."""
    paths = get_cowork_import_paths(db_path)
    for folder in (paths.incoming, paths.approved, paths.rejected):
        folder.mkdir(parents=True, exist_ok=True)
    return paths


def get_active_db_path() -> Path:
    """The filesystem path of the currently open SQLite database."""
    from db.database import get_engine  # local import: avoids a hard dependency at module import time

    database = get_engine().url.database
    if not database:
        raise RuntimeError("No active database file is open.")
    return Path(database)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _validate_proposal(proposal, index: int) -> list[str]:
    if not isinstance(proposal, dict):
        return [f"Proposal {index}: must be a JSON object."]

    kind = proposal.get("kind")
    if kind not in PROPOSAL_FIELDS:
        return [f"Proposal {index}: unsupported kind {kind!r}; must be one of {sorted(PROPOSAL_FIELDS)}."]

    spec = PROPOSAL_FIELDS[kind]
    allowed_fields = spec["required"] | spec["optional"] | {"kind"}
    errors = []

    missing = spec["required"] - proposal.keys()
    if missing:
        errors.append(f"Proposal {index} ({kind}): missing required field(s): {', '.join(sorted(missing))}.")

    unknown = proposal.keys() - allowed_fields
    if unknown:
        errors.append(f"Proposal {index} ({kind}): unknown field(s): {', '.join(sorted(unknown))}.")

    if "timestamp" in proposal:
        try:
            _parse_timestamp(proposal["timestamp"])
        except (TypeError, ValueError):
            errors.append(f"Proposal {index} ({kind}): invalid timestamp {proposal.get('timestamp')!r}.")

    if kind == "communication_log" and proposal.get("comm_type") not in (None,) and "comm_type" in proposal:
        if proposal["comm_type"] not in COMMUNICATION_TYPES:
            errors.append(
                f"Proposal {index} (communication_log): comm_type {proposal['comm_type']!r} is not one of "
                f"{COMMUNICATION_TYPES}."
            )

    if kind == "due_out":
        if "priority" in proposal and proposal["priority"] not in DUE_OUT_PRIORITIES:
            errors.append(f"Proposal {index} (due_out): priority {proposal['priority']!r} is not one of {DUE_OUT_PRIORITIES}.")
        if "status" in proposal and proposal["status"] not in DUE_OUT_STATUSES:
            errors.append(f"Proposal {index} (due_out): status {proposal['status']!r} is not one of {DUE_OUT_STATUSES}.")
        if proposal.get("due_date"):
            try:
                datetime.strptime(proposal["due_date"], "%Y-%m-%d")
            except ValueError:
                errors.append(f"Proposal {index} (due_out): due_date must be YYYY-MM-DD, got {proposal['due_date']!r}.")

    return errors


def validate_draft(data) -> list[str]:
    """Return a list of human-readable validation errors; empty list means valid."""
    if not isinstance(data, dict):
        return ["Draft must be a JSON object."]

    errors = []

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Unsupported schema_version {data.get('schema_version')!r}; expected {SCHEMA_VERSION!r}.")

    incident_number = data.get("incident_number")
    if not incident_number or not INCIDENT_NUMBER_RE.fullmatch(str(incident_number)):
        errors.append("incident_number is missing or does not match the INC-### convention.")

    source = data.get("source")
    if not isinstance(source, dict):
        errors.append("source is missing or is not a JSON object.")
    else:
        missing_source = REQUIRED_SOURCE_FIELDS - source.keys()
        if missing_source:
            errors.append(f"source is missing field(s): {', '.join(sorted(missing_source))}.")

    proposals = data.get("proposals")
    if not isinstance(proposals, list) or not proposals:
        errors.append("proposals must be a non-empty list.")
    else:
        for index, proposal in enumerate(proposals):
            errors.extend(_validate_proposal(proposal, index))

    return errors


@dataclass
class DraftFile:
    """One parsed (and validated) draft JSON file sitting in `incoming/`."""

    path: Path
    data: dict | None
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.data is not None and not self.errors


def scan_incoming_drafts(paths: CoworkImportPaths) -> list[DraftFile]:
    """Parse and validate every `*.json` file in `incoming/`, oldest first (the
    naming convention `<timestamp>_<incident_number>.json` sorts chronologically)."""
    drafts: list[DraftFile] = []
    if not paths.incoming.exists():
        return drafts
    for file_path in sorted(paths.incoming.glob("*.json")):
        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            drafts.append(DraftFile(path=file_path, data=None, errors=[f"Could not parse JSON: {exc}"]))
            continue
        drafts.append(DraftFile(path=file_path, data=raw, errors=validate_draft(raw)))
    return drafts


def find_case_by_incident_number(session, incident_number: str) -> Case | None:
    return session.query(Case).filter(Case.incident_number == incident_number).one_or_none()


def _to_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def detect_duplicate(session, case_id: int, proposal: dict) -> bool:
    """A best-effort, never-blocking duplicate hint for the reviewer (Import Rule 7
    in CLAUDE_COWORK_INTEGRATION.md — warn only, reviewer always decides)."""
    kind = proposal.get("kind")
    try:
        if kind == "timeline":
            target = _to_naive_utc(_parse_timestamp(proposal["timestamp"]))
            description = (proposal.get("description") or "").strip().lower()
            existing = session.query(TimelineEvent).filter(TimelineEvent.case_id == case_id).all()
            return any(
                abs((_to_naive_utc(record.timestamp) - target).total_seconds()) < 60
                and record.description.strip().lower() == description
                for record in existing
            )
        if kind == "communication_log":
            target = _to_naive_utc(_parse_timestamp(proposal["timestamp"]))
            comm_type = proposal.get("comm_type")
            existing = session.query(CommunicationLogEntry).filter(CommunicationLogEntry.case_id == case_id).all()
            return any(
                abs((_to_naive_utc(record.timestamp) - target).total_seconds()) < 60
                and record.comm_type == comm_type
                for record in existing
            )
        if kind == "due_out":
            task = (proposal.get("task") or "").strip().lower()
            existing = (
                session.query(DueOut)
                .filter(DueOut.case_id == case_id, DueOut.status != "Completed")
                .all()
            )
            return any(record.task.strip().lower() == task for record in existing)
    except (KeyError, TypeError, ValueError):
        return False
    return False


def apply_proposal(session, case_id: int, proposal: dict) -> None:
    """Create the one new row a single approved proposal represents. Caller owns
    the session/transaction (use `db.get_session()`)."""
    kind = proposal.get("kind")
    if kind == "timeline":
        session.add(
            TimelineEvent(
                case_id=case_id,
                timestamp=_parse_timestamp(proposal["timestamp"]),
                description=proposal["description"],
                type=proposal.get("type", "communication"),
            )
        )
    elif kind == "communication_log":
        session.add(
            CommunicationLogEntry(
                case_id=case_id,
                timestamp=_parse_timestamp(proposal["timestamp"]),
                comm_type=proposal["comm_type"],
                summary=proposal.get("summary"),
                notes=proposal.get("notes"),
            )
        )
    elif kind == "due_out":
        session.add(
            DueOut(
                case_id=case_id,
                task=proposal["task"],
                owner=proposal.get("owner"),
                priority=proposal.get("priority", "Medium"),
                status=proposal.get("status", "Pending"),
                due_date=proposal.get("due_date"),
            )
        )
    else:
        raise DraftValidationError(f"Unsupported proposal kind: {kind!r}")


def _unique_destination(path: Path) -> Path:
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def finalize_draft(
    draft: DraftFile, paths: CoworkImportPaths, decisions: list[dict], reviewer: str
) -> Path:
    """Append a local audit record to the draft content and move the whole file
    (never delete) into `approved/` (if anything was approved) or `rejected/`
    (if every proposal was rejected)."""
    data = dict(draft.data or {})
    data["review"] = {
        "reviewer": reviewer,
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "decisions": decisions,
    }
    any_approved = any(decision.get("decision") == "approved" for decision in decisions)
    destination_dir = paths.approved if any_approved else paths.rejected
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = _unique_destination(destination_dir / draft.path.name)
    destination_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    draft.path.unlink(missing_ok=True)
    return destination_path


# --- Retention (local setting, same preferences-file pattern as
# ui/database_locations.py) --------------------------------------------------

_APP_DATA_ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
_SETTINGS_PATH = _APP_DATA_ROOT / "BastionCommand" / "Viper" / "cowork_import_settings.json"
DEFAULT_RETENTION_DAYS = 30


def get_retention_days() -> int:
    try:
        raw = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        return int(raw.get("retention_days", DEFAULT_RETENTION_DAYS))
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return DEFAULT_RETENTION_DAYS


def set_retention_days(days: int) -> None:
    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SETTINGS_PATH.write_text(json.dumps({"retention_days": int(days)}), encoding="utf-8")


def purge_expired_drafts(paths: CoworkImportPaths, retention_days: int | None = None) -> int:
    """Delete `approved/`/`rejected/` files older than the retention window.
    `incoming/` is never touched here — those are still pending review."""
    retention_days = get_retention_days() if retention_days is None else retention_days
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    purged = 0
    for folder in (paths.approved, paths.rejected):
        if not folder.exists():
            continue
        for file_path in folder.glob("*.json"):
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                file_path.unlink(missing_ok=True)
                purged += 1
    return purged
