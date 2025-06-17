from __future__ import annotations
from typing import Optional,TYPE_CHECKING

if TYPE_CHECKING:  # only used for type hinting so no circular import issues
    from lookup_tables import PauseReasons
    from .model_category import Category, Subcategory
    from model_change import Change
    from model_cmdb import CmdbConfigurationItem
    from model_notes import Notes
    from model_problem import Problem
    from model_user import Team, User

from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from . import db
from .model_notes import CommsJournal  # Import CommsJournal for update_comms_journal method

class Ticket(db.Model):
    __tablename__ = 'ticket'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    ticket_number: Mapped[int] = mapped_column(
        db.Integer,
        sa.Identity(start=1000, increment=1),  # Auto-incrementing identity column
        unique=True,
        nullable=False
    )

    closed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    last_updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    outage_start: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    outage_end: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    outage_duration_total: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    outage_duration_sla: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(db.String(2), nullable=True)
    priority_impact: Mapped[Optional[str]] = mapped_column(db.String(8), nullable=True)
    priority_urgency: Mapped[Optional[str]] = mapped_column(db.String(8), nullable=True)
    priority_user_set: Mapped[Optional[str]] = mapped_column(db.String(8), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    resolution_code_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    resolution_journal: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)  # history of resolution changes
    resolution_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    short_desc: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    sla_paused_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    sla_pause_journal: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    sla_respond_by: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    sla_responded_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    sla_resolve_by: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    sla_resumed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(db.String(15), nullable=True)
    ticket_type: Mapped[Optional[str]] = mapped_column(db.String(15), nullable=True)

    # relationships
    category_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('category.id'))
    category: Mapped['Category'] = relationship(
        'Category',
        back_populates='ticket_category'
    )

    change_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('change.id', ondelete='SET NULL'), nullable=True)
    change: Mapped['Change'] = relationship(
        'Change',
        back_populates='child_ticket'
    )

    children: Mapped[list['Ticket']] = relationship(
        'Ticket',
        back_populates='parent',
    )

    cmdb_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('cmdb_configuration_item.id'), nullable=True)
    cmdb: Mapped['CmdbConfigurationItem'] = relationship(
        'CmdbConfigurationItem',
        back_populates='tickets'
    )

    comms_journal: Mapped['CommsJournal'] = relationship(
        'CommsJournal',
        back_populates='ticket',
        cascade='all, delete-orphan'
    )

    created_by_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by: Mapped['User'] = relationship(
        'User',
        foreign_keys='Ticket.created_by_id',
        back_populates='tickets_created',
    )

    notes: Mapped[list['Notes']] = relationship(
        'Notes',
        back_populates='ticket',
        cascade='all, delete-orphan, delete',
    )

    pause_history: Mapped[list["TicketPauseHistory"]] = relationship(
        "TicketPauseHistory",
        back_populates="ticket",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    parent_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('ticket.id', ondelete='SET NULL'), nullable=True
    )
    parent: Mapped[Optional['Ticket']] = relationship(
        'Ticket',
        remote_side=[id],
        foreign_keys=[parent_id],
        uselist=False,
        passive_deletes=False,
        back_populates='children'
    )

    problem_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('problem.id', ondelete='SET NULL'), nullable=True)
    problem: Mapped['Problem'] = relationship(
        'Problem',
        back_populates='child_tickets',
        uselist=False,
        foreign_keys=[problem_id]
    )

    requester_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    requester: Mapped['User'] = relationship(
        'User',
        foreign_keys=[requester_id],
        back_populates='tickets_requested',
    )

    source_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('source.id'), nullable=True)
    source: Mapped['Source'] = relationship(
        'Source',
        foreign_keys=[source_id],
        back_populates='ticket_source'
    )

    supporter_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    supporter: Mapped['User'] = relationship(
        'User',
        foreign_keys=[supporter_id],
        back_populates='tickets_supported'
    )

    support_team_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    support_team: Mapped['Team'] = relationship(
        'Team',
        foreign_keys=[support_team_id],
        back_populates='tickets'
    )

    subcategory_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('subcategory.id'), nullable=True)
    subcategory: Mapped['Subcategory'] = relationship(
        'Subcategory',
        foreign_keys=[subcategory_id],
        back_populates='ticket_subcategory',
    )

    # fields with default values
    is_major: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    is_parent: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    outage: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    rapid_resolution: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    sla_paused: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    sla_response_breach: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    sla_responded: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    sla_resolved: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    sla_resolve_breach: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    
    # Methods
    def update_comms_journal(self, subject, message):
        journal_entries = message.split('\n')
        comms_journal_entries = [
            CommsJournal(
                subject=subject,
                message=entry.strip(),
                timestamp=datetime.now(timezone.utc),
                ticket=self
            )
            for entry in journal_entries if entry.strip()
        ]
        # Associate these journal entries with the ticket
        self.comms_journal.extend(comms_journal_entries)

    def get_supporter_name(self):
        return self.supporter.full_name if self.supporter else 'Not assigned'

    def get_support_team_name(self):
        return self.support_team.name if self.support_team_id else 'Not assigned'

    def get_requester_name(self):
        return self.requester.full_name if self.requester else None

    @classmethod
    def get_ticket_stats(cls):
        # Query to get the counts for each condition
        incident_counts = db.session.execute(
            sa.select(
                sa.func.count().label("total"),
                sa.func.sum(sa.func.cast(cls.sla_response_breach, db.Integer)).label("response_breach"),
                sa.func.sum(sa.func.cast(cls.sla_resolve_breach, db.Integer)).label("resolve_breach")
            ).where(cls.ticket_type == "Incident")
        ).first()

        request_counts = db.session.execute(
            sa.select(
                sa.func.count().label("total"),
                sa.func.sum(sa.func.cast(cls.sla_response_breach, db.Integer)).label("response_breach"),
                sa.func.sum(sa.func.cast(cls.sla_resolve_breach, db.Integer)).label("resolve_breach")
            ).where(cls.ticket_type == "Request")
        ).first()

        # Format the results for the ECharts Polar Chart
        data = {
            "Incidents": {
                "Total": incident_counts.total or 0,
                "response-breach": incident_counts.response_breach or 0,
                "resolve-breach": incident_counts.resolve_breach or 0,
            },
            "Requests": {
                "Total": request_counts.total or 0,
                "response-breach": request_counts.response_breach or 0,
                "resolve-breach": request_counts.resolve_breach or 0,
            }
        }
        return data



