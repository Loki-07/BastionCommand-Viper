"""
Database Models (Viper MVP)
============================

SQLAlchemy 2.0 declarative models for the desktop rewrite of Bastion Command.
Trimmed to MVP scope from the legacy Flask app's `backend/models.py`:

    IncidentCase, TimelineEvent, AffectedSystem, AffectedUser, IOC

No authentication/User model in the MVP — this is a single-user local desktop app.
Deferred (not implemented yet): RCA, AAR, Expert Finder, Communication Log, Audit Log,
Admin Panel, Evidence upload, Interviews, CTI/PIR, DueOuts, PDF export.
"""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Case(Base):
    """A single incident from start to finish."""

    __tablename__ = "case"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(default="Detection")  # Detection, Containment,
    # Communication, Recovery, Closed
    description: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, default="No summary provided yet.")
    impact: Mapped[int] = mapped_column(default=1)  # 1-5
    urgency: Mapped[int] = mapped_column(default=1)  # 1-5
    incident_number: Mapped[str | None] = mapped_column(Text)  # external incident/ticket ID
    incident_manager: Mapped[str | None] = mapped_column(Text)  # name of the incident manager
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    timeline_events: Mapped[list["TimelineEvent"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    affected_systems: Mapped[list["AffectedSystem"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    affected_users: Mapped[list["AffectedUser"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    iocs: Mapped[list["IOC"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    due_outs: Mapped[list["DueOut"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    rca: Mapped["RootCauseAnalysis | None"] = relationship(
        back_populates="case", cascade="all, delete-orphan", uselist=False
    )
    rca_history: Mapped[list["RCAHistoryEntry"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    incident_pocs: Mapped[list["IncidentPOC"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    aar: Mapped["AfterActionReview | None"] = relationship(
        back_populates="case", cascade="all, delete-orphan", uselist=False
    )
    aar_history: Mapped[list["AARHistoryEntry"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    communication_logs: Mapped[list["CommunicationLogEntry"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    pirs: Mapped[list["PIR"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    running_assessment: Mapped["RunningAssessment | None"] = relationship(
        back_populates="case", cascade="all, delete-orphan", uselist=False
    )
    intelligence_reports: Mapped[list["IntelligenceReport"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    case_updates: Mapped[list["CaseUpdate"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )


class CaseUpdate(Base):
    """A dated narrative update logged against a case's Overview — a running log of
    status updates distinct from the Timeline (which tracks discrete incident events),
    the RCA/AAR (post-analysis), and the CTI RunningAssessment (intel-focused).
    """

    __tablename__ = "case_update"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), nullable=False)
    date: Mapped[str] = mapped_column(nullable=False)  # YYYY-MM-DD
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    case: Mapped["Case"] = relationship(back_populates="case_updates")


class TimelineEvent(Base):
    """Chronological event within an incident."""

    __tablename__ = "timeline_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(default=utcnow)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(default="detection")  # detection, containment,
    # compromise, communication, recovery

    case: Mapped["Case"] = relationship(back_populates="timeline_events")


class AffectedSystem(Base):
    """A compromised or potentially affected system."""

    __tablename__ = "affected_system"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), nullable=False)
    hostname: Mapped[str] = mapped_column(nullable=False)
    ip_address: Mapped[str | None] = mapped_column()
    asset_type: Mapped[str] = mapped_column(default="Workstation")  # Server, Workstation,
    # Network Device, Database, etc.
    status: Mapped[str] = mapped_column(default="Investigating")  # Investigating,
    # Compromised, Patched, Quarantined, Recovered, Clean

    case: Mapped["Case"] = relationship(back_populates="affected_systems")
    iocs: Mapped[list["IOC"]] = relationship(back_populates="affected_system")


class AffectedUser(Base):
    """An end user impacted by the incident."""

    __tablename__ = "affected_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    username: Mapped[str | None] = mapped_column()
    email: Mapped[str | None] = mapped_column()
    phone: Mapped[str | None] = mapped_column()
    chat_handle: Mapped[str | None] = mapped_column()
    systems_affected: Mapped[str | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    restricted_comm: Mapped[bool] = mapped_column(default=False)

    case: Mapped["Case"] = relationship(back_populates="affected_users")


class IOC(Base):
    """Indicator of Compromise discovered during investigation."""

    __tablename__ = "ioc"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), nullable=False)
    type: Mapped[str] = mapped_column(nullable=False)  # IP, Hash, Domain, Email, Phone,
    # Hashtag, Other
    value: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    affected_system_id: Mapped[int | None] = mapped_column(ForeignKey("affected_system.id"))
    detection_date: Mapped[datetime | None] = mapped_column()
    source: Mapped[str | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    added_at: Mapped[datetime] = mapped_column(default=utcnow)

    case: Mapped["Case"] = relationship(back_populates="iocs")
    affected_system: Mapped["AffectedSystem | None"] = relationship(back_populates="iocs")


class DueOut(Base):
    """An outstanding investigation task/action item tracked against a case."""

    __tablename__ = "due_out"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), nullable=False)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str | None] = mapped_column()
    priority: Mapped[str] = mapped_column(default="Medium")  # Low, Medium, High, Critical
    status: Mapped[str] = mapped_column(default="Pending")  # Pending, In Progress, Completed
    due_date: Mapped[str | None] = mapped_column()  # free-form/ISO date string, e.g. YYYY-MM-DD
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    case: Mapped["Case"] = relationship(back_populates="due_outs")


class RootCauseAnalysis(Base):
    """Post-incident root cause determination — one record per case, editable in place.

    Version history is a simple audit trail (see `RCAHistoryEntry`): each save records
    who/when, not a full content snapshot.
    """

    __tablename__ = "root_cause_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), unique=True, nullable=False)
    immediate_cause: Mapped[str | None] = mapped_column(Text)
    contributing_factors: Mapped[str | None] = mapped_column(Text)
    root_cause: Mapped[str | None] = mapped_column(Text)
    timeline_refs: Mapped[str | None] = mapped_column()  # comma-separated TimelineEvent IDs
    author: Mapped[str | None] = mapped_column()
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    case: Mapped["Case"] = relationship(back_populates="rca")


class RCAHistoryEntry(Base):
    """Audit-trail entry: records that the case's RCA was edited, by whom, and when.

    Deliberately does NOT store a content snapshot — just who/when per edit.
    """

    __tablename__ = "rca_history_entry"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), nullable=False)
    version: Mapped[int] = mapped_column()
    author: Mapped[str | None] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column(default=utcnow)

    case: Mapped["Case"] = relationship(back_populates="rca_history")


class IncidentPOC(Base):
    """A case-specific stakeholder/point-of-contact (escalation, notifications, etc.).

    Distinct from the (deferred, Phase 6) global `PointOfContact` expert-finder
    directory — this links a specific person to one incident case.
    """

    __tablename__ = "incident_poc"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str | None] = mapped_column()
    status: Mapped[str | None] = mapped_column()  # Employee, Contractor, Vendor, Consultant
    bu: Mapped[str | None] = mapped_column()  # Business Unit
    email: Mapped[str | None] = mapped_column()
    cell: Mapped[str | None] = mapped_column()
    tz: Mapped[str | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)

    case: Mapped["Case"] = relationship(back_populates="incident_pocs")


class AfterActionReview(Base):
    """Post-incident team retrospective — one record per case, editable in place.

    Trimmed from the legacy model: participants and the lessons-learned Q&A are kept
    as free-form text (not structured JSON/dynamic rows) since there's no Expert Finder
    or multi-user auth in this app yet. The summary stats (timeline/IOC/affected
    counts, case duration, RCA status) are recomputed and snapshotted every time the
    AAR is saved. Version history is a simple audit trail (see `AARHistoryEntry`),
    matching the RCA pattern — who/when per version, not a full content snapshot.
    """

    __tablename__ = "after_action_review"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), unique=True, nullable=False)
    review_date: Mapped[str | None] = mapped_column()  # free-form/ISO YYYY-MM-DD string
    participants: Mapped[str | None] = mapped_column(Text)  # free-form, one per line
    who: Mapped[str | None] = mapped_column(Text)
    what: Mapped[str | None] = mapped_column(Text)
    where: Mapped[str | None] = mapped_column(Text)
    when: Mapped[str | None] = mapped_column(Text)
    why: Mapped[str | None] = mapped_column(Text)
    questions_and_answers: Mapped[str | None] = mapped_column(Text)  # free-form lessons learned
    comments: Mapped[str | None] = mapped_column(Text)
    improvement_notes: Mapped[str | None] = mapped_column(Text)
    # Auto-computed/snapshotted at save time:
    rca_status: Mapped[str | None] = mapped_column()
    timeline_summary: Mapped[str | None] = mapped_column()
    ioc_count: Mapped[int | None] = mapped_column()
    affected_systems_count: Mapped[int | None] = mapped_column()
    affected_users_count: Mapped[int | None] = mapped_column()
    case_duration: Mapped[str | None] = mapped_column()
    author: Mapped[str | None] = mapped_column()
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    case: Mapped["Case"] = relationship(back_populates="aar")


class AARHistoryEntry(Base):
    """Audit-trail entry: records that the case's AAR was edited, by whom, and when.

    Deliberately does NOT store a content snapshot — just who/when per edit (same
    pattern as `RCAHistoryEntry`).
    """

    __tablename__ = "aar_history_entry"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), nullable=False)
    version: Mapped[int] = mapped_column()
    author: Mapped[str | None] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column(default=utcnow)

    case: Mapped["Case"] = relationship(back_populates="aar_history")


class CommunicationLogEntry(Base):
    """A single logged communication event (not the message content itself) — a
    quick-reference timeline of when/what-type/why, per the user's simplified scope
    (deliberately trimmed from the legacy `CommunicationLog` model, which stored the
    actual communication template/recipients/content)."""

    __tablename__ = "communication_log_entry"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(default=utcnow)
    comm_type: Mapped[str] = mapped_column(default="Vendor")  # Vendor, SA Deconfliction,
    # Final CAN, CAN, CCIR, CTM, Legal Request
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    case: Mapped["Case"] = relationship(back_populates="communication_logs")

class PointOfContact(Base):
    """Global expert/resource directory (Expert Finder) — independent of any one case.

    Distinct from `IncidentPOC`, which links a specific person to one incident case.
    This is a standing reference built up over time so a past expert can be found
    again for a future case (searchable by name/role/team/technology/specialization).
    """

    __tablename__ = "point_of_contact"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str | None] = mapped_column()
    email: Mapped[str | None] = mapped_column()
    phone: Mapped[str | None] = mapped_column()
    cell: Mapped[str | None] = mapped_column()
    tz: Mapped[str | None] = mapped_column()
    team: Mapped[str | None] = mapped_column()  # comma-separated, e.g. "SOC,Forensics"
    technology_sme: Mapped[str | None] = mapped_column()  # comma-separated, e.g. "AWS,Azure"
    vendor_employee: Mapped[str | None] = mapped_column()  # "Employee" or "Vendor"
    vendor_company: Mapped[str | None] = mapped_column()  # company name, if a vendor
    system_owner: Mapped[str | None] = mapped_column()  # systems/infra this person owns
    specialization: Mapped[str | None] = mapped_column()  # e.g. "Cloud Incident Response"
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class PIR(Base):
    """Priority Information Request — an intelligence question that needs answering,
    used to drive CTI collection activities during an investigation."""

    __tablename__ = "pir"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    case: Mapped["Case"] = relationship(back_populates="pirs")


class RunningAssessment(Base):
    """Evolving threat picture during an investigation — one editable record per case,
    similar to RCA/AAR but without a version-history audit trail (matches the legacy
    model, which only tracks a single "Date of Intelligence" freshness timestamp).
    """

    __tablename__ = "running_assessment"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), unique=True, nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    doi: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)  # Date of Intelligence

    case: Mapped["Case"] = relationship(back_populates="running_assessment")


class IntelligenceReport(Base):
    """A finished intelligence product documenting findings during an investigation
    (e.g. "Threat Actor TTPs Analysis")."""

    __tablename__ = "intelligence_report"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id"), nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    bluf: Mapped[str | None] = mapped_column(Text)  # Bottom Line Up Front
    source_url: Mapped[str | None] = mapped_column()
    ioc_list: Mapped[str | None] = mapped_column(Text)  # IOCs mentioned in this report
    has_iocs: Mapped[bool] = mapped_column(default=False)
    data_section: Mapped[str | None] = mapped_column(Text)  # detailed findings/analysis
    analyst_comments: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    case: Mapped["Case"] = relationship(back_populates="intelligence_reports")