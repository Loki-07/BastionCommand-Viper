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
