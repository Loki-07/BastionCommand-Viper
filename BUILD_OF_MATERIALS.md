# Bastion Command: Viper - Build of Materials

**Prepared:** 2026-09-06  
**Last updated:** 2026-10-26  
**Scope:** Active desktop application in this repository (`BastionCommand-Viper`).
The legacy `csim-app` project in the adjacent workspace is reference-only and is
not part of this inventory.

## Purpose And Verification Basis

This document identifies the software components, runtime facilities, imported
modules, local assets, and data flows that Corporate Compliance should review
before distribution or production use.

Direct dependency versions come from [requirements.txt](requirements.txt).
Installed versions, package relationships, and license expressions were
re-checked from the project's local `.venv` Python 3.12.4 environment on
2026-10-26 using `python -m pip show`; the environment passed `python -m pip
check` with no broken requirements. This refresh added the `cryptography`
direct dependency (database encryption-at-rest, see below) and its transitive
`cffi`/`pycparser` dependencies, and picked up version drift in `greenlet`,
`typing_extensions`, and `Pillow` since the 2026-09-06 baseline. License values
below are package-distribution metadata, not a substitute for a legal review of
the complete license text or its notice requirements.

## Application Summary

| Item | Value |
| --- | --- |
| Application | Bastion Command: Viper |
| Application type | Local Windows desktop incident-response case-management application |
| Language/runtime | Python 3.12.4 |
| User interface | Tkinter/ttk with ttkbootstrap theming |
| Data store | User-selected local SQLite database (default suggestion: `bastion_command.db`) via SQLAlchemy; optionally stored at rest as a pure-Python encrypted envelope container, decrypted to a local working copy only while the app is running (see Security section) |
| Networking | No network-client, HTTP, socket, or telemetry imports found in the active Python source |
| Local data ingestion | Optional "Claude Cowork Import" workflow reads externally-produced JSON draft files from a local folder colocated with the database; every proposed database change requires explicit human review/approval before it is written (see Security section) |
| User-initiated outputs | Local report export (text/Markdown/JSON) and clipboard copy |

## Third-Party Python Components

### Direct Dependencies

These are explicitly pinned for deployment in [requirements.txt](requirements.txt).

| Component | Installed / required version | Purpose in Viper | License reported by installed distribution | Compliance review |
| --- | --- | --- | --- | --- |
| SQLAlchemy | 2.0.45 | ORM, SQLite connection management, schema initialization/migration | MIT | Retain required copyright/license notices when distributing. |
| ttkbootstrap | 1.10.1 | Themed ttk/Tkinter widgets, including the custom Bastion theme | MIT | Retain required copyright/license notices when distributing. |
| tzdata | 2026.3 | IANA time-zone database used by Python `zoneinfo` where the operating system does not provide time-zone data | Apache-2.0 | Review Apache-2.0 notice and attribution requirements. |
| cryptography | >=42 (installed: 50.0.2) | Pure-Python-facing envelope encryption-at-rest for the SQLite database file (Fernet/AES + PBKDF2-HMAC-SHA256 key derivation) in `security/envelope.py` | Apache-2.0 OR BSD-3-Clause | Confirm the organization's accepted choice between the dual-offered licenses and retain the chosen license's notice. |

### Transitive Runtime Dependencies

These were installed because they are required by the direct components above.
They should be included in the compliance and vulnerability review even though
they are not listed directly in `requirements.txt`.

| Component | Installed version | Brought in by | Purpose | License reported by installed distribution | Compliance review |
| --- | --- | --- | --- | --- |
| greenlet | 3.5.6 | SQLAlchemy | Optional/in-process concurrency support used by SQLAlchemy installations | `MIT AND PSF-2.0` | Review both applicable license texts and notice obligations. |
| typing_extensions | 4.16.0 | SQLAlchemy | Backported and experimental typing support | PSF-2.0 | Retain the required Python Software Foundation license notice. |
| Pillow | 13.0.0 | ttkbootstrap | Image handling used by ttkbootstrap; supports the PNG title/window icon | MIT-CMU | Review the distribution license text and included notices. |
| cffi | 2.1.1 | cryptography | Foreign-function interface used by `cryptography`'s native bindings | MIT-0 | Retain required copyright/license notices when distributing. |
| pycparser | 3.12 | cffi | C parser used by `cffi` at build/import time | BSD-3-Clause | Retain required copyright/license notices when distributing. |

### Environment Components Not Installed From `requirements.txt`

These are bundled with or supplied by the selected Python/operating-system
runtime rather than fetched by the application’s dependency file.

| Component | Observed version | Use in Viper | Review note |
| --- | --- | --- | --- |
| CPython | 3.12.4 | Executes the application and provides most imported modules | Corporate packaging should use an approved CPython distribution and include its license notices. |
| Tk/Tcl | 8.6.13 | Native desktop widgets underlying Tkinter/ttkbootstrap | Review the Tk/Tcl terms included with the approved Python distribution. |
| SQLite | 3.45.3 | Embedded local database engine used through Python's SQLite support | SQLite is public domain; confirm policy treatment for bundled components. |
| Windows fonts | OS supplied | `Bahnschrift`, with `Impact`/`Arial Black` fallbacks, is used when installed for the header title | Validate that use/distribution follows the Windows font license and that the application does not redistribute these font files. |

## Source Import Inventory

### Third-Party Imports Used By Active Source

| Import | Used for |
| --- | --- |
| `sqlalchemy` / `sqlalchemy.orm` | Data models, sessions, queries, database schema and migration checks |
| `ttkbootstrap` / `ttkbootstrap.style` | Desktop interface, widget styling, custom `bastion` theme |
| `cryptography.fernet` / `cryptography.hazmat.primitives` | Envelope encryption/decryption and PBKDF2-HMAC-SHA256 key derivation for the optional encrypted-database container (`security/envelope.py`, `security/encrypted_database.py`) |

