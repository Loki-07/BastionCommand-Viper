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
- No network access, no encryption-at-rest module (legacy encryption code was dead code
  anyway — see prior compliance review).
- No PDF/CSV export in the MVP (legacy used `reportlab`; revisit in Phase 4 backlog).

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

## Phase 2 — UI Shell (not started)

**Objective:** Build the app's navigational skeleton — no feature-tab content yet, just
the case list and the empty case-detail frame.

**Deliverables:**
- Root window: `ttk.Treeview` listing all `Case` rows (case_name, status, impact,
  urgency, created_at), sortable by column.
- "New Case" dialog: minimal form (case_name, description, impact, urgency) → inserts a
  `Case` row and refreshes the list.
- Case-detail window/frame: opens on double-click of a case row, hosts a `ttk.Notebook`
  with placeholder tabs (Overview, Timeline, Affected Systems, Affected Users, IOCs) —
  each tab initially just shows a label, no data yet.
- Basic delete/edit-status affordance on the case list (right-click menu or buttons).

**Checkpoint (how to validate):**
- Launch app → create 2-3 test cases → confirm they persist across app restart (reopen
  and see them in the list, backed by the SQLite file).
- Open a case → confirm the Notebook tab bar renders with all 5 placeholder tabs.
- No feature logic yet — this phase is purely "can I navigate the shell."

**Pause here to discuss:** tab order/naming, whether case list needs filtering/search
before Phase 3, and any visual/theme preferences.

---

## Phase 3 — Feature Tabs (depends on Phase 2)

**Objective:** Implement full CRUD for each MVP feature tab, matching legacy field
layout/validation where practical. Tabs can be built in any order; suggested order below
follows legacy tab prominence.

| Tab | Reference (legacy) | Deliverable |
|---|---|---|
| Overview | `App.jsx` case header + `OverviewUpdate` fields | Edit case_name/status/description/summary/impact/urgency in place |
| Timeline | `Timeline`-related component, `TimelineEvent` model | Treeview of events + add/edit/delete form (timestamp, description, type) |
| Affected Systems | `AffectedSystems.jsx` | Treeview + add/edit/delete form (hostname, ip_address, asset_type, status) |
| Affected Users | `AffectedUsers.jsx` | Treeview + add/edit/delete form, honoring `restricted_comm` flag (e.g. visual warning) |
| IOCs | IOC-related component | Treeview + add/edit/delete form, optional link to an `AffectedSystem` |

**Checkpoint (how to validate, per tab):** create/edit/delete a record in the tab, verify
it persists (restart app, confirm still there), verify it's scoped to the correct case
(no cross-case leakage).

**Overall Phase 3 checkpoint:** a full run-through — create a case, populate all 5 tabs,
close and reopen the app, confirm full data integrity. This is the MVP "done" milestone.

**Pause here to discuss:** any field-level validation rules from the legacy `app.py`
routes worth enforcing (e.g. required fields, dropdown value lists) before calling MVP
complete.

---

## Phase 4 — Polish & Backlog (depends on Phase 3)

**Objective:** Confirm CRUD parity/usability, then decide what (if anything) from the
deferred list gets pulled into scope next.

**Deliverables:**
- Usability pass: keyboard shortcuts, confirmation dialogs on delete, sensible default
  sort/filter on case list, error handling/user-facing messages for bad input.
- Written backlog (this document, updated) of deferred features with a recommendation
  per item (build later / drop / revisit if compliance allows).

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

**Checkpoint:** review this backlog together, prioritize next increment (could become
"Phase 5", "Phase 6", etc. as separate planned phases once decided).

---

## Status Summary

| Phase | Status |
|---|---|
| 0 — Repo Scaffold | ✅ Done |
| 1 — Data Layer | ✅ Done |
| 2 — UI Shell | ⏳ Not started |
| 3 — Feature Tabs | ⏳ Not started |
| 4 — Polish & Backlog | ⏳ Not started |
