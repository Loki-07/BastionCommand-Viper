# Bastion Command: Viper - Build of Materials

**Prepared:** 2026-09-06  
**Scope:** Active desktop application in this repository (`BastionCommand-Viper`).
The legacy `csim-app` project in the adjacent workspace is reference-only and is
not part of this inventory.

## Purpose And Verification Basis

This document identifies the software components, runtime facilities, imported
modules, local assets, and data flows that Corporate Compliance should review
before distribution or production use.

Direct dependency versions come from [requirements.txt](requirements.txt).
Installed versions, package relationships, and license expressions were checked
from the local Python 3.12.4 environment on 2026-09-06 using `python -m pip
show`; the environment passed `python -m pip check` with no broken requirements.
License values below are package-distribution metadata, not a substitute for a
legal review of the complete license text or its notice requirements.

## Application Summary

| Item | Value |
| --- | --- |
| Application | Bastion Command: Viper |
| Application type | Local Windows desktop incident-response case-management application |
| Language/runtime | Python 3.12.4 |
| User interface | Tkinter/ttk with ttkbootstrap theming |
| Data store | Local SQLite database (`bastion_command.db`) via SQLAlchemy |
| Networking | No network-client, HTTP, socket, or telemetry imports found in the active Python source |
| User-initiated outputs | Local report export (text/Markdown/JSON) and clipboard copy |

## Third-Party Python Components

### Direct Dependencies

These are explicitly pinned for deployment in [requirements.txt](requirements.txt).

| Component | Installed / required version | Purpose in Viper | License reported by installed distribution | Compliance review |
| --- | --- | --- | --- | --- |
| SQLAlchemy | 2.0.45 | ORM, SQLite connection management, schema initialization/migration | MIT | Retain required copyright/license notices when distributing. |
| ttkbootstrap | 1.10.1 | Themed ttk/Tkinter widgets, including the custom Bastion theme | MIT | Retain required copyright/license notices when distributing. |
| tzdata | 2026.3 | IANA time-zone database used by Python `zoneinfo` where the operating system does not provide time-zone data | Apache-2.0 | Review Apache-2.0 notice and attribution requirements. |

### Transitive Runtime Dependencies

These were installed because they are required by the direct components above.
They should be included in the compliance and vulnerability review even though
they are not listed directly in `requirements.txt`.

| Component | Installed version | Brought in by | Purpose | License reported by installed distribution | Compliance review |
| --- | --- | --- | --- | --- |
| greenlet | 3.3.0 | SQLAlchemy | Optional/in-process concurrency support used by SQLAlchemy installations | `MIT AND Python-2.0` | Review both applicable license texts and notice obligations. |
| typing_extensions | 4.15.0 | SQLAlchemy | Backported and experimental typing support | PSF-2.0 | Retain the required Python Software Foundation license notice. |
| Pillow | 12.1.0 | ttkbootstrap | Image handling used by ttkbootstrap; supports the PNG title/window icon | MIT-CMU | Review the distribution license text and included notices. |

### Environment Components Not Installed From `requirements.txt`

These are bundled with or supplied by the selected Python/operating-system
runtime rather than fetched by the application’s dependency file.

| Component | Observed version | Use in Viper | Review note |
| --- | --- | --- | --- |
| CPython | 3.12.4 | Executes the application and provides most imported modules | Corporate packaging should use an approved CPython distribution and include its license notices. |
| Tk | 8.6 | Native desktop widgets underlying Tkinter/ttkbootstrap | Review the Tk/Tcl terms included with the approved Python distribution. |
| SQLite | 3.45.3 | Embedded local database engine used through Python's SQLite support | SQLite is public domain; confirm policy treatment for bundled components. |
| Windows fonts | OS supplied | `Bahnschrift`, with `Impact`/`Arial Black` fallbacks, is used when installed for the header title | Validate that use/distribution follows the Windows font license and that the application does not redistribute these font files. |

## Source Import Inventory

### Third-Party Imports Used By Active Source

| Import | Used for |
| --- | --- |
| `sqlalchemy` / `sqlalchemy.orm` | Data models, sessions, queries, database schema and migration checks |
| `ttkbootstrap` / `ttkbootstrap.style` | Desktop interface, widget styling, custom `bastion` theme |

### Python Standard-Library Imports Used By Active Source

`collections.abc`, `contextlib`, `datetime`, `json`, `pathlib`, `tkinter`
(including `filedialog`, `font`, `messagebox`, and ttk), `typing`, and
`zoneinfo` are used. These are supplied by CPython; they do not add separately
downloaded packages to this project.

Internal imports are limited to the local `db` and `ui` packages.

## Local Assets And Data

| Asset / data | Location | Use | Compliance action |
| --- | --- | --- | --- |
| Rook PNG graphic | [ui/assets/PO_Rook.png](ui/assets/PO_Rook.png) | Window/taskbar icon and application header graphic | Confirm the organization owns the supplied image or has documented permission to use and distribute it. Store source/provenance evidence with the release record. |
| SQLite case database | `bastion_command.db` at the application root by default | Holds incident/case content, contacts, indicators, case updates, and related operational data | Treat as potentially sensitive incident-response data. Define encryption-at-rest, access-control, retention, backup, and secure-deletion requirements before deployment. Do not ship production data in installation media. |
| Generated reports | User-selected local path | JSON, Markdown, or text export of case data | Exports may contain sensitive data. Apply classification, approved-storage, and sharing controls. |
| Clipboard content | Local user clipboard | User-initiated report copy | Treat copied report contents as sensitive; document the operational handling expectation. |

## Security And Deployment Notes

- The active source scan found no HTTP client, socket, subprocess, browser,
  telemetry, analytics, or cloud-storage imports. Viper does not itself transmit
  case data over the network.
- SQLAlchemy opens a local SQLite file through `sqlite:///...`; the product has
  no server-side database dependency.
- Version pins exist for the three direct Python dependencies. The transitive
  versions above are an observed environment snapshot, not a checked-in lock
  file. Before release, generate and approve a fully resolved lock/SBOM from the
  build environment so repeatable builds use the same transitive versions.
- No project `LICENSE`, `NOTICE`, `pyproject.toml`, `setup.py`, or other
  application-level licensing file was found in this repository. Confirm the
  proprietary ownership/distribution classification of Viper source code and
  provide any required product license or third-party attribution bundle.
- The adjacent legacy `csim-app` workspace may have separate dependencies and
  licenses. It is deliberately excluded from this desktop-app BOM.

## Compliance Sign-Off Checklist

- [ ] Approve the licenses and notice obligations for every component in the
  third-party tables, especially Greenlet's dual license and tzdata's Apache-2.0
  obligations.
- [ ] Review the full license texts from the exact release artifacts used for
  the build; do not rely only on this metadata summary.
- [ ] Approve the Python, Tk/Tcl, SQLite, and Windows-font distribution model.
- [ ] Verify the ownership/license and permitted distribution of
  `ui/assets/PO_Rook.png`.
- [ ] Establish handling controls for the SQLite database, exported reports,
  and clipboard data.
- [ ] Produce a release-specific, fully resolved SBOM and vulnerability scan
  from the approved build environment.
- [ ] Confirm Viper's product licensing/proprietary classification and ship all
  required third-party attribution notices with any distributable package.