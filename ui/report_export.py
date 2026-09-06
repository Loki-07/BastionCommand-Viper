"""Report export — assembles a full case snapshot and renders it as JSON, Markdown, or
plain text, for saving to disk or copying into an AI assistant for report writing.

This is read-only: it never touches the database beyond a single query pass, and never
mutates any records.
"""

import json

from db import (
    AffectedSystem,
    AffectedUser,
    AfterActionReview,
    Case,
    CaseUpdate,
    CommunicationLogEntry,
    DueOut,
    IncidentPOC,
    IntelligenceReport,
    IOC,
    PIR,
    RootCauseAnalysis,
    RunningAssessment,
    TimelineEvent,
)


def _fmt_dt(value) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m-%d %H:%M")


def gather_case_report(session, case_id: int) -> dict:
    """Build a plain-dict snapshot of everything known about one case.

    Runs entirely inside the caller's session so relationships can be queried directly;
    the result contains only primitives (str/int/bool/None), safe to use after the
    session closes.
    """

    case = session.get(Case, case_id)
    if case is None:
        raise ValueError(f"No case found with id={case_id}")

    timeline_events = (
        session.query(TimelineEvent)
        .filter_by(case_id=case_id)
        .order_by(TimelineEvent.timestamp)
        .all()
    )
    affected_systems = session.query(AffectedSystem).filter_by(case_id=case_id).all()
    affected_users = session.query(AffectedUser).filter_by(case_id=case_id).all()
    iocs = session.query(IOC).filter_by(case_id=case_id).all()
    due_outs = session.query(DueOut).filter_by(case_id=case_id).all()
    rca = session.query(RootCauseAnalysis).filter_by(case_id=case_id).first()
    incident_pocs = session.query(IncidentPOC).filter_by(case_id=case_id).all()
    aar = session.query(AfterActionReview).filter_by(case_id=case_id).first()
    communication_logs = (
        session.query(CommunicationLogEntry)
        .filter_by(case_id=case_id)
        .order_by(CommunicationLogEntry.timestamp)
        .all()
    )
    pirs = session.query(PIR).filter_by(case_id=case_id).order_by(PIR.created_at).all()
    running_assessment = (
        session.query(RunningAssessment).filter_by(case_id=case_id).first()
    )
    intelligence_reports = (
        session.query(IntelligenceReport)
        .filter_by(case_id=case_id)
        .order_by(IntelligenceReport.created_at)
        .all()
    )
    case_updates = (
        session.query(CaseUpdate)
        .filter_by(case_id=case_id)
        .order_by(CaseUpdate.date.desc(), CaseUpdate.created_at.desc())
        .all()
    )

    return {
        "case": {
            "case_name": case.case_name,
            "status": case.status,
            "impact": case.impact,
            "urgency": case.urgency,
            "incident_number": case.incident_number,
            "incident_manager": case.incident_manager,
            "summary": case.summary,
            "description": case.description,
            "created_at": _fmt_dt(case.created_at),
        },
        "timeline_events": [
            {
                "timestamp": _fmt_dt(e.timestamp),
                "type": e.type,
                "description": e.description,
            }
            for e in timeline_events
        ],
        "affected_systems": [
            {
                "hostname": s.hostname,
                "ip_address": s.ip_address,
                "asset_type": s.asset_type,
                "status": s.status,
            }
            for s in affected_systems
        ],
        "affected_users": [
            {
                "name": u.name,
                "username": u.username,
                "email": u.email,
                "phone": u.phone,
                "chat_handle": u.chat_handle,
                "systems_affected": u.systems_affected,
                "notes": u.notes,
                "restricted_comm": u.restricted_comm,
            }
            for u in affected_users
        ],
        "iocs": [
            {
                "type": i.type,
                "value": i.value,
                "description": i.description,
                "source": i.source,
                "detection_date": _fmt_dt(i.detection_date),
                "notes": i.notes,
            }
            for i in iocs
        ],
        "due_outs": [
            {
                "task": d.task,
                "owner": d.owner,
                "priority": d.priority,
                "status": d.status,
                "due_date": d.due_date,
            }
            for d in due_outs
        ],
        "rca": (
            {
                "immediate_cause": rca.immediate_cause,
                "contributing_factors": rca.contributing_factors,
                "root_cause": rca.root_cause,
                "timeline_refs": rca.timeline_refs,
                "author": rca.author,
                "version": rca.version,
                "updated_at": _fmt_dt(rca.updated_at),
            }
            if rca is not None
            else None
        ),
        "incident_pocs": [
            {
                "name": p.name,
                "role": p.role,
                "status": p.status,
                "bu": p.bu,
                "email": p.email,
                "cell": p.cell,
                "tz": p.tz,
                "notes": p.notes,
            }
            for p in incident_pocs
        ],
        "aar": (
            {
                "review_date": aar.review_date,
                "participants": aar.participants,
                "who": aar.who,
                "what": aar.what,
                "where": aar.where,
                "when": aar.when,
                "why": aar.why,
                "questions_and_answers": aar.questions_and_answers,
                "comments": aar.comments,
                "improvement_notes": aar.improvement_notes,
                "rca_status": aar.rca_status,
                "timeline_summary": aar.timeline_summary,
                "ioc_count": aar.ioc_count,
                "affected_systems_count": aar.affected_systems_count,
                "affected_users_count": aar.affected_users_count,
                "case_duration": aar.case_duration,
                "author": aar.author,
                "version": aar.version,
                "updated_at": _fmt_dt(aar.updated_at),
            }
            if aar is not None
            else None
        ),
        "communication_logs": [
            {
                "timestamp": _fmt_dt(c.timestamp),
                "comm_type": c.comm_type,
                "summary": c.summary,
                "notes": c.notes,
            }
            for c in communication_logs
        ],
        "pirs": [
            {
                "question": p.question,
                "created_at": _fmt_dt(p.created_at),
            }
            for p in pirs
        ],
        "running_assessment": (
            {
                "content": running_assessment.content,
                "doi": _fmt_dt(running_assessment.doi),
            }
            if running_assessment is not None
            else None
        ),
        "intelligence_reports": [
            {
                "title": r.title,
                "description": r.description,
                "bluf": r.bluf,
                "source_url": r.source_url,
                "ioc_list": r.ioc_list,
                "has_iocs": r.has_iocs,
                "data_section": r.data_section,
                "analyst_comments": r.analyst_comments,
                "created_at": _fmt_dt(r.created_at),
            }
            for r in intelligence_reports
        ],
        "case_updates": [
            {"date": u.date, "summary": u.summary}
            for u in case_updates
        ],
    }


