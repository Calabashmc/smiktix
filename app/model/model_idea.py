from __future__ import annotations
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:  # only used for type hinting so no circular import issues
    from .model_category import Category
    from lookup_tables import BenefitsLookup, ImpactLookup
    from model_notes import Notes
    from model_user import Team, User
    
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped, relationship

from . import db
from .relationship_tables import idea_benefit, idea_impact

class Idea(db.Model):
    __tablename__ = 'idea'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    ticket_number: Mapped[int] = mapped_column(
        db.Integer,
        sa.Identity(start=1000, increment=1),  # Auto-incrementing sa.Identity column
        unique=True,
        nullable=False
    )

    business_goal_alignment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    current_issue: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    dependencies: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    estimated_cost: Mapped[Optional[str]] = mapped_column(db.String(30), nullable=True)
    estimated_effort: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    likelihood: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    resolution_code_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    resolution_journal: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)  # history of resolution changes
    resolution_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    risks_challenges: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    short_desc: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    ticket_type: Mapped[Optional[str]] = mapped_column(db.String(15), nullable=True)
    vote_count: Mapped[int] = mapped_column(db.Integer, server_default='0')
    vote_score: Mapped[int] = mapped_column(db.Integer, server_default='0')

    # relationships
    benefits: Mapped[list['BenefitsLookup']] = relationship(
        'BenefitsLookup',
        secondary=idea_benefit,
        back_populates='ideas',
        cascade='save-update, merge, delete',  # Automatically delete associations
        passive_deletes=True,  # Enable DB-level cascading deletes
    )

    category_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('category.id'))
    category: Mapped['Category'] = relationship(
        'Category',
        back_populates='idea_category',
    )

    created_by_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('user.id'))
    created_by: Mapped['User'] = relationship(
        'User',
        foreign_keys=[created_by_id],
        back_populates='ideas_created',
    )

    impact: Mapped[list['ImpactLookup']] = relationship(
        'ImpactLookup',
        secondary=idea_impact,
        back_populates='ideas',
        cascade='save-update, merge, delete',  # Automatically delete associations
        passive_deletes=True,
    )

    notes: Mapped[list['Notes']] = relationship(
        'Notes',
        back_populates='idea',
        lazy=True,
        cascade='all, delete,delete-orphan'
    )

    requester_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    requester: Mapped['User'] = relationship(
        'User',
        foreign_keys=[requester_id],
        back_populates='ideas_submitted'
    )

    support_team_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    support_team: Mapped['Team'] = relationship(
        'Team',
        back_populates='ideas'
    )

    voters: Mapped[list['User']] = relationship(
        'User',
        secondary='user_votes',
        back_populates='voted_ideas',
        cascade='save-update, merge, delete',  # Automatically delete associations
        passive_deletes=True,
    )

    def get_requester_name(self):
        if self.requester:
            return self.requester.full_name
        else:
            return None

    @classmethod
    def likelihood_count(cls):
        """
        Calling it priority_count to be consistent with all other models.
        It actually returns counts by likelihood
        """
        counts_dict = {}

        # Base query for counting by likelihood
        stmt = (
            sa.select(cls.likelihood, sa.func.count())
            .where(sa.and_(cls.status != 'closed'))
            .group_by(cls.likelihood)
        )

        # Execute the query
        likelihood_counts = db.session.execute(stmt).all()

        # Populate the counts dictionary
        for likelihood, count in likelihood_counts:
            counts_dict[likelihood] = count

        # Total count for all tickets of the given type and not closed
        total_count = db.session.execute(
            sa.select(sa.func.count())
            .where(sa.and_(cls.status != 'closed'))
        ).scalar()

        counts_dict['All'] = total_count
        return counts_dict

    @classmethod
    def tickets_category_count(cls):
        from .model_category import Category
        # Define the query to get category counts, excluding 'closed' status
        stmt = (
            sa.select(Category.name, sa.func.count().label('count'))
            .select_from(cls)  # Explicitly sa.select from the main table
            .join(Category, sa.and_(cls.category_id == Category.id))  # Explicit join condition
            .where(sa.and_(cls.status != 'closed'))
            .group_by(Category.name)
        )

        # Execute the query and populate the dictionary
        category_counts = db.session.execute(stmt).all()
        counts_dict = {category_name: count for category_name, count in category_counts}

        # Calculate the total count for non-closed tickets
        total_count = db.session.execute(sa.select(sa.func.count(cls.id)).where(sa.and_(cls.status != 'closed'))).scalar()
        counts_dict['All'] = total_count

        return counts_dict






