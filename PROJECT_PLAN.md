# Bastion Command (Viper) — Project Plan

**Type:** Pure-Python desktop rewrite of Bastion Command (CSIM)
**Stack:** Tkinter (stdlib) + ttkbootstrap ("darkly" theme) + SQLAlchemy 2.0 + SQLite
**Explicitly excluded:** Flask, REST API, Node.js/npm, React, any browser runtime
**Reference only (do not modify):** `csim-app` (legacy Flask+React app), opened side-by-side
via `bastion-project.code-workspace`

## Goals

- Recreate the core incident-management workflow as a single-process desktop app with
  zero server/browser/Node dependency, to simplify corporate compliance review.
- Preserve the domain model and field-level behavior of the legacy app where it's in
  MVP scope (see Phase 3 feature list and the deferred-features backlog in Phase 4).
- Ship in small, independently testable phases. Each phase below ends with a
  **Checkpoint** — stop, run/validate, and get sign-off before starting the next phase.

## Non-goals (for now)

- No multi-user authentication/login (single local user, no `User` model in MVP).
- No network access.
- No PDF/CSV export in the MVP (legacy used `reportlab`; revisit in Phase 4 backlog).

(Encryption-at-rest was a non-goal through Phase 8 — the legacy app's SQLCipher/Fernet
code was dead code, never wired into its live database connection. Revisited and
implemented in Phase 9 below, as pure-Python envelope encryption — not SQLCipher.)

---

## Phase 0 — Repo Scaffold ✅ DONE

**Objective:** Stand up a clean, standalone git repo so the rewrite has no inherited
history/deps from the legacy app.

**Deliverables:**
- `.gitignore`, `requirements.txt` (`SQLAlchemy`, `ttkbootstrap`)
- `main.py` smoke-test window
- Empty package stubs: `db/__init__.py`, `ui/__init__.py`, `ui/tabs/__init__.py`

**Checkpoint:** `python main.py` opens a themed window. — **Passed.**

---

## Phase 1 — Data Layer ✅ DONE

**Objective:** Define the MVP data model and local SQLite persistence, independent of
any UI.

**Deliverables:**
- [db/models.py](db/models.py) — SQLAlchemy 2.0 declarative models trimmed from legacy
  `backend/models.py`: `Case`, `TimelineEvent`, `AffectedSystem`, `AffectedUser`, `IOC`
  (with relationships/cascade deletes).
- [db/database.py](db/database.py) — `init_db()`, `get_session()` (commit/rollback
  context manager), `get_engine()`.
- [db/__init__.py](db/__init__.py) — public API surface for the package.
- [main.py](main.py) — calls `init_db()` on startup.

**Checkpoint (how to validate):**
```powershell
python -c "from db import init_db, get_session, Case; init_db('test_viper.db')
with get_session() as s:
    s.add(Case(case_name='Smoke Test'))
print('OK')"
Remove-Item test_viper.db
```
Confirms tables create and rows insert/commit without error. — **Passed** (verified with
pinned `requirements.txt` versions installed).

**Discussion point before Phase 2:** confirm the MVP model field list below is complete
enough, or trim/add fields now while it's cheap to change.

| Model | Key fields |
|---|---|
| `Case` | case_name, status, description, summary, impact (1-5), urgency (1-5), created_at |
| `TimelineEvent` | case_id, timestamp, description, type |
| `AffectedSystem` | case_id, hostname, ip_address, asset_type, status |
| `AffectedUser` | case_id, name, username, email, phone, chat_handle, systems_affected, notes, restricted_comm |
| `IOC` | case_id, type, value, description, affected_system_id, detection_date, source, notes, added_at |

---

## Phase 2 — UI Shell ✅ DONE

**Objective:** Build the app's navigational skeleton — no feature-tab content yet, just
the case list and the empty case-detail frame.

**Deliverables:**
- [ui/main_window.py](ui/main_window.py) — root frame: `ttk.Treeview` listing all `Case`
  rows (case_name, status, impact, urgency, created_at), sortable by clicking column
  headings; toolbar with New Case / Open Case / Delete Case / Refresh.
- [ui/new_case_dialog.py](ui/new_case_dialog.py) — modal "New Case" dialog (case_name,
  description, impact, urgency) → inserts a `Case` row and refreshes the list.
- [ui/case_detail_window.py](ui/case_detail_window.py) — opens on double-click (or
  "Open Case") of a case row, hosts a `ttk.Notebook` with placeholder tabs (Overview,
  Timeline, Affected Systems, Affected Users, IOCs) under [ui/tabs/](ui/tabs/), one
  module per tab — each currently just a label, ready for Phase 3 to fill in.
- Delete affordance (confirmation dialog) on the case list toolbar.
- [main.py](main.py) wires `init_db()` + `MainWindow` into the app window.

**Checkpoint (how to validate):**
- Automated smoke tests run (real Tkinter window, auto-closed after render):
  1. Launch app with a seeded `Case` row → `MainWindow` tree shows exactly 1 row. Passed.
  2. Open `CaseDetailWindow` for that case → window exists with Notebook tabs. Passed.
  3. Open `NewCaseDialog`, set a name, save → case list grows from 1 to 2 rows,
     confirming DB insert + refresh wiring. Passed.
- Manual follow-up recommended: run `python main.py`, create/delete a couple of cases by
  hand, restart the app, confirm persistence via the on-disk `bastion_command.db` file.

**Pause here to discuss:** tab order/naming, whether case list needs filtering/search
before Phase 3, and any visual/theme preferences. — *Resolved: proceeding as-is; can
revisit anytime since this is low-cost to change.*

---

## Phase 3 — Feature Tabs ✅ DONE

**Objective:** Implement full CRUD for each MVP feature tab, matching legacy field
layout/validation where practical.

**Deliverables:**
- [ui/tabs/list_form_tab.py](ui/tabs/list_form_tab.py) — shared base class (`ListFormTab`)
  used by the four list-style tabs: handles Treeview population, row selection → form,
  Add/Save/Delete/Clear wiring, case-scoped queries. Subclasses only define the form
  widgets and field mapping.
