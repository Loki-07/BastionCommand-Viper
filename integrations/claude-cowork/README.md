# Claude Cowork Import Add-On — Skill Package

This folder is the deployable unit for the Viper Cowork import pipeline described in
[`CLAUDE_COWORK_INTEGRATION.md`](../../CLAUDE_COWORK_INTEGRATION.md) at the repo root.
Copy (or point Claude Cowork at) this `claude-cowork/` folder on whatever machine the
analyst runs Cowork from — typically their work laptop, alongside their Outlook/Teams
access and the Viper database file itself.

## What's here

```text
claude-cowork/
  SKILL.md                         <- the Skill itself (load this into Claude Cowork)
  README.md                        <- this file
  schema/
    viper-import-draft-v1.json     <- JSON Schema the Skill's output must satisfy
  examples/
    can-email-draft.json           <- a worked example of a valid draft
```

## How it fits together

1. The analyst runs Claude Cowork with this Skill loaded, pointed at an authorized
   Outlook mailbox (initial pilot: email only — no Teams ingestion yet).
2. The Skill identifies a CAN report email (subject contains `CAN` and an `INC-#`
   pattern — see `SKILL.md`), or the analyst explicitly selects an email.
3. The Skill writes one draft JSON file (schema above) into
   `<folder containing the active Viper .db file>/cowork_imports/incoming/`.
4. In Viper, the analyst opens the case matching that `incident_number` and reviews
   the draft in the **Cowork Import** tab: approve, edit, or reject each proposal
   individually. Nothing is written to the database until that happens.
5. Viper moves the whole draft file into `cowork_imports/approved/` or
   `cowork_imports/rejected/` next to it, with a reviewer/timestamp/decision record
   appended — this is the local audit trail. Processed drafts are auto-purged after
   30 days by default (configurable); files still in `incoming/` are never purged.

## Non-goals

- The Skill never writes directly to `bastion_command.db` (or any `.db` file) — only
  to the `incoming/` drafts folder.
- The Skill never creates a new Viper case — a draft with a missing, non-matching, or
  ambiguous `incident_number` is rejected by Viper, not resolved by guessing.
- No Claude, Microsoft, or network credentials are stored by Viper itself; all
  authorized access (Teams/Outlook) is handled entirely within Claude Cowork.

## Validating a draft by hand

The schema is a standard JSON Schema (draft-07) file, so it can be checked with any
compatible validator, e.g.:

```powershell
pip install jsonschema
python -c "import json, jsonschema; jsonschema.validate(json.load(open('examples/can-email-draft.json')), json.load(open('schema/viper-import-draft-v1.json')))"
```

Viper also performs its own validation when scanning `incoming/` (see
`services/import_drafts.py`), independent of this schema file, so the schema here is
primarily documentation/tooling support for whoever authors or debugs drafts.
