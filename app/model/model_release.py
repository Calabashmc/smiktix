from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:  # only used for type hinting so no circular import issues
    from .model_category import Category
    from .model_cmdb import CmdbConfigurationItem
    from model_user import User, Team
    from model_notes import Notes

from datetime import datetime, timezone
from flask_security import current_user
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..model.relationship_tables import release_cis

from . import db

class ReleaseTypesLookup(db.Model):
    __tablename__ = 'release_types_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    release_type: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(db.String(300), nullable=True)

    release: Mapped['Release'] = relationship(
        'Release',
        foreign_keys='Release.release_type_id',
        back_populates='release_type'
    )


class Release(db.Model):
    __tablename__ = 'release'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    ticket_number: Mapped[int] = mapped_column(
        db.Integer,
        sa.Identity(start=1000, increment=1),  # Auto-incrementing identity column
        unique=True,
        nullable=False
    )

    approval_by: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    approval_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    build_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    build_plan: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    created_at:Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    deployment_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    deployment_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    last_updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    release_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    release_dependencies: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    release_name: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    release_method: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    release_risks: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    release_stage: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    release_successful: Mapped[bool] = mapped_column(db.Boolean, nullable=True)
    release_version: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    resolution_code_id: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    resolution_journal: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)  # history of resolution changes
    resolution_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    short_desc: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    scheduled_date: Mapped[datetime] = mapped_column(db.DateTime, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=False)
    target_environment: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    test_plan: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    test_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    test_successful: Mapped[bool] = mapped_column(db.Boolean, nullable=True)
    ticket_type: Mapped[Optional[str]] = mapped_column(db.String(15), nullable=True)

    # relationships
    affected_cis: Mapped[list[CmdbConfigurationItem]] = relationship(
        "CmdbConfigurationItem",
        secondary=release_cis,
        back_populates="release_cis"
    )

    build_leader_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    build_leader: Mapped['User'] = relationship(
        'User',
        foreign_keys=[build_leader_id],
        back_populates='releases_built',
    )

    created_by_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by: Mapped['User'] = relationship(
        'User',
        foreign_keys=[created_by_id],
        back_populates='releases_created'
    )

    change_id = mapped_column(db.Integer, db.ForeignKey('change.id'),
                              nullable=True)  # Foreign key to the Change model (optional)

    category_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('category.id'))
    category: Mapped['Category'] = relationship(
        'Category',
        back_populates='release_category',
    )

    deployment_leader_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    deployment_leader: Mapped['User'] = relationship(
        'User',
        foreign_keys=[deployment_leader_id],
        back_populates='releases_deployed',
    )

    notes: Mapped[list['Notes']] = relationship(
        'Notes',
        back_populates='release',
        lazy=True,
        cascade='delete, delete-orphan'
    )

    product_owner_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    product_owner: Mapped['User'] = relationship(
        'User',
        foreign_keys=[product_owner_id],
        back_populates='releases_approved',
    )

    release_type_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('release_types_lookup.id'), nullable=True)
    release_type: Mapped['ReleaseTypesLookup'] = relationship(
        'ReleaseTypesLookup',
        foreign_keys=[release_type_id],
        back_populates='release',
    )

    requester_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    requester: Mapped['User'] = relationship(
        'User',
        foreign_keys=[requester_id],
        back_populates='releases_requested',
    )

    support_team_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('team.id'))
    support_team: Mapped['Team'] = relationship(
        'Team', foreign_keys=[support_team_id], back_populates='releases'
    )

    supporter_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    supporter: Mapped['User'] = relationship(
        'User',
        foreign_keys=[supporter_id],
        back_populates='releases_supported'
    )

    test_leader_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    test_leader: Mapped['User'] = relationship(
        'User',
        foreign_keys=[test_leader_id],
        back_populates='releases_tested',
    )

    # fields with default values
    approved: Mapped[bool] = mapped_column(db.Boolean, nullable=True, default=False)
    deployment_successful: Mapped[bool] = mapped_column(db.Boolean, nullable=True, default=False)

    def get_affected_cis(self):
        return [ci.name for ci in self.affected_cis]

    def get_release_name(self):
        return self.release_name if self.requester else None

    def get_requester_name(self):
        return self.requester.full_name if self.requester else None

    def get_support_team_name(self):
        return self.support_team.name

    @classmethod
    def category_counts(cls, scope):
        from .model_category import Category
        counts_dict = {}

        stmt = (sa.select(Category.name, sa.func.count(cls.id).label('count'))
                .join(cls, cls.category_id == Category.id)
                .group_by(Category.name)
                .where(cls.status != 'closed'))

        if scope == 'me':
            stmt = stmt.where(Release.supporter_id == current_user.id)

        if scope == 'team':
            team_id = current_user.team_id
            stmt = stmt.where(sa.and_(Release.supporter_id != current_user.id, Release.support_team_id == team_id))

        # Query to get category counts
        category_counts = (db.session.execute(stmt)
                           .all())

        # Populate the dictionary with results
        for category_name, count in category_counts:
            counts_dict[category_name] = count

        return counts_dict

    @classmethod
    def release_type_count(cls, scope):
        stmt = (sa.select(ReleaseTypesLookup.release_type, sa.func.count(cls.id).label('count'))  # Labeling count
                .join(cls, cls.release_type_id == ReleaseTypesLookup.id)
                .group_by(ReleaseTypesLookup.release_type))

        if scope == 'me':
            stmt = stmt.where(cls.supporter_id == current_user.id)

        if scope == 'team':
            stmt = stmt.where(sa.and_(
                cls.supporter_id != current_user.id),
                cls.support_team_id == current_user.team_id)

        # Define the main query to fetch both change_type counts and the total count
        release_type_counts = db.session.execute(stmt).all()

        # Calculate total count (for 'All')
        total_count = sum(count for _, count in release_type_counts)
        # Prepare the final dictionary
        counts_dict = {release_type: count for release_type, count in release_type_counts}
        counts_dict['All'] = total_count
        return counts_dict