- [ui/tabs/overview.py](ui/tabs/overview.py) — edits `Case` fields directly (case_name,
  status dropdown, impact/urgency spinboxes, summary, description) with a Save button.
- [ui/tabs/timeline.py](ui/tabs/timeline.py) — `TimelineEvent` CRUD, sorted by timestamp,
  type dropdown (detection/containment/compromise/communication/recovery).
- [ui/tabs/affected_systems.py](ui/tabs/affected_systems.py) — `AffectedSystem` CRUD,
  asset_type + status dropdowns.
- [ui/tabs/affected_users.py](ui/tabs/affected_users.py) — `AffectedUser` CRUD, with a
  `restricted_comm` toggle that flags the row in red in the list (visual warning per
  legacy intent — "should NOT be contacted directly").
- [ui/tabs/iocs.py](ui/tabs/iocs.py) — `IOC` CRUD, type dropdown, optional link to one
  of the case's `AffectedSystem` rows via a dynamically-populated combobox.

**Checkpoint (how to validate):** automated end-to-end smoke test (real Tkinter
window, auto-closed after render) covering two cases:
- Edited Overview (name + status) on Case One → change persisted.
- Added 1 Timeline event, 1 additional Affected System (2 total incl. seeded row), 1
  restricted Affected User, 1 IOC linked to an Affected System → all persisted and
  independently re-queryable after the window closed.
- Confirmed **no cross-case leakage**: Case Two still shows 0 affected systems.
- IOC "Affected System" combobox correctly listed the case's own hostnames.
All assertions passed. Byte-compiled every `.py` file in the repo — no syntax errors.

**Pause here to discuss:** field-level validation rules from the legacy `app.py` routes
worth enforcing before calling MVP complete — currently only "required" fields are
validated (case_name, hostname, description, IOC value, timestamp/date formats); no
length limits, regex checks (e.g. IP/email format), or duplicate-hostname checks yet.

---

## Phase 4 — Polish & Backlog ✅ DONE

**Objective:** Confirm CRUD parity/usability, then decide what (if anything) from the
deferred list gets pulled into scope next.

**Deliverables:**
- [ui/constants.py](ui/constants.py) — centralized the dropdown value lists
  (`STATUS_OPTIONS`, `EVENT_TYPES`, `ASSET_TYPES`, `SYSTEM_STATUS_OPTIONS`, `IOC_TYPES`)
  that were previously duplicated across tab files, so they can't drift out of sync.
- Case list search/filter: a live text search on case name and a status dropdown filter
  in [ui/main_window.py](ui/main_window.py) ("sensible default sort/filter" from the plan).