class TicketTemplate(db.Model):
    """
    Templates to pre-populate a ticket for fast resolution
    """
    __tablename__ = 'ticket_template'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    affected_ci_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    priority_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    priority_impact: Mapped[Optional[str]] = mapped_column(db.String(8), nullable=True)
    priority_urgency: Mapped[Optional[str]]= mapped_column(db.String(8), nullable=True)
    resolution_code_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    source_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    subcategory_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    support_team_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    supporter_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    template_name: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    ticket_type: Mapped[Optional[str]] = mapped_column(db.String(15), nullable=True)


class Source(db.Model):
    __tablename__ = 'source'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True, server_default=None)
    source: Mapped[str] = mapped_column(db.String)
    ticket_source: Mapped['Ticket'] = relationship(
        'Ticket',
        foreign_keys='Ticket.source_id',
        back_populates='source'
    )

    @classmethod
    def get_source(cls):
        session = db.session  # or use your session object directly if you have one
        results = session.query(cls).all()
        return [{'id': result.id, 'source': result.source} for result in results]

    def __repr__(self):
        return f'{self.source}'


class TicketPauseHistory(db.Model):
    """
    Tracks each SLA pause event for a ticket. Locating here rather than in the relationship tables file
    as it is only used for Incidents/Requests (aka Interactions)
    """
    __tablename__ = 'ticket_pause_history'

    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    paused_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), nullable=False)
    resumed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(db.Float, nullable=True)  # Store pause duration in seconds

    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id', ondelete="CASCADE"))
    ticket: Mapped["Ticket"] = relationship(
        "Ticket",
        back_populates="pause_history"
    )

    reason_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('pause_reasons.id'), nullable=False)
    reason: Mapped["PauseReasons"] = relationship(
        "PauseReasons",
        back_populates="pause_history"
    )

    paused_by_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("user.id"), nullable=True)  # User ID (optional)
    paused_by: Mapped['User'] = relationship(
        "User",
        back_populates="pause_history"
    )

    def __repr__(self):
        return (f"<TicketPauseHistory(id={self.id}, ticket_id={self.ticket_id}, "
                f"paused_at={self.paused_at}, reason_id={self.reason_id})>")