def format_as_json(data: dict) -> str:
    return json.dumps(data, indent=2)


def _md_table(headers: list[str], rows: list[list]) -> str:
    if not rows:
        return "_None recorded._\n"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        cells = [str(v).replace("\n", " ").replace("|", "\\|") if v not in (None, "") else "" for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def format_as_markdown(data: dict) -> str:
    c = data["case"]
    lines = [f"# Incident Report: {c['case_name']}", ""]
    lines.append(
        f"**Status:** {c['status']}  |  **Impact:** {c['impact']}/5  |  "
        f"**Urgency:** {c['urgency']}/5  |  **Created:** {c['created_at']}"
    )
    lines.append(
        f"**Incident Number:** {c['incident_number'] or '_None_'}  |  "
        f"**Incident Manager:** {c['incident_manager'] or '_None_'}"
    )
    lines.append("")
    lines.append("## Summary")
    lines.append(c["summary"] or "_None recorded._")
    lines.append("")
    lines.append("## Description")
    lines.append(c["description"] or "_None recorded._")
    lines.append("")

    lines.append("## Case Updates")
    lines.append(
        _md_table(
            ["Date", "Summary"],
            [[u["date"], u["summary"]] for u in data["case_updates"]],
        )
    )

    lines.append("## Timeline")
    lines.append(
        _md_table(
            ["Date/Time", "Type", "Description"],
            [[e["timestamp"], e["type"], e["description"]] for e in data["timeline_events"]],
        )
    )

    lines.append("## Affected Systems")
    lines.append(
        _md_table(
            ["Hostname", "IP Address", "Asset Type", "Status"],
            [
                [s["hostname"], s["ip_address"], s["asset_type"], s["status"]]
                for s in data["affected_systems"]
            ],
        )
    )

    lines.append("## Affected Users")
    lines.append(
        _md_table(
            ["Name", "Username", "Email", "Phone", "Systems Affected", "Restricted Comm"],
            [
                [
                    u["name"],
                    u["username"],
                    u["email"],
                    u["phone"],
                    u["systems_affected"],
                    "Yes" if u["restricted_comm"] else "No",
                ]
                for u in data["affected_users"]
            ],
        )
    )

    lines.append("## Indicators of Compromise (IOCs)")
    lines.append(
        _md_table(
            ["Type", "Value", "Source", "Detected", "Description"],
            [
                [i["type"], i["value"], i["source"], i["detection_date"], i["description"]]
                for i in data["iocs"]
            ],
        )
    )

    lines.append("## Due Outs")
    lines.append(
        _md_table(
            ["Task", "Owner", "Priority", "Status", "Due Date"],
            [
                [d["task"], d["owner"], d["priority"], d["status"], d["due_date"]]
                for d in data["due_outs"]
            ],
        )
    )

    lines.append("## Root Cause Analysis")
    rca = data["rca"]
    if rca is None:
        lines.append("_No RCA recorded for this case._")
    else:
        lines.append(f"**Immediate Cause:** {rca['immediate_cause'] or '_None_'}")
        lines.append("")
        lines.append(f"**Contributing Factors:** {rca['contributing_factors'] or '_None_'}")
        lines.append("")
        lines.append(f"**Root Cause:** {rca['root_cause'] or '_None_'}")
        lines.append("")
        lines.append(
            f"**Author:** {rca['author'] or '_Unknown_'}  |  **Version:** {rca['version']}  |  "
            f"**Last Updated:** {rca['updated_at']}"
        )
    lines.append("")

    lines.append("## Stakeholders")
    lines.append(
        _md_table(
            ["Name", "Role", "Status", "BU", "Email", "Cell", "TZ"],
            [
                [p["name"], p["role"], p["status"], p["bu"], p["email"], p["cell"], p["tz"]]
                for p in data["incident_pocs"]
            ],
        )
    )

    lines.append("## After Action Review")
    aar = data["aar"]
    if aar is None:
        lines.append("_No AAR recorded for this case._")
    else:
        lines.append(f"**Review Date:** {aar['review_date'] or '_None_'}")
        lines.append("")
        lines.append(f"**Participants:** {aar['participants'] or '_None_'}")
        lines.append("")
        for field in ("who", "what", "where", "when", "why"):
            lines.append(f"**{field.capitalize()}:** {aar[field] or '_None_'}")
            lines.append("")
        lines.append(f"**Lessons Learned (Q&A):** {aar['questions_and_answers'] or '_None_'}")
        lines.append("")
        lines.append(f"**Comments:** {aar['comments'] or '_None_'}")
        lines.append("")
        lines.append(f"**Improvement Notes:** {aar['improvement_notes'] or '_None_'}")
        lines.append("")
        lines.append(
            f"**Stats snapshot:** RCA status: {aar['rca_status']}  |  "
            f"IOCs: {aar['ioc_count']}  |  Affected Systems: {aar['affected_systems_count']}  |  "
            f"Affected Users: {aar['affected_users_count']}  |  Duration: {aar['case_duration']}"
        )
        lines.append("")
        lines.append(
            f"**Author:** {aar['author'] or '_Unknown_'}  |  **Version:** {aar['version']}  |  "
            f"**Last Updated:** {aar['updated_at']}"
        )
    lines.append("")

    lines.append("## Communication Log")
    comm_rows = []
    for entry in data["communication_logs"]:
        comm_rows.append([entry["timestamp"], entry["comm_type"], entry["summary"]])
        if entry["notes"]:
            comm_rows.append(["", "", f"↳ Notes: {entry['notes']}"])
    lines.append(_md_table(["Date/Time", "Type", "Summary"], comm_rows))

    lines.append("## CTI — Priority Information Requests (PIRs)")
    lines.append(
        _md_table(
            ["Created", "Question"],
            [[p["created_at"], p["question"]] for p in data["pirs"]],
        )
    )

    lines.append("## CTI — Running Assessment")
    ra = data["running_assessment"]
    if ra is None:
        lines.append("_No running assessment recorded for this case._")
    else:
        lines.append(ra["content"] or "_None recorded._")
        lines.append("")
        lines.append(f"**Date of Intelligence (DOI):** {ra['doi']}")
    lines.append("")

    lines.append("## CTI — Intelligence Reports")
    for report in data["intelligence_reports"]:
        lines.append(f"### {report['title']}")
        lines.append(
            f"**Created:** {report['created_at']}  |  **Has IOCs:** "
            f"{'Yes' if report['has_iocs'] else 'No'}  |  **Source:** {report['source_url'] or '_None_'}"
        )
        lines.append("")
        lines.append(f"**BLUF:** {report['bluf'] or '_None_'}")
        lines.append("")
        lines.append(f"**Description:** {report['description'] or '_None_'}")
        lines.append("")
        lines.append(f"**Data:** {report['data_section'] or '_None_'}")
        lines.append("")
        lines.append(f"**IOC List:** {report['ioc_list'] or '_None_'}")
        lines.append("")
        lines.append(f"**Analyst Comments:** {report['analyst_comments'] or '_None_'}")
        lines.append("")
    if not data["intelligence_reports"]:
        lines.append("_None recorded._")

    return "\n".join(lines) + "\n"


def _text_table(headers: list[str], rows: list[list]) -> str:
    if not rows:
        return "  (none recorded)\n"
    lines = []
    for row in rows:
        parts = []
        for header, value in zip(headers, row):
            if value in (None, ""):
                continue
            parts.append(f"{header}: {value}")
        lines.append("  - " + "; ".join(parts))
    return "\n".join(lines) + "\n"


def format_as_text(data: dict) -> str:
    c = data["case"]
    lines = [f"INCIDENT REPORT: {c['case_name']}", "=" * (17 + len(c["case_name"]))]
    lines.append(
        f"Status: {c['status']}   Impact: {c['impact']}/5   Urgency: {c['urgency']}/5   "
        f"Created: {c['created_at']}"
    )
    lines.append(
        f"Incident Number: {c['incident_number'] or '(none)'}   "
        f"Incident Manager: {c['incident_manager'] or '(none)'}"
    )
    lines.append("")
    lines.append("SUMMARY")
    lines.append("-------")
    lines.append(c["summary"] or "(none recorded)")
    lines.append("")
    lines.append("DESCRIPTION")
    lines.append("-----------")
    lines.append(c["description"] or "(none recorded)")
    lines.append("")

    lines.append("CASE UPDATES")
    lines.append("------------")
    lines.append(
        _text_table(
            ["Date", "Summary"],
            [[u["date"], u["summary"]] for u in data["case_updates"]],
        )
    )

    lines.append("TIMELINE")
    lines.append("--------")
    lines.append(
        _text_table(
            ["Date/Time", "Type", "Description"],
            [[e["timestamp"], e["type"], e["description"]] for e in data["timeline_events"]],
        )
    )

    lines.append("AFFECTED SYSTEMS")
    lines.append("----------------")
    lines.append(
        _text_table(
            ["Hostname", "IP", "Type", "Status"],
            [
                [s["hostname"], s["ip_address"], s["asset_type"], s["status"]]
                for s in data["affected_systems"]
            ],
        )
    )

    lines.append("AFFECTED USERS")
    lines.append("--------------")
    lines.append(
        _text_table(
            ["Name", "Username", "Email", "Phone", "Systems Affected", "Restricted Comm"],
            [
                [
                    u["name"],
                    u["username"],
                    u["email"],
                    u["phone"],
                    u["systems_affected"],
                    "Yes" if u["restricted_comm"] else "No",
                ]
                for u in data["affected_users"]
            ],
        )
    )

    lines.append("INDICATORS OF COMPROMISE (IOCs)")
    lines.append("--------------------------------")
    lines.append(
        _text_table(
            ["Type", "Value", "Source", "Detected", "Description"],
            [
                [i["type"], i["value"], i["source"], i["detection_date"], i["description"]]
                for i in data["iocs"]
            ],
        )
    )

    lines.append("DUE OUTS")
    lines.append("--------")
    lines.append(
        _text_table(
            ["Task", "Owner", "Priority", "Status", "Due Date"],
            [
                [d["task"], d["owner"], d["priority"], d["status"], d["due_date"]]
                for d in data["due_outs"]
            ],
        )
    )

    lines.append("ROOT CAUSE ANALYSIS")
    lines.append("-------------------")
    rca = data["rca"]
    if rca is None:
        lines.append("(no RCA recorded for this case)")
    else:
        lines.append(f"Immediate Cause: {rca['immediate_cause'] or '(none)'}")
        lines.append(f"Contributing Factors: {rca['contributing_factors'] or '(none)'}")
        lines.append(f"Root Cause: {rca['root_cause'] or '(none)'}")
        lines.append(
            f"Author: {rca['author'] or '(unknown)'}   Version: {rca['version']}   "
            f"Last Updated: {rca['updated_at']}"
        )
    lines.append("")

    lines.append("STAKEHOLDERS")
    lines.append("------------")
    lines.append(
        _text_table(
            ["Name", "Role", "Status", "BU", "Email", "Cell", "TZ"],
            [
                [p["name"], p["role"], p["status"], p["bu"], p["email"], p["cell"], p["tz"]]
                for p in data["incident_pocs"]
            ],
        )
    )

    lines.append("AFTER ACTION REVIEW")
    lines.append("-------------------")
    aar = data["aar"]
    if aar is None:
        lines.append("(no AAR recorded for this case)")
    else:
        lines.append(f"Review Date: {aar['review_date'] or '(none)'}")
        lines.append(f"Participants: {aar['participants'] or '(none)'}")
        for field in ("who", "what", "where", "when", "why"):
            lines.append(f"{field.capitalize()}: {aar[field] or '(none)'}")
        lines.append(f"Lessons Learned (Q&A): {aar['questions_and_answers'] or '(none)'}")
        lines.append(f"Comments: {aar['comments'] or '(none)'}")
        lines.append(f"Improvement Notes: {aar['improvement_notes'] or '(none)'}")
        lines.append(
            f"Stats snapshot: RCA status={aar['rca_status']}, IOCs={aar['ioc_count']}, "
            f"Affected Systems={aar['affected_systems_count']}, "
            f"Affected Users={aar['affected_users_count']}, Duration={aar['case_duration']}"
        )
        lines.append(
            f"Author: {aar['author'] or '(unknown)'}   Version: {aar['version']}   "
            f"Last Updated: {aar['updated_at']}"
        )
    lines.append("")

    lines.append("COMMUNICATION LOG")
    lines.append("-----------------")
    comm_rows = []
    for entry in data["communication_logs"]:
        comm_rows.append([entry["timestamp"], entry["comm_type"], entry["summary"]])
        if entry["notes"]:
            comm_rows.append([None, None, f"Notes: {entry['notes']}"])
    lines.append(_text_table(["Date/Time", "Type", "Summary"], comm_rows))

    lines.append("CTI - PRIORITY INFORMATION REQUESTS (PIRs)")
    lines.append("-------------------------------------------")
    lines.append(
        _text_table(
            ["Created", "Question"],
            [[p["created_at"], p["question"]] for p in data["pirs"]],
        )
    )

    lines.append("CTI - RUNNING ASSESSMENT")
    lines.append("------------------------")
    ra = data["running_assessment"]
    if ra is None:
        lines.append("(no running assessment recorded for this case)")
    else:
        lines.append(ra["content"] or "(none recorded)")
        lines.append(f"Date of Intelligence (DOI): {ra['doi']}")
    lines.append("")

    lines.append("CTI - INTELLIGENCE REPORTS")
    lines.append("--------------------------")
    if not data["intelligence_reports"]:
        lines.append("(none recorded)")
    for report in data["intelligence_reports"]:
        lines.append(f"* {report['title']}")
        lines.append(
            f"  Created: {report['created_at']}   Has IOCs: "
            f"{'Yes' if report['has_iocs'] else 'No'}   Source: {report['source_url'] or '(none)'}"
        )
        lines.append(f"  BLUF: {report['bluf'] or '(none)'}")
        lines.append(f"  Description: {report['description'] or '(none)'}")
        lines.append(f"  Data: {report['data_section'] or '(none)'}")
        lines.append(f"  IOC List: {report['ioc_list'] or '(none)'}")
        lines.append(f"  Analyst Comments: {report['analyst_comments'] or '(none)'}")

    return "\n".join(lines) + "\n"