- Keyboard shortcuts: `Delete` key removes the selected row (case list and every feature
  tab's list), `Return` opens the selected case or submits the New Case dialog, `Escape`
  closes the New Case dialog and the case-detail window.
- Error handling: every DB write (`Case`, and all 4 list-form tabs) is now wrapped so
  unexpected SQLAlchemy/DB errors surface as a friendly message box instead of an
  unhandled traceback; existing "required field"/format validation (case name, hostname,
  description, IOC value, timestamp/date formats) left as-is from Phase 3.
- Delete confirmation dialogs (already added in Phases 2-3) confirmed still in place for
  case deletion and every per-tab record deletion.

**Checkpoint (how to validate):** automated smoke tests (real Tkinter windows,
auto-closed after render):
- Search filter narrowed 3 seeded cases to the 2 matching "alpha"; status filter narrowed
  to the 1 "Closed" case; both cleared back to 3. Passed.
- `Delete` key on the case list tree removed the selected case (with confirm dialog
  mocked). Passed.
- `Delete` key on a feature tab (Affected Systems) removed the selected child record.
  Passed (note: the Notebook tab must be the active/selected tab for its widgets to
  receive focus/keyboard events — true for a real user who's clicked into the tab).
- `Escape` closed both the case-detail window and the New Case dialog. Passed.
- Byte-compiled every `.py` file in the repo — no syntax errors.

**CRUD parity confirmation:** all 5 MVP tabs (Overview, Timeline, Affected Systems,
Affected Users, IOCs) support create/read/update/delete, scoped correctly per case, per
the Phase 3 end-to-end test. Considered **MVP complete**.

**Deferred features (not in MVP)** — from legacy `backend/models.py` / `app.py`:
- Root Cause Analysis (RCA) + version history
- After Action Review (AAR) + version history
- Expert Finder (`PointOfContact` directory + org chart visualization)
- Case-specific stakeholders (`IncidentPOC`)
- Communication Log
- Audit Log
- Admin Panel / multi-user auth (`User` model, roles, lock/unlock)
- Evidence upload/download (chain-of-custody file tracking)
- Interviews (structured Q&A records)
- CTI: `PIR`, `RunningAssessment`, `IntelligenceReport`
- Due Outs (task tracking)
- PDF/CSV report export (`reportlab`)

**Pause here to discuss:** review the deferred-feature backlog above and prioritize what
(if anything) becomes "Phase 5" next — e.g. Due Outs and Audit Log are relatively small
and high-value; RCA/AAR and Expert Finder are larger; Admin Panel/multi-user auth is a
bigger architectural decision (this app is currently single-user by design).

---


## Phase 5: Deferred Features
- Root Cause Analysis (RCA) + version history ✅ DONE
- After Action Review (AAR) + version history ✅ DONE
- Case-specific stakeholders (`IncidentPOC`) ✅ DONE
- Due Outs (task tracking) ✅ DONE
- report export (`reportlab`) - May be in JSON, Markdown or Text document - this will be used for AI assisted writing of reports ✅ DONE (JSON/Markdown/Text — no `reportlab`/PDF, see writeup below)
- Communication Log ✅ DONE (scope reduced — see below)

**Due Outs — done:**
- [db/models.py](db/models.py) — `DueOut` model (case_id, task, owner, priority
  [Low/Medium/High/Critical], status [Pending/In Progress/Completed], due_date as a
  free-form/ISO `YYYY-MM-DD` string, created_at), cascade-deletes with its `Case`.
- [ui/constants.py](ui/constants.py) — `DUE_OUT_PRIORITIES`, `DUE_OUT_STATUSES`.
- [ui/tabs/due_outs.py](ui/tabs/due_outs.py) — `DueOutsTab(ListFormTab)`: list + form CRUD
  like the other feature tabs. Rows tagged red ("overdue") when `due_date` is in the past
  and status isn't Completed, and tagged gray ("completed") when status is Completed —
  matching the legacy `DueOuts.jsx` visual treatment (no version history needed here per
  user decision — Due Outs don't need diffable history, just current state).
- Wired into [ui/case_detail_window.py](ui/case_detail_window.py) as a new "Due Outs" tab.
- **Checkpoint (validated):** automated smoke test — added 3 tasks (overdue/pending,
  completed, future/pending), confirmed correct row tags for each, confirmed all 3
  persisted via direct DB query, deleted one via the shared `ListFormTab` delete flow
  (2 remain), confirmed a malformed due-date string raises a validation error before
  save. Full repo byte-compiled clean. **Passed.**

**Root Cause Analysis (RCA) — done:**
- [db/models.py](db/models.py) — `RootCauseAnalysis` (one row per case: immediate_cause,
  contributing_factors, root_cause, timeline_refs [comma-separated `TimelineEvent` IDs],
  author, version, created_at, updated_at) and `RCAHistoryEntry` (case_id, version,
  author, timestamp) — a **simple audit trail** per user decision (who/when edited each
  version), not a full content-snapshot history. Both cascade-delete with their `Case`.
- [ui/tabs/rca.py](ui/tabs/rca.py) — `RCATab`: single editable form (Overview-tab style,
  not list-based) with an "Author" field and a read-only "Edit History" Treeview below
  showing every past version's number/author/timestamp, newest first. Saving a new RCA
  creates version 1 + one history entry; every subsequent save increments `version` and
  appends a new history entry (no prior entries are ever modified).
- Wired into [ui/case_detail_window.py](ui/case_detail_window.py) as a new "RCA" tab.
- **Checkpoint (validated):** automated smoke test — confirmed "no RCA yet" empty state,
  first save created version 1 with 1 history entry, second save bumped to version 2
  with a 2nd history entry (1st entry unchanged), history Treeview showed both entries
  newest-first, status label reflected the current version, and deleting the parent
  `Case` cascade-deleted both the RCA row and all history entries. Full repo
  byte-compiled clean. **Passed.**

**Incident POCs (case-specific stakeholders) — done:**
- [db/models.py](db/models.py) — `IncidentPOC` (case_id, name, role, status
  [Employee/Contractor/Vendor/Consultant], bu [business unit], email, cell, tz, notes),
  cascade-deletes with its `Case`. Distinct from the deferred, Phase 6 global
  `PointOfContact` expert-finder directory — this links a specific person to one case.
- [ui/constants.py](ui/constants.py) — `POC_STATUS_OPTIONS`.
- [ui/tabs/incident_poc.py](ui/tabs/incident_poc.py) — `IncidentPOCsTab(ListFormTab)`:
  list + form CRUD like Affected Systems/Users/IOCs.
- Wired into [ui/case_detail_window.py](ui/case_detail_window.py) as a new
  "Stakeholders" tab.
- **Checkpoint (validated):** automated smoke test — added, edited, and deleted a
  stakeholder via the shared `ListFormTab` flow; confirmed no cross-case leakage (a
  second case showed 0 stakeholders); confirmed the required-name validation raises
  before save; confirmed cascade delete removes stakeholders when their `Case` is
  deleted. Full repo byte-compiled clean. **Passed.**

**After Action Review (AAR) — done:**
- [db/models.py](db/models.py) — `AfterActionReview` (one row per case: review_date,
  author, participants, who/what/where/when/why, questions_and_answers, comments,
  improvement_notes, plus auto-computed/snapshotted rca_status, timeline_summary,
  ioc_count, affected_systems_count, affected_users_count, case_duration, version,
  created_at, updated_at) and `AARHistoryEntry` (case_id, version, author, timestamp) —
  same **simple audit trail** pattern as RCA. Both cascade-delete with their `Case`.
  Simplified from the legacy model: participants and lessons-learned Q&A are free-form
  text rather than structured JSON/dynamic rows, since there's no Expert Finder or
  multi-user auth in this app yet.
- [ui/tabs/aar.py](ui/tabs/aar.py) — `AARTab`: single editable form (RCA-tab style) with
  a "5 W's" sub-section, a read-only "Auto-Computed Summary" panel that's recomputed
  from the case's current Timeline/IOC/Affected Systems/Affected Users/RCA data every
  time the tab loads or saves, and the same version + Edit History Treeview pattern as
  RCA.
- Wired into [ui/case_detail_window.py](ui/case_detail_window.py) as a new "AAR" tab.
- **Checkpoint (validated):** automated smoke test — seeded a case with 2 timeline
  events, 1 affected system, 1 affected user, 1 IOC, and an RCA; confirmed the
  pre-save "no AAR yet" summary already reflected the correct live counts; first save
  created version 1 + 1 history entry with correct snapshotted stats; added a 2nd
  affected system and saved again → version 2, stats updated to reflect the new count,
  2nd history entry added (1st unchanged); confirmed a malformed review-date string
  raises a validation error before save; confirmed cascade delete removes the AAR and
  all history entries when the parent `Case` is deleted. Full repo byte-compiled clean.
  **Passed.**
**Communication Log — done (scope reduced per user request):**
- Deliberately simplified from the legacy `CommunicationLog` model, which stored the
  actual message template/recipients/content. This version is a **quick-reference
  timeline of when communications happened and what type they were** — not the
  message content itself.
- [db/models.py](db/models.py) — `CommunicationLogEntry` (case_id, timestamp, comm_type,
  optional summary, optional notes), cascade-deletes with its `Case`.
- [ui/constants.py](ui/constants.py) — `COMMUNICATION_TYPES` = Vendor, SA Deconfliction,
  Final CAN, CAN, CCIR, CTM, Legal Request.
- [ui/tabs/communication_log.py](ui/tabs/communication_log.py) —
  `CommunicationLogTab(ListFormTab)`: list sorted chronologically (like Timeline),
  columns are Date/Time, Type, Summary only — Notes is form-only, so the list reads as
  a scannable timeline and a row is "opened" (selected) to see full notes for quick
  reference.
- Wired into [ui/case_detail_window.py](ui/case_detail_window.py) as a new "Comm Log" tab.
- **Checkpoint (validated):** automated smoke test — added 3 entries out of
  chronological order, confirmed the list re-sorts to correct date/time order;
  confirmed notes are populated in the form on row selection; confirmed no cross-case
  leakage; confirmed a malformed timestamp raises a validation error before save;
  deleted one entry via the shared `ListFormTab` flow (2 remain); confirmed cascade
  delete removes entries when the parent `Case` is deleted. Full repo byte-compiled
  clean. **Passed.**

**Report Export — done (JSON/Markdown/Text, not `reportlab`/PDF):**
- The plan bullet mentioned `reportlab`, but the actual requirement ("May be in JSON,
  Markdown or Text document") doesn't need a PDF library, and the Non-goals section
  already deferred PDF/CSV export. Implemented as plain-text formats only — no new
  dependency added to [requirements.txt](requirements.txt).
- [ui/report_export.py](ui/report_export.py) — `gather_case_report()` assembles a
  full plain-dict snapshot of one case (overview, timeline, affected systems/users,
  IOCs, due outs, RCA, stakeholders, AAR, communication log) inside a single session
  pass (read-only, never mutates data). `format_as_json()`, `format_as_markdown()`,
  `format_as_text()` render that dict into each output format.
- [ui/tabs/report_export_tab.py](ui/tabs/report_export_tab.py) — `ReportExportTab`:
  a format dropdown (Markdown/JSON/Text), a live read-only preview pane, and
  "Refresh Preview" / "Copy to Clipboard" / "Save to File..." buttons. Intended for
  quickly handing a case off to an AI assistant for report writing, per the plan's
  stated purpose.
- Wired into [ui/case_detail_window.py](ui/case_detail_window.py) as the final "Export"
  tab.
- **Checkpoint (validated):** automated smoke test — data layer: JSON output
  round-trips through `json.loads` with correct nested values for every section;
  Markdown/Text output verified to contain case fields, table rows, and
  notes-append-on-communication-log-entries; a case with no RCA/AAR/child records
  renders "none recorded" placeholders without error; a nonexistent case id raises
  `ValueError`. Widget layer: preview auto-populates on tab load, refreshes correctly
  across all 3 formats, save-to-file writes the exact previewed content to disk
  (mocked file dialog), copy-to-clipboard puts the exact previewed content on the
  clipboard, and the preview `Text` widget is confirmed read-only (`state=disabled`).
  Full repo byte-compiled clean. **Passed.**

**Phase 5 is now fully complete** — all six sub-features (Due Outs, RCA, Incident
POCs, AAR, Communication Log, Report Export) are done and smoke-tested.

## Phase 6: Deferred Features
- CTI: `PIR`, `RunningAssessment`, `IntelligenceReport` ✅ DONE
- Expert Finder (`PointOfContact` directory + org chart visualization) ✅ DONE (directory
  CRUD + search done; org chart visualization deferred — see writeup below)
- Interviews (structured Q&A records) ⏸️ DEFERRED — now handled by a different team,
  out of scope for this app
- Admin Panel for Customization - Colors, Layout, Etc ⏸️ DEFERRED
- Time Zone Converter ✅ DONE

**CTI — done:**
- Case-scoped Cyber Threat Intelligence tab, grouping three sub-features into one
  nested Notebook (`CTITab`) inside the case-detail window: Priority Information
  Requests (PIRs), a Running Assessment, and Intelligence Reports.
- [db/models.py](db/models.py) — `PIR` (case_id, question, created_at) — a simple,
  ordered list of intel questions being tracked for the case; `RunningAssessment`
  (case_id, unique — one per case, content, doi [Date of Intelligence] with
  `onupdate=utcnow`, so it auto-refreshes on every save, matching the legacy model's
  freshness-timestamp behavior and deliberately carrying no version history, unlike
  RCA/AAR); `IntelligenceReport` (case_id, title, source_url, bluf, description,
  data_section, ioc_list, has_iocs, analyst_comments, created_at) — a list of finished
  intel products (e.g. "Threat Actor TTPs Analysis").
- [ui/tabs/pir.py](ui/tabs/pir.py) — `PIRTab(ListFormTab)`: single required "Question"
  text field, list ordered by `created_at`.
- [ui/tabs/running_assessment.py](ui/tabs/running_assessment.py) —
  `RunningAssessmentTab`: single get-or-create record per case (same pattern as
  Overview/RCA/AAR, not a `ListFormTab`), one large content field, a status label
  showing the current DOI timestamp (or an empty-state message before the first
  save).
- [ui/tabs/intelligence_report.py](ui/tabs/intelligence_report.py) —
  `IntelligenceReportTab(ListFormTab)`: required Title, Source URL, BLUF, Description,
  Data Section, IOC List, a "Has IOCs" checkbox, and Analyst Comments; long text
  fields are form-only (excluded from the list columns), matching the Comm Log
  precedent.
- [ui/tabs/cti.py](ui/tabs/cti.py) — `CTITab`: a `ttk.Frame` hosting a nested
  `ttk.Notebook` with the three sub-tabs above ("PIRs", "Running Assessment", "Intel
  Reports").
- Wired into [ui/case_detail_window.py](ui/case_detail_window.py) as a new "CTI" tab,
  positioned after Comm Log and before Export.
- [ui/report_export.py](ui/report_export.py) — extended `gather_case_report()` and
  all three formatters (JSON/Markdown/Text) to include PIRs, the running assessment,
  and intelligence reports, keeping the export a true full-case snapshot.
- **Checkpoint (validated):** automated smoke test — added two PIRs and confirmed
  list ordering/count; confirmed empty-question validation raises before save;
  confirmed PIR delete works; confirmed the Running Assessment tab shows the correct
  empty-state message before any save, and that saving both creates the record and
  updates the DOI-timestamp status label, with a second save (content changed)
  persisting the new content; confirmed adding an Intelligence Report with "Has
  IOCs" checked lists correctly with "Yes" in the tree and confirmed empty-title
  validation raises; confirmed a second, unrelated case's CTI tab starts with zero
  PIRs/reports (no cross-case leakage); confirmed `gather_case_report()` and all
  three export formats (JSON/Markdown/Text) correctly include the new PIR/Running
  Assessment/Intelligence Report data; confirmed cascade-delete of the parent `Case`
  removes all `PIR`/`RunningAssessment`/`IntelligenceReport` rows. Full repo
  byte-compiled clean. **Passed.**

**Time Zone Converter — done:**
- Standalone utility (independent of any case), opened from the main window's
  toolbar, for converting a source date/time in one IANA time zone to several target
  zones at once — to help schedule calls with stakeholders/experts across regions
  (the `tz` field on both `IncidentPOC` and `PointOfContact` is free-form text, so this
  converter is a separate, precise IANA-zone-based tool rather than parsing those
  fields).
- Added `tzdata==2026.3` to [requirements.txt](requirements.txt) — required because
  Windows has no built-in IANA time zone database; Python's stdlib `zoneinfo` module
  needs the `tzdata` package to resolve zone names on Windows (confirmed
  `zoneinfo.available_timezones()` returns 0 zones without it, 598 with it).
- [ui/timezone_converter_window.py](ui/timezone_converter_window.py) —
  `TimezoneConverterWindow`: source date/time/zone entry (with a "Now" button), a
  searchable time zone combobox (type-to-filter across all ~598 IANA zones), a target
  zone list seeded with 6 common defaults (UTC, US zones, London) that can be added to
  or removed from, and a results Treeview showing each target zone's local time, UTC
  offset, and same/next/previous-day label relative to the source date.
- Wired into [ui/main_window.py](ui/main_window.py) as a new "Time Zone Converter"
  toolbar button.
- **Checkpoint (validated):** automated smoke test — confirmed default target zones
  populate on open; confirmed DST-aware conversion accuracy for both a summer date
  (EDT/CDT/MDT/PDT/BST all UTC-4/-5/-6/-7/+1) and a winter date (EST/GMT at
  UTC-5/+0); confirmed a late-night UTC source correctly rolls Tokyo to "+1 day";
  confirmed adding a duplicate zone doesn't create a duplicate row; confirmed adding
  an unrecognized zone name shows an error and isn't added; confirmed an unparseable
  date/time shows an error without crashing; confirmed removing a selected zone drops
  it from both the list and the results; confirmed the type-to-filter combobox helper
  narrows correctly; confirmed a second independently-opened window has its own
  default state. Full repo byte-compiled clean. **Passed.**

**Expert Finder — done:**
- Global, case-independent directory of experts/resources, built up over time from
  past cases so a specific expert can be found again later — opened from the main
  window's toolbar, not from any case-detail window.
- [db/models.py](db/models.py) — `PointOfContact` (name, role, email, phone, cell, tz,
  team [comma-separated], technology_sme [comma-separated], vendor_employee
  ["Employee"/"Vendor"], vendor_company, system_owner, specialization, notes,
  created_at). No `case_id`/FK — deliberately independent of the `Case` lifecycle
  (never cascade-deleted). Distinct from `IncidentPOC`, which links a person to one
  specific case.
- [ui/constants.py](ui/constants.py) — `VENDOR_EMPLOYEE_OPTIONS`.
- [ui/expert_finder_window.py](ui/expert_finder_window.py) — `ExpertFinderWindow`: a
  standalone `Toplevel` (list + form CRUD, same interaction pattern as the case-scoped
  `ListFormTab` tabs, but not a subclass since it has no `case_id`) with a search box
  that filters across name/role/team/technology_sme/vendor_company/system_owner
  (case-insensitive substring, including fields not shown as tree columns).
- Wired into [ui/main_window.py](ui/main_window.py) as a new "Expert Finder" toolbar
  button, opening the directory independent of any case selection.
- Org chart visualization (mentioned in the original backlog bullet) is deferred — not
  needed for the core "find an expert again" use case; can revisit later if wanted.
- **Checkpoint (validated):** automated smoke test — added an employee and a vendor
  expert via the form; confirmed both list correctly; confirmed search matches on a
  field not shown in the tree (`system_owner`) as well as a specialization field;
  confirmed clearing the search restores all rows; confirmed selecting a row loads
  every field (including ones not shown in the tree) into the form; confirmed editing
  and re-saving persists the change; confirmed empty-name validation raises before
  save; confirmed deleting the unrelated `Case` used to seed the test does **not**
  affect the expert directory (no FK relationship); confirmed a second
  `ExpertFinderWindow` instance shows the same shared global data; confirmed delete via
  the shared flow removes exactly the targeted record. Full repo byte-compiled clean.
  **Passed.**

## Phase 7: Graphical Enhancements
- Bring the graphical colors closer to the original via the design language guide in the legacy program ✅ DONE
- Timeline into a color coded graphical lay out (If not feesible in current design may be a new pop out option) ✅ DONE
- Color Code Due Outs section ✅ DONE
- Minor Updates: ✅ DONE
    - Add Incidemtn Manager to Overview Tab ✅ DONE
    - Add Incident Numebr to Overiew Tab ✅ DONE
    - Add section below description for updates organized by Date and summary of update ✅ DONE
    - Dates have option to select from a calander ✅ DONE

**Color Coded Timeline & Due Outs — done:**
- [ui/constants.py](ui/constants.py) — added `TIMELINE_TYPE_COLORS` (detection/
  containment/compromise/communication/recovery mapped to the exact hex values from
  the legacy `Timeline.jsx` `TYPE_COLORS` object) and `DUE_OUT_PRIORITY_COLORS`
  (Critical/High/Medium/Low mapped to the legacy `DueOuts.jsx` `getPriorityColor`
  values — Critical/High get distinct red/orange, Medium and Low share the same blue,
  matching the legacy behavior exactly).
- [ui/tabs/timeline.py](ui/tabs/timeline.py) — `TimelineTab` now tag-configures one
  Treeview foreground color per event type and overrides `refresh()` to tag each row
  by its `type`, so the timeline reads as an at-a-glance color-coded list (matching
  the legacy timeline's colored dot/timestamp per event type) without needing a
  separate graphical/pop-out view.
- [ui/tabs/due_outs.py](ui/tabs/due_outs.py) — `DueOutsTab` extended: rows already
  tagged `overdue` (red) or `completed` (gray) now fall back to a new
  priority-based tag (`priority_Critical/High/Medium/Low`) when neither of those
  applies, so every row is colored by something meaningful — urgency/completion
  first, priority otherwise.
- **Checkpoint (validated):** automated smoke test — added 3 timeline events of
  different types and confirmed each row gets the correct `type_*` tag with the
  correct configured foreground color; added 5 due-outs covering overdue,
  completed, and non-overdue/non-completed at each priority level, and confirmed
  each row receives exactly the expected tag (`overdue`/`completed`/
  `priority_Critical`/`priority_High`/`priority_Medium`) with the correct configured
  color, with overdue/completed correctly taking precedence over priority coloring.
  Full repo byte-compiled clean. **Passed.**

**Minor Updates — done:**
- [db/models.py](db/models.py) — `Case` gained `incident_number` and
  `incident_manager` text columns, plus a new `CaseUpdate` model (`date` string,
  `summary` text, `created_at`) with a `case.case_updates` relationship
  (cascade all, delete-orphan) — a deliberately simplified version of the legacy
  `OverviewUpdate` model (no author/versioning/`is_latest` tracking, matching the
  same simplification already applied to Communication Log).
- [ui/widgets.py](ui/widgets.py) — new `date_entry()` helper: wraps
  `ttkbootstrap.DateEntry` and rebinds its internal entry to a caller-supplied
  `tk.StringVar`, giving any date-only field (`YYYY-MM-DD`) a calendar-popup
  picker as a drop-in replacement for a plain `ttk.Entry`, with zero changes to
  surrounding form read/load/reset logic.
- [ui/tabs/due_outs.py](ui/tabs/due_outs.py), [ui/tabs/aar.py](ui/tabs/aar.py),
  [ui/tabs/iocs.py](ui/tabs/iocs.py) — Due Date / Review Date / Detection Date
  fields upgraded to `date_entry()` calendar pickers (full-datetime fields like
  Timeline and Comm Log timestamps were intentionally left as-is since
  `DateEntry` has no time-of-day component).
- [ui/tabs/case_updates.py](ui/tabs/case_updates.py) — new `CaseUpdatesTab`
  (`ListFormTab` subclass) with a date-picker date field and a multi-line summary
  field, newest-first ordering, and a truncated (80-char) preview in the list view
  with the full text shown when editing.
- [ui/tabs/overview.py](ui/tabs/overview.py) — added Incident Number and Incident
  Manager fields next to Status/Impact/Urgency; embeds a `CaseUpdatesTab` instance
  directly below the Description field (same embedded-widget pattern first used by
  CTI's nested sub-tabs), giving the dated update log a home without a new
  top-level notebook tab.
- [ui/report_export.py](ui/report_export.py) — report snapshot/JSON/Markdown/text
  exports extended to include Incident Number, Incident Manager, and the full
  Case Updates list.
- **Checkpoint (validated):** automated smoke test — opened a real (withdrawn)
  `CaseDetailWindow`, set and saved Incident Number/Incident Manager on the
  Overview tab and confirmed persistence via a fresh `OverviewTab` reload; added
  two Case Updates with different dates via the embedded `CaseUpdatesTab` and
  confirmed newest-first ordering, correct truncated ("…") preview for a long
  summary vs. the untruncated short one, and `ValueError` raised for empty
  date/summary; confirmed the `date_entry()` widget's bound `StringVar` updates
  the visible entry text; confirmed `gather_case_report`/`format_as_json`/
  `format_as_markdown`/`format_as_text` all include the new fields and update log;
  confirmed deleting the `Case` cascade-deletes its `CaseUpdate` rows. Full repo
  byte-compiled clean. **Passed.**

**Title Banner + Legacy Color Theme — done:**
- [ui/assets/PO_Rook.png](ui/assets/PO_Rook.png) — rook graphic (moved here from
  the repo root); used as both the app window/taskbar icon (`iconphoto`) and the
  banner icon.
- [ui/widgets.py](ui/widgets.py) — new `build_app_header()` renders a banner (rook
  icon + **"Bastion Command: Viper"** title, optional subtitle) shown at the top
  of the main dashboard window and every case-detail window, mirroring the
  legacy web app's persistent page header. Title font resolves at runtime to the
  first available of `Bahnschrift` / `Impact` / `Arial Black` (Bahnschrift ships
  with Windows 10/11 and has a condensed, military/government signage look).
- [ui/theme.py](ui/theme.py) (NEW) — registers a custom ttkbootstrap theme
  (`"bastion"`) whose color roles are mapped directly to
  `csim-app/DESIGN_LANGUAGE_GUIDE.md`'s documented hex values, so every widget
  styled via built-in bootstyle roles (default buttons, `success`/`info`/
  `warning`/`danger` variants, inputs, tabs, focus rings, Treeviews, etc.)
  automatically matches the legacy web app's palette without editing every tab
  file individually: `bg`=#0a0a0a (page bg), `dark`=#1a1a1a (panels/cards),
  `border`/`inputbg` accents=#333333, `primary`/`success`=#00ff00 (the guide uses
  green for every primary action button, checkbox/radio accent, and input focus
  ring), `info`=#00d4ff (links/important data text, kept distinct from the green
  action color), `warning`=#ffbb33, `danger`=#ff4444, `active` (hover)=#222222.
  **Important gotcha:** the theme must be registered/switched via
  `apply_bastion_theme(window)` called on the already-constructed
  `ttkbootstrap.Window` (which is created first with a built-in placeholder
  theme like `"darkly"`) — calling `Style()` standalone *before* any `Window`
  exists causes tkinter to silently create a separate hidden default Tk root,
  which then breaks `iconphoto()` (`TclError: not a photo image`) and other
  resources tied to the real window. Registering/switching on the real window's
  own `Style` instance avoids this.
- [main.py](main.py) — constructs the window with `themename="darkly"`, then
  calls `apply_bastion_theme(app)` immediately after, before setting the window
  icon or building `MainWindow`.
- **Checkpoint (validated):** automated smoke test — confirmed the `"bastion"`
  theme registers and activates (`style.theme.name == "bastion"`), confirmed
  `style.colors.primary`/`bg`/`success`/`info` match the design-guide hex values,
  opened `MainWindow` and every tab of a real `CaseDetailWindow` under the new
  theme with no errors. Full repo byte-compiled clean; app launched manually via
  `python main.py` with no traceback. **Passed.**

Phase 7 is now fully complete — no remaining items.

## Phase 8: Claude Cowork Import Add-On 🟡 SCOPED

**Objective:** Add an optional, human-reviewed import workflow for structured
findings produced by an authorized Claude Cowork Skill from Working Group Teams
chats, Outlook email, and CAN reports.

**Confirmed constraints:**
- Cowork access to the user's Teams and Outlook information is authorized.
- CAN reports normally arrive by email with an identifiable subject/title.
- The workflow may update existing cases only; it must never create a case.
- A draft must match an existing `Case.incident_number` using the `INC-XXX`
  convention; missing, non-matching, or ambiguous identifiers are rejected.
- Every proposed database change requires a human reviewer to approve, edit, or
  reject it before persistence.

**Proposed initial scope:**
- A versioned JSON draft contract generated by the Cowork Skill, containing source
  metadata, a target incident number, structured proposals, evidence excerpts, and
  confidence labels.
- Viper-side validation, exact incident-number matching, review/edit/reject UI,
  duplicate warnings, transactional application of approved proposals, and a local
  import audit trail.
- Initial record types: Timeline events, Communication Log entries, and Due Outs.
- Initial source: analyst-selected Outlook/CAN email exports. Add Teams chat analysis
  only after the review workflow and extraction quality are validated.

**Non-goals:**
- No direct, unreviewed Cowork writes to `bastion_command.db`.
- No Claude, Microsoft, or network credentials stored in Viper.
- No automatic creation of cases based on an email subject or extracted incident number.

**Detailed design:** [CLAUDE_COWORK_INTEGRATION.md](CLAUDE_COWORK_INTEGRATION.md).

**Database selection — done:**
- [ui/database_selection_dialog.py](ui/database_selection_dialog.py) presents a
  startup GUI dialog before Viper initializes SQLAlchemy. Users can choose an
  existing SQLite database, provide a file path directly, or select a new `.db`
  location to create.
- [main.py](main.py) initializes the database only after selection; canceling the
  dialog exits without opening a database. Invalid paths and initialization failures
  are shown as user-facing errors.
- The default startup suggestion remains `bastion_command.db`, but its location is
  no longer fixed to the application working directory.
- Successfully opened database locations are saved locally as recent choices. The
  startup dialog offers them in a dropdown and lets the user mark or remove a path as
  a favorite; only local file paths are stored in the preference file.

**Design decisions — resolved:** all four blocking decisions from
[CLAUDE_COWORK_INTEGRATION.md](CLAUDE_COWORK_INTEGRATION.md) are now settled —
CAN subject rule (must contain `CAN` + an `INC-\d+` pattern), draft handoff (a
`cowork_imports/{incoming,approved,rejected}/` folder colocated with the active
database, derived from the already-tracked DB path, no separate config), retention
(30-day age-based auto-cleanup of `approved/`/`rejected/`, configurable; `incoming/`
never auto-purged), and duplicate policy (warn only in the review UI, reviewer
always decides, never auto-block/merge).

**Implementation — done (initial pilot: Timeline / Communication Log / Due Out only,
email-sourced drafts only):**
- [services/import_drafts.py](services/import_drafts.py) — the whole local pipeline,
  no Claude/Microsoft/network dependency: `get_cowork_import_paths()`/
  `ensure_cowork_import_paths()` (colocated `cowork_imports/{incoming,approved,
  rejected}/`, derived from `get_active_db_path()`); `validate_draft()` (schema
  version, `INC-\d+` incident number, required `source` fields, per-proposal-kind
  required/optional/enum field checks, rejects unknown fields); `scan_incoming_drafts()`;
  `find_case_by_incident_number()` (exact match only); `detect_duplicate()` (best-effort
  timestamp+type/task matching, warn-only, never blocks); `apply_proposal()` (creates
  exactly one `TimelineEvent`/`CommunicationLogEntry`/`DueOut` row per approved
  proposal); `finalize_draft()` (appends a reviewer/timestamp/decisions audit record,
  moves the whole file to `approved/` or `rejected/`, never deletes at review time);
  `get_retention_days()`/`set_retention_days()`/`purge_expired_drafts()` (30-day
  default, same local-JSON-prefs pattern as `ui/database_locations.py`).
- [ui/tabs/cowork_import.py](ui/tabs/cowork_import.py) — `CoworkImportTab`: a regular
  Notebook tab (not a separate Toplevel, to match every other feature in this app),
  wired into [ui/case_detail_window.py](ui/case_detail_window.py) as the final
  "Cowork Import" tab. Requires the case to already have an Incident Number set
  (Overview tab) before it will scan. Lists pending drafts matching the case's
  incident number; selecting one lists its proposals with a duplicate-hint flag;
  Approve Selected / Reject Selected (multi-select) / Edit Selected (a small generic
  field-editor dialog) / Finalize Draft (applies every approved proposal in one
  transaction, warns about any still-undecided proposals before treating them as
  rejected, then archives the file).
- [integrations/claude-cowork/](integrations/claude-cowork/) — the deployable Skill
  package: `SKILL.md` (the actual Claude Cowork Skill — trigger conditions, hard
  rules including prompt-injection defense and "never create a case", step-by-step
  drafting process, output contract, file-naming convention), `README.md` (how the
  pieces fit together + manual schema-validation instructions), `schema/
  viper-import-draft-v1.json` (JSON Schema draft-07), `examples/can-email-draft.json`.
  A Teams-chat example was intentionally omitted since this pilot's `source.kind` is
  `"email"` only.
- **Checkpoint (validated):** automated smoke test — CAN-subject detection regex
  (positive/negative); folder auto-creation next to a fresh test database;
  `validate_draft()` accepted a fully-valid draft with zero errors and correctly
  flagged 3 distinct errors on a deliberately broken one (bad incident number, missing
  source fields, unsupported proposal kind); `scan_incoming_drafts()` found 1 valid +
  1 invalid file without crashing; exact incident-number case matching confirmed
  (hit and miss); opened a real `CaseDetailWindow`, selected the "Cowork Import" tab,
  confirmed it loaded the 1 matching draft with its 3 proposals; approved 2 proposals
  (communication_log, due_out) and rejected 1 (timeline) via the real Treeview
  selection + button handlers; finalized the draft and confirmed **only** the 2
  approved rows were actually written to the database (the rejected timeline
  proposal was not applied); confirmed the original file was removed from
  `incoming/` and an equivalent file appeared in `approved/` with an appended
  `review` block recording the exact per-proposal decisions; confirmed a tab refresh
  no longer lists the now-processed draft as pending. Full repo byte-compiled clean.

## Phase 9: Database Encryption at Rest ✅ DONE (pilot)

**Objective:** Let a single user optionally encrypt their Viper database file at rest,
without reintroducing the legacy app's "designed but never wired in" encryption
anti-pattern, and without adding a compiled/native dependency (which was evaluated —
SQLCipher — and explicitly ruled out; see repo memory for the full trade-off research).

**Approach chosen:** pure-Python whole-file envelope encryption, built entirely on the
`cryptography` package (Fernet + PBKDF2-HMAC-SHA256, 600,000 iterations). The database
file on disk is one opaque encrypted container; while the app is running, a decrypted
"working copy" exists at a stable, non-guessable path under
`%LOCALAPPDATA%/BastionCommand/Viper/decrypted_cache/` (keyed by a hash of the
encrypted file's path) so a leftover copy from an unclean shutdown can be recovered.
Passphrase is prompted once per launch and never persisted anywhere (per explicit user
decision) — held in memory only for the session, needed to re-encrypt on close.

**New files:**
- `security/envelope.py` — container format (magic bytes + salt + KDF iterations +
  Fernet token), `encrypt_bytes`/`decrypt_bytes`/`encrypt_file`/`decrypt_file`,
  `is_encrypted_container()`, `InvalidPassphraseError`.
- `security/encrypted_database.py` — working-copy lifecycle: `create_encrypted_database()`
  (new DB), `open_encrypted_database()` (decrypt-or-recover, returns `(path, recovered)`),
  `encrypt_snapshot()`, `close_encrypted_database()` (re-encrypt + best-effort shred +
  delete working copy), `EncryptionSession` dataclass + module-level
  active-session getter/setter/`finalize_active_session()`.
- `ui/passphrase_dialog.py` — `prompt_new_passphrase()` (set+confirm, ≥8 chars, for new
  encrypted DBs) and `prompt_unlock_passphrase()` (for existing ones, with a retry/
  "incorrect passphrase" message).

**Changed files:**
- `db/database.py`/`db/__init__.py` — added `close_db()` (disposes the engine; must run
  before re-encrypting so SQLite has no open connections/locks on the working copy).
- `main.py` — `_resolve_db_path_for_session()` branches on whether the selected path
  exists/is a container: new file → ask to encrypt (yes → set+confirm passphrase,
  no → plain legacy behavior unchanged); existing encrypted container → prompt passphrase
  in a retry loop; existing non-container file → opened as-is (full backward
  compatibility with every pre-Phase-9 database). `WM_DELETE_WINDOW` now calls
  `close_db()` + `finalize_active_session()` before destroying the window; if
  re-encryption fails, the window stays open (and the working copy is left intact) so
  the user can retry rather than silently losing data.
- `requirements.txt` — added `cryptography>=42`.

**Known trade-offs (documented, not hidden):** this protects the file at rest when the
app is closed, but a plaintext working copy exists on disk while the app runs (weaker
than SQLCipher's page-level in-use encryption, which was evaluated and rejected — see
repo memory for why: official Windows builds are Enterprise-only, and the free
community-edition Windows build path isn't officially documented). OS-level disk
encryption (BitLocker) remains the recommended defense-in-depth baseline underneath
this. Not yet implemented: changing/rotating a passphrase on an existing database, and
migrating an existing plain database to encrypted in place (both straightforward
follow-ups on top of the same `security/envelope.py` primitives if needed later).

**Checkpoint validation:** two temporary smoke-test scripts (written, run, then
deleted) covered: envelope encrypt/decrypt round trip + wrong-passphrase rejection;
new-encrypted-database creation + initial snapshot; clean close (re-encrypt + shred
working copy); reopen-and-decrypt with data surviving the round trip; wrong passphrase
rejected on reopen without leaking a working copy; crash recovery (leftover working
copy reused, still gated by a correct-passphrase check against the master file) with a
second case added "pre-crash" confirmed present after recovery; and `main.py`'s
`_resolve_db_path_for_session()` exercised directly (via a real Tkinter root, with
`messagebox.askyesno`/passphrase-dialog functions monkeypatched) across all four paths:
new+encrypt, new+plain, existing-encrypted-correct-passphrase, existing-legacy-plain.

## Status Summary

| Phase | Status |
|---|---|
| 0 — Repo Scaffold | ✅ Done |
| 1 — Data Layer | ✅ Done |
| 2 — UI Shell | ✅ Done |
| 3 — Feature Tabs | ✅ Done |
| 4 — Polish & Backlog | ✅ Done (MVP complete) |
| 5 — RCA/AAR, Stakeholders, Due Outs, Report Export, Comm Log | ✅ Done |
| 6 — CTI, Expert Finder, Interviews, Admin Customization, Time Zone Converter | ✅ Done (Interviews and Admin Customization deferred — handled by a different team / descoped) |
| 7 — Graphical Enhancements (design language, timeline visualization) | ✅ Done |
| 8 — Claude Cowork Import Add-On | 🟡 In progress (design resolved, pilot implementation done — Timeline/Comm Log/Due Out, email-sourced drafts only) |
| 9 — Database Encryption at Rest | ✅ Done (pilot — pure-Python envelope encryption; passphrase rotation/migrate-existing-DB not yet built) |
