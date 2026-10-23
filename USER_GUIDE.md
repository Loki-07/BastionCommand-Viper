# Bastion Command: Viper — User Guide

Viper is a local desktop application for managing security incident cases. It runs
entirely on your own machine — no server, no internet connection, no account to sign
into. Everything you enter is stored in a single SQLite database file that you choose
the location of.

This guide has two parts:
1. [Quick Start](#quick-start) — get the app running for the first time.
2. [How to Use the System](#how-to-use-the-system) — a tour of every screen and feature.

---

## Quick Start

### 1. Install Python dependencies

Viper needs Python 3.12 and a handful of packages listed in
[requirements.txt](requirements.txt). From the project folder, run:

```powershell
pip install -r requirements.txt
```

If you ever see `ModuleNotFoundError` when launching the app, this is the fix — re-run
the command above (it's safe to run again; it won't duplicate anything already
installed).

### 2. Launch the app

```powershell
python main.py
```

### 3. Choose or create a database

The first window you see is **Select Viper Database**. You have two options:

- **Open Existing...** — browse to a `.db` file you've used before.
- **Create New...** — pick a name and folder for a brand-new database (this is what
  you'll do the very first time you run Viper).

There's also a **Saved locations** dropdown that remembers databases you've opened
before, and a **Save this location as a favorite** checkbox so it's easy to find again
next time.

### 4. (Optional) Encrypt your new database

If you created a brand-new database, Viper will ask:

> **Encrypt this new database at rest with a passphrase?**

- Choose **Yes** if you want the database file encrypted when the app isn't running
  (recommended for laptops, shared drives, or anywhere the file could be copied off the
  machine). You'll be asked to set and confirm a passphrase.
- Choose **No** to use a plain, unencrypted database — this matches how every earlier
  version of Viper worked, and is the simplest option if encryption isn't a concern for
  your environment.

**Important:** if you encrypt a database, write your passphrase down somewhere safe.
Viper never stores it anywhere — if you lose it, the database cannot be recovered. See
[Database Encryption](#database-encryption) below for the full details.

### 5. Create your first case

Once the main window opens, click **New Case**, give it a name, and click **Save**.
Double-click the case in the list (or select it and click **Open Case**) to start
filling in details across the tabs described below.

That's it — you're up and running.

---

## How to Use the System

### The Main Window

The main window shows every case in your database as a list, with a toolbar above it:

| Button | What it does |
| --- | --- |
| **New Case** | Opens a form to create a case (name, description, impact, urgency). |
| **Open Case** | Opens the selected case's detail window. Double-clicking a row, or pressing Enter, does the same thing. |
| **Delete Case** | Deletes the selected case and everything attached to it (timeline, affected systems, etc.) after a confirmation prompt. Pressing Delete on a selected row does the same. |
| **Expert Finder** | Opens a standing directory of subject-matter experts/contacts, independent of any one case — see below. |
| **Time Zone Converter** | Opens a tool for converting a date/time across multiple time zones — handy for coordinating with distributed teams. |
| **Refresh** | Reloads the case list from the database. |

Above the list, a **Search** box filters cases by name as you type, and a **Status**
dropdown filters by case status (Detection/Containment/Communication/Recovery/Closed).
Click any column heading to sort by that column.

### Case Detail Tabs

Opening a case shows a window with a row of tabs. Each tab manages one part of the
case record:

| Tab | Purpose |
| --- | --- |
| **Overview** | The case's core fields: name, status, priority/impact, urgency, incident number, incident manager, description, and a running log of dated case updates. |
| **Timeline** | Chronological events (detection, containment, compromise, communication, recovery), color-coded by type. |
| **Affected Systems** | Hosts/systems involved, with status tracking (Investigating → Compromised → Patched/Quarantined → Recovered/Clean). |
| **Affected Users** | People impacted, with a flag for restricted communications. |
| **IOCs** | Indicators of compromise (IPs, hashes, domains, etc.), optionally linked to an affected system. |
| **Due Outs** | Action items/tasks with owner, priority, status, and due date — overdue items are highlighted. |
| **RCA** | Root cause analysis (immediate cause, contributing factors, root cause), with a simple version history of who edited it and when. |
| **Stakeholders** | People to notify/escalate to for this specific case (distinct from Expert Finder's general directory). |
| **AAR** | After-action review (what/when/where/why, lessons learned), with the same simple version history as RCA. |
| **Comm Log** | A quick-reference log of communications sent (vendor notices, CAN, CCIR, etc.) — date/type/summary, with full notes available per entry. |
| **CTI** | Three sub-tabs: Priority Intelligence Requirements (PIR), a single running assessment narrative, and finished intelligence reports. |
| **Export** | Generates a full report of the case (every tab's data) as Markdown, JSON, or plain text — preview it, copy it to the clipboard, or save it to a file. |
| **Cowork Import** | Reviews draft updates proposed by the Claude Cowork integration (see [CLAUDE_COWORK_INTEGRATION.md](CLAUDE_COWORK_INTEGRATION.md)) — approve or reject timeline/comm-log/due-out suggestions before they're added to the case. Requires the case's Incident Number to be set on the Overview tab first. |

### Expert Finder

A standalone directory (opened from the main window toolbar) of people you may want
to find again later — SMEs, vendor contacts, system owners — independent of any
specific case. Search matches across name, role, team, technology, vendor, and system
owner fields.

### Time Zone Converter

A standalone utility (opened from the main window toolbar) for converting one
date/time into several time zones at once, with daylight-saving-aware offsets and a
"same day / +1 day / -1 day" indicator for each target zone.

### Database Encryption

Viper can optionally encrypt your database file at rest using a passphrase you choose.
This is pure-Python encryption (no extra software to install) — here's what to expect:

- **Setting it up:** only offered when creating a brand-new database. You set a
  passphrase (at least 8 characters) and confirm it.
- **Opening it later:** when you select an encrypted database, Viper asks for the
  passphrase before it will open. Entering the wrong passphrase shows an error and
  lets you try again.
- **While the app is open:** Viper works with a temporary, decrypted copy of the
  database. This copy lives in a private folder under your Windows user profile and
  isn't something you'd normally see or need to touch.
- **Closing the app:** when you close the window normally, Viper re-encrypts the
  database and removes the temporary copy. If re-encryption fails for some reason
  (e.g., disk full), Viper keeps the window open and shows an error rather than
  risking data loss — nothing is deleted until the re-encryption succeeds.
- **If Viper closes unexpectedly** (crash, power loss): the next time you open that
  same database, Viper detects the leftover temporary copy and picks up right where
  you left off, after re-confirming your passphrase.
- **There is no "forgot passphrase" recovery.** The passphrase is never stored
  anywhere, by design. If it's lost, the database cannot be decrypted.
- **Existing (unencrypted) databases keep working exactly as before** — Viper only
  asks about encryption for brand-new databases, and opens any pre-existing `.db` file
  without prompts.

### Switching Databases

Viper only works with one database at a time. To switch, close the app and reopen it —
the **Select Viper Database** screen appears again every time you launch, with your
saved/recent locations available for quick access.

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `ModuleNotFoundError` when running `python main.py` | Run `pip install -r requirements.txt`, then try again. |
| "Incorrect passphrase" when opening an encrypted database | Double-check for typos (passphrases are case-sensitive). There is no recovery if the passphrase is genuinely lost. |
| Database won't open / "could not be opened" error | Confirm the file path exists and isn't open in another program; try picking it again via **Open Existing...**. |
| Cowork Import tab shows an instructional message instead of drafts | Set the case's **Incident Number** on the Overview tab first — it's required to match incoming drafts to the right case. |