### Python Standard-Library Imports Used By Active Source

`base64`, `collections.abc`, `contextlib`, `dataclasses`, `datetime`, `hashlib`,
`json`, `os`, `pathlib`, `re`, `struct`, `tkinter` (including `filedialog`,
`font`, `messagebox`, and ttk), `typing`, and `zoneinfo` are used. These are
supplied by CPython; they do not add separately downloaded packages to this
project.

Internal imports are limited to the local `db`, `security`, `services`, and
`ui` packages.

## Local Assets And Data

| Asset / data | Location | Use | Compliance action |
| --- | --- | --- | --- |
| Rook PNG graphic | [ui/assets/PO_Rook.png](ui/assets/PO_Rook.png) | Window/taskbar icon and application header graphic | Confirm the organization owns the supplied image or has documented permission to use and distribute it. Store source/provenance evidence with the release record. |
| SQLite case database | User-selected local `.db`/SQLite file; `bastion_command.db` is the startup suggestion | Holds incident/case content, contacts, indicators, case updates, and related operational data | Treat as potentially sensitive incident-response data. Define encryption-at-rest, access-control, retention, backup, and secure-deletion requirements before deployment. Do not ship production data in installation media. |
| Encrypted database container | Same user-selected path, when the user opts into encryption at database creation | Whole-file Fernet-encrypted container (`security/envelope.py`) wrapping the SQLite file; the passphrase is prompted at every launch and is never written to disk | Confirm the PBKDF2-HMAC-SHA256 iteration count (600,000, OWASP's 2023 minimum) meets policy; review passphrase-loss recovery posture (no rotation/rekey or recovery path exists yet). |
| Decrypted working-copy cache | `%LOCALAPPDATA%\BastionCommand\Viper\decrypted_cache\<hash>.db` on Windows | Plaintext SQLite file SQLAlchemy actually opens while an encrypted database is in use; re-encrypted and best-effort shredded on clean app close | Treat as sensitive plaintext while present. Confirm endpoint disk-encryption/access-control compensates for the window between app launch and shutdown, and for any leftover copy after an unclean shutdown. |
| Database-location preferences | `%LOCALAPPDATA%\BastionCommand\Viper\database_locations.json` on Windows | Stores recent and user-marked favorite database file paths; never stores case content | Treat database paths as local operational metadata. Include the preference file in endpoint-backup/retention decisions where appropriate. |
| Claude Cowork import drop folder | `cowork_imports/{incoming,approved,rejected}/` colocated with the active database file | Holds externally-produced JSON draft files (from an authorized Claude Cowork Skill) proposing Timeline/Communication Log/Due Out entries; every proposal is schema-validated and requires human approval before being applied, and approved/rejected files are retained for a configurable period (default 30 days) before cleanup | Treat incoming JSON as untrusted external input even though it is schema-validated and never auto-applied. Confirm the folder's filesystem permissions and the retention policy meet data-handling requirements. |
| Cowork import settings | `%LOCALAPPDATA%\BastionCommand\Viper\cowork_import_settings.json` on Windows | Stores the configurable retention-days setting for the import drop folder; never stores case content | Include in endpoint-backup/retention decisions where appropriate. |
| Generated reports | User-selected local path | JSON, Markdown, or text export of case data | Exports may contain sensitive data. Apply classification, approved-storage, and sharing controls. |
| Clipboard content | Local user clipboard | User-initiated report copy | Treat copied report contents as sensitive; document the operational handling expectation. |

## Security And Deployment Notes

- The active source scan found no HTTP client, socket, subprocess, browser,
  telemetry, analytics, or cloud-storage imports. Viper does not itself transmit
  case data over the network.
- SQLAlchemy opens a user-selected local SQLite file through `sqlite:///...`; the
  product has no server-side database dependency.
- The database chooser records successfully opened locations in a local recent-list
  and optionally as user-marked favorites. The preference file contains paths only,
  never database content or credentials.
- Encryption-at-rest is optional and pure-Python (`cryptography`'s Fernet
  recipe + PBKDF2-HMAC-SHA256), opted into only when creating a new database.
  The passphrase is requested at every launch and held in memory only for the
  session; it is never persisted to disk, logged, or transmitted. There is
  currently no passphrase rotation/rekey flow and no in-place migration path
  for encrypting an already-existing plaintext database.
- The Claude Cowork Import workflow is a local file-based data-ingestion path,
  not a network integration: Viper only reads/validates/archives JSON files
  that an external, separately-authorized tool has already written to a local
  folder. Every parsed proposal is schema-validated and requires a human
  reviewer to explicitly approve, edit, or reject it before any database write
  occurs; nothing is auto-applied. Treat the authoring tool (the Claude Cowork
  Skill itself) and its access to Teams/Outlook content as a separate system
  outside this BOM's scope, reviewed on its own.
- Version pins exist for all four direct Python dependencies. The transitive
  versions above are an observed environment snapshot, not a checked-in lock
  file. Before release, generate and approve a fully resolved lock/SBOM from the
  build environment so repeatable builds use the same transitive versions.
- No project `LICENSE`, `NOTICE`, `pyproject.toml`, `setup.py`, or other
  application-level licensing file was found in this repository. Confirm the
  proprietary ownership/distribution classification of Viper source code and
  provide any required product license or third-party attribution bundle.
- The adjacent legacy `csim-app` workspace may have separate dependencies and
  licenses. It is deliberately excluded from this desktop-app BOM.

