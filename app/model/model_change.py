from __future__ import annotations
from datetime import datetime, date, time, timezone
from jinja2.filters import Markup

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from typing import List, Optional
from . import db
from .relationship_tables import ChangeApprover, cab_attendees, change_followers
from ..model.model_problem import Problem
from ..model.model_interaction import Ticket


class Change(db.Model):
    __tablename__ = 'change'
    id: Mapped[int] = mapped_column(db.Integer, sa.Identity(), primary_key=True)
    ticket_number: Mapped[int] = mapped_column(
        db.Integer,
        sa.Identity(start=1000, increment=1),  # Auto-incrementing sa.Identity column
        unique=True,
        nullable=False
    )

    build_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    build_plan: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    cab_approval_status: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    cab_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    cab_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    cab_ready: Mapped[Optional[bool]] = mapped_column(db.Boolean, nullable=True)
    change_cancelled: Mapped[Optional[bool]] = mapped_column(db.Boolean, nullable=True)
    change_reason: Mapped[Optional[str]] = mapped_column(db.String(3), nullable=True)
    change_successful: Mapped[Optional[bool]] = mapped_column(db.Boolean, nullable=True)
    change_type: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    comms_plan: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    downtime: Mapped[Optional[float]] = mapped_column(db.Numeric, nullable=True)
    ecab_approved: Mapped[Optional[bool]] = mapped_column(db.Boolean, nullable=True)
    effects_plan: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(db.Time, nullable=True)
    expected_duration: Mapped[Optional[float]] = mapped_column(db.Numeric, nullable=True)
    implement_plan: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    last_updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    other_fail_reason: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    people_impact: Mapped[Optional[int]] = mapped_column(db.Integer, server_default='0')
    resolution_code_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    resolution_journal: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)  # history of resolution changes
    resolution_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    risk_calc: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    risk_set: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    risk_continuity_impact: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    risk_continuity_likelihood: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    risk_customer_impact: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    risk_customer_likelihood: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    risk_data_impact: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    risk_data_likelihood: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    risk_financial_impact: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    risk_financial_likelihood: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    risk_reputation_impact: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    risk_reputation_likelihood: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    risk_security_impact: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    risk_security_likelihood: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    rollback_plan: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    scale: Mapped[Optional[str]] = mapped_column(db.String(8), nullable=True)
    short_desc: Mapped[Optional[str]] = mapped_column(db.String(200))
    standard_change_exemplar: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    start_time: Mapped[Optional[time]] = mapped_column(db.Time, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(db.String(25))
    test_date_start: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    test_date_end: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    test_plan: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    test_results: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    test_successful: Mapped[Optional[bool]] = mapped_column(db.Boolean, nullable=True)
    ticket_type: Mapped[Optional[str]] = mapped_column(db.String(15), nullable=True)

    # relationships
    category_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('category.id'))
    category: Mapped['Category'] = relationship(
        'Category',
        foreign_keys=[category_id],
        back_populates='change_category'
    )

    change_approvers: Mapped[List['ChangeApprover']] = relationship(
        'ChangeApprover',
        back_populates='change'
    )

    child_ticket: Mapped['Ticket'] = relationship(
        'Ticket',
        back_populates='change'
    )

    child_problem: Mapped['Problem'] = relationship(
        'Problem',
        back_populates='change'
    )

    cmdb_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('cmdb_configuration_item.id'),
                                                   nullable=True)
    cmdb: Mapped[Optional['CmdbConfigurationItem']] = relationship(
        'CmdbConfigurationItem',
        back_populates='changes'
    )

    created_by_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by: Mapped[Optional['User']] = relationship(
        'User',
        foreign_keys='Change.created_by_id',
        back_populates='changes_created'
    )

    departments_impacted: Mapped[List['Department']] = relationship(
        'Department',
        secondary='change_department',
        back_populates='changes'
    )

    ecab_approver_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ecab_approver: Mapped[Optional['User']] = relationship(
        'User',
        foreign_keys='Change.ecab_approver_id',
        back_populates='changes_ecab_approved'
    )

    notes: Mapped[List['Notes']] = relationship(
        'Notes',
        back_populates='change',
        lazy=True,
        cascade='all, delete-orphan'
    )

    requester_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('user.id'))
    requester: Mapped['User'] = relationship(
        'User',
        foreign_keys='Change.requester_id',
        back_populates='changes_requested'
    )

    support_team_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('team.id'))
    support_team: Mapped['Team'] = relationship(
        'Team',
        back_populates='changes'
    )

    supporter_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    supporter: Mapped[Optional['User']] = relationship(
        'User',
        foreign_keys='Change.supporter_id',
        back_populates='changes_supported'
    )

    tester_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    tester: Mapped[Optional['User']] = relationship(
        'User',
        foreign_keys='Change.tester_id',
        back_populates='changes_tested'
    )

    # fields with default value must come after other fields
    cab_check_approver_consensus: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    cab_check_category: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    cab_check_no_clash: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    cab_check_plan_build: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    cab_check_plan_comms: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    cab_check_plan_implement: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    cab_check_plan_impact: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    cab_check_plan_rollback: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    cab_check_plan_test: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    cab_check_reason: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    cab_check_security: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    cab_check_timing: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    extended_outage: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    risk_continuity: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    risk_data: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    risk_customer: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    risk_financial: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    risk_reputation: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    rollback_required: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    risk_security: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    vendor_issue: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)

    # methods
    def create_notes(self, note_content, noted_by):
        from . import Notes
        worklog = Notes(
            note=Markup(note_content),
            noted_by=noted_by,
            note_date=datetime.now(timezone.utc),
            ticket_type=self.ticket_type,
            ticket_number=self.ticket_number
        )
        self.notes.append(worklog)

    def get_supporter_name(self):
        return str(self.supporter.full_name) if self.supporter else 'None'

    def get_requester_name(self):
        return str(self.requester.full_name) if self.requester else 'None'

    @classmethod
    def cab_status_count(cls):
        cab_status_counts = db.session.execute(
            sa.select(cls.cab_approval_status, sa.func.count().label('count'))
            .where(cls.status == 'cab')
            .group_by(cls.cab_approval_status)
        ).fetchall()

        total_count = sum(count for _, count in cab_status_counts)  # total for center of pie chart

        # Prepare the final dictionary
        counts_dict = {change_type: count for change_type, count in cab_status_counts}
        # counts_dict['All'] = total_count

        return counts_dict

    @classmethod
    def change_type_count(cls, scope):
        # Determine the scope filter based on the passed argument
        if scope == 'cab':
            scope_filter = cls.status == 'cab'
        else:
            scope_filter = cls.status != 'closed'

        # Define the main query to fetch both change_type counts and the total count
        change_type_counts = db.session.execute(
            sa.select(
                cls.change_type,
                sa.func.count().label('count')  # Labeling count correctly
            )
            .where(scope_filter)  # Correct placement
            .group_by(cls.change_type)
        ).fetchall()

        # Calculate total count (for 'All')
        total_count = sum(count for _, count in change_type_counts)

        # Prepare the final dictionary
        counts_dict = {change_type: count for change_type, count in change_type_counts}
        counts_dict['All'] = total_count

        return counts_dict

    @classmethod
    def change_risk_count(cls, change_type, scope):
        counts_dict = {}

        if scope == 'cab':
            risk_counts = db.session.execute(
                sa.select(cls.risk_set, sa.func.count())
                .where(cls.status == 'cab')
                .group_by(cls.risk_set)
            ).all()


        else:
            risk_counts = db.session.execute(
                sa.select(cls.risk_set, sa.func.count())
                .where(cls.status != 'closed')
                .group_by(cls.risk_set)
            ).all()

        total_count = sum(count for _, count in risk_counts)

        for risk, count in risk_counts:
            counts_dict[risk] = count

        counts_dict['All'] = total_count
        return counts_dict

    @classmethod
    def scheduled_changes(cls):
        scheduled = []
        scheduled_changes = (db.session.execute(
            sa.select(cls)
            .where(sa.and_(cls.status != 'closed', sa.or_(cls.status == 'cab', cls.status == 'implement')))
        ).scalars().all())

        for change in scheduled_changes:
            change_class = f'{change.risk_set.lower()}-change'  # used by css to set event colour in Change calendar
            if change.change_type == 'Emergency':
                change_class = 'emergency-change'  # class set to this so css can highlight in red

            date_time_start = datetime.combine(change.start_date, change.start_time).isoformat()
            date_time_end = datetime.combine(change.end_date, change.end_time).isoformat()

            scheduled.append({
                'id': change.ticket_number,
                'resourceId': change.support_team_id,
                'content': Markup(
                    f'Change: {change.ticket_number}\n'
                    f'Type: {change.change_type} \n'
                    f"Approval: {change.cab_approval_status or 'TBD'} \n"
                    f'Status: {change.status}'
                ),
                'start': date_time_start,
                'end': date_time_end,
                'group': change.change_type,
                'className': f'{change.risk_set.lower()}-change',
            })
        return scheduled

    @classmethod
    def get_change_resources(cls):
        from ..model.model_user import Team
        change_teams = db.session.execute(
            sa.select(Team)
            .join(cls, cls.support_team_id == Team.id)
            .where(sa.or_(cls.status == 'cab', cls.status == 'implement'))
            .distinct()  # Ensure uniqueness
        ).scalars().all()

        resources = [{'id': team.id, 'title': team.name} for team in change_teams]
        return resources

    def __repr__(self):
        return f'{self.ticket_number}'


class ChangeReasons(db.Model):
    __tablename__ = 'change_reasons'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    reason: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)

    def __repr__(self):
        return f'{self.reason}'


class ChangeTemplates(db.Model):
    __tablename__ = 'change_templates'
    id: Mapped[int] = mapped_column(db.Integer, sa.Identity(), primary_key=True)
    cab_approval_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)
    change_reason: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)
    cmdb_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    comms_plan: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    departments_impacted: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    implement_plan: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    name: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)
    risk_set: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    short_desc: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    support_team: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)


class CabDetails(db.Model):
    __tablename__ = 'cab_details'
    id: Mapped[int] = mapped_column(db.Integer, sa.Identity(), primary_key=True)
    cab_number: Mapped[int] = mapped_column(
        db.Integer,
        sa.Identity(start=1, increment=1),  # Auto-incrementing sa.Identity column
        unique=True,
        nullable=False
    )

    cab_datetime: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    cab_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)


    # Relationships
    attendees: Mapped[List['User']] = relationship(
        'User',
        secondary=cab_attendees,
        back_populates='cabs_attended'
    )

    cab_chair_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    chaired_by: Mapped['User'] = relationship(
        'User',
        back_populates='cabs_chaired'
    )