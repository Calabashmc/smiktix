from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:  # only used for type hinting so no circular import issues
    from .model_category import Category, Subcategory
    from model_change import Change
    from model_cmdb import CmdbConfigurationItem
    from model_notes import CommsJournal, Notes
    from model_interaction import Ticket
    from model_user import Team, User

from datetime import datetime, timezone
from sqlalchemy import Identity
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import db


class Problem(db.Model):
    __tablename__ = 'problem'
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    ticket_number: Mapped[int] = mapped_column(
        db.Integer,
        Identity(start=1000, increment=1),  # Auto-incrementing identity column
        unique=True,
        nullable=False
    )
    analysis_method: Mapped[Optional[str]] = mapped_column(db.String(25), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    generic_rca_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    generic_root_cause: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    last_updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(db.String(2), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    resolution_code_id: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    resolution_journal: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)  # history of resolution changes
    resolution_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    short_desc: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(db.String(15), nullable=True)
    ticket_type: Mapped[Optional[str]] = mapped_column(db.String(15), nullable=True)

    # relationships
    category_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    category: Mapped['Category'] = relationship(
        'Category',
        back_populates='problem_category',
    )

    change_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('change.id', ondelete='SET NULL'), nullable=True)
    change: Mapped['Change'] = relationship(
        'Change',
        back_populates='child_problem'
    )

    child_tickets: Mapped[list['Ticket']] = relationship(
        'Ticket',
        back_populates='problem',
    )

    cmdb_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('cmdb_configuration_item.id'), nullable=True)
    cmdb: Mapped['CmdbConfigurationItem'] = relationship(
        'CmdbConfigurationItem',
        back_populates='problems'
    )

    comms_journal: Mapped[list['CommsJournal']] = relationship(
        'CommsJournal',
        back_populates='problem',
        cascade='all, delete'
    )

    created_by_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by: Mapped['User'] = relationship(
        'User',
        foreign_keys=[created_by_id],
        back_populates='problems_created',
    )

    five_whys: Mapped['FiveWhysAnalysis'] = relationship(
        'FiveWhysAnalysis',
        back_populates='problem',
        uselist=False
    )

    kepner_tregoe: Mapped['KepnerTregoeAnalysis'] = relationship(
        'KepnerTregoeAnalysis',
        back_populates='problem',
        uselist=False
    )

    notes: Mapped[list['Notes']] = relationship(
        'Notes',
        back_populates='problem',
        lazy=True,
        cascade='delete, delete-orphan'
    )

    requester_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    requester: Mapped['User'] = relationship(
        'User',
        foreign_keys=[requester_id],
        back_populates='problems_requested',
    )

    subcategory_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('subcategory.id'), nullable=True)
    subcategory: Mapped['Subcategory'] = relationship(
        'Subcategory',
        back_populates='problem_subcategory',
    )

    supporter_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    supporter: Mapped['User'] = relationship(
        'User',
        foreign_keys=[supporter_id],
        back_populates='problems_supported'
    )

    support_team_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    support_team: Mapped['Team'] = relationship(
        'Team',
        foreign_keys=[support_team_id],
        back_populates='problems'
    )

    def get_supporter_name(self):
        if self.supporter:
            return self.supporter.full_name
        else:
            return None

    def get_requester_name(self):
        if self.requester:
            return self.requester.full_name
        else:
            return None

    def __repr__(self):
        return f'{self.ticket_number}'


class KepnerTregoeAnalysis(db.Model):
    __tablename__ = 'kepner_tregoe_analysis'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    what_is_happening: Mapped[Optional[str]] = mapped_column(db.Text)
    what_should_be_happening: Mapped[Optional[str]] = mapped_column(db.Text)

    # Problem Specification (IS/IS NOT)
    where_is: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    where_is_not: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    where_distinction: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)

    when_is: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    when_is_not: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    when_distinction: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)

    what_extent_is: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    what_extent_is_not: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    what_extent_distinction: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)

    # Distinctions and Changes
    distinctions: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    changes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)

    # Possible Causes
    possible_causes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    most_probable_cause: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)

    # Testing and Verification
    test_results: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    kt_root_cause: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)

    problem_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    problem: Mapped['Problem'] = relationship(
        'Problem',
        back_populates='kepner_tregoe'
    )



class FiveWhysAnalysis(db.Model):
    __tablename__ = 'five_whys_analysis'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)

    # relationship
    problem_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    problem: Mapped['Problem'] = relationship(
        'Problem',
        back_populates='five_whys'
    )

    # The 5 Why's
    why_1_question: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    why_1_answer: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)

    why_2_question: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    why_2_answer: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)

    why_3_question: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    why_3_answer: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)

    why_4_question: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    why_4_answer: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)

    why_5_question: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    why_5_answer: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)

    # Root-cause and Actions
    why_root_cause: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    corrective_actions: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)
    preventive_actions: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, default=None)


