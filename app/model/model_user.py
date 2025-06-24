from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from flask_security import RoleMixin, UserMixin
from sqlalchemy import and_, Identity, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from . import db
from .model_change import Change, CabDetails
from .model_cmdb import CmdbConfigurationItem
from .model_idea import Idea
from .model_knowledge import KnowledgeBase
from .model_problem import Problem
from .model_interaction import Ticket
from .model_release import Release
from .relationship_tables import (
    ChangeApprover,
    cab_attendees,
    change_followers,
    incident_followers,
    problem_followers,
    user_roles,
    user_votes
)

class Department(db.Model):
    __tablename__ = 'department'
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100))
    description: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    changes: Mapped[List['Change']] = relationship(
        'Change',
        secondary='change_department',
        back_populates='departments_impacted'
    )

    users: Mapped[List['User']] = relationship(
        'User',
        back_populates='department',
        lazy='dynamic'
    )

    def __init__(self, **kwargs):
        # Set default values for columns that need them
        # Ensure that values can be overwritten by kwargs
        super().__init__()

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return self.name


class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(db.String(80), unique=True)
    description: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    users: Mapped[List['User']] = relationship(
        'User',
        secondary=user_roles,
        back_populates='roles',
        lazy='select'
    )



class Team(db.Model):
    __tablename__ = 'team'
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(db.String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    changes: Mapped[List['Change']] = relationship(
        'Change',
        foreign_keys=[Change.support_team_id],
        back_populates='support_team',
        lazy=True
    )

    cis: Mapped[List['CmdbConfigurationItem']] = relationship(
        'CmdbConfigurationItem',
        foreign_keys=[CmdbConfigurationItem.support_team_id],
        back_populates='support_team',
        lazy=True
    )

    ideas: Mapped[List['Idea']] = relationship(
        'Idea',
        foreign_keys=[Idea.support_team_id],
        back_populates='support_team',
        lazy=True
    )

    members: Mapped[List['User']] = relationship(
        'User',
        back_populates='team',
        lazy=True
    )

    problems: Mapped[List['Problem']] = relationship(
        'Problem',
        foreign_keys=[Problem.support_team_id],
        back_populates='support_team',
        lazy=True
    )

    releases: Mapped[List['Release']] = relationship(
        'Release',
        foreign_keys=[Release.support_team_id],
        back_populates='support_team',
        lazy=True
    )

    tickets: Mapped[List['Ticket']] = relationship(
        'Ticket',
        foreign_keys=[Ticket.support_team_id],
        back_populates='support_team',
        lazy=True
    )



class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    avatar: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(db.DateTime(timezone=True), nullable=True)
    current_login_at: Mapped[datetime | None] = mapped_column(db.DateTime(timezone=True), nullable=True)
    current_login_ip: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    email: Mapped[str] = mapped_column(db.String(255), nullable=False, unique=True)
    first_name: Mapped[Optional[str]] = mapped_column(db.String(30), nullable=True)
    fs_uniquifier: Mapped[Optional[str]] = mapped_column(db.String(255), unique=True, nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(db.String(60), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(db.String(30), nullable=True)
    login_count: Mapped[Optional[int]] = mapped_column(db.Integer, server_default='0', nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(db.String(15), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=False, unique=True)
    us_phone_number: Mapped[Optional[str]] = mapped_column(db.String(128), nullable=True)
    us_totp_secrets = db.Column(db.JSON, nullable=True)

    # Foreign keys and relationships
    articles_approved: Mapped[List['KnowledgeBase']] = relationship(
        'KnowledgeBase',
        foreign_keys='KnowledgeBase.approver_id',
        back_populates='approver',
    )

    articles_authored: Mapped[List['KnowledgeBase']] = relationship(
        'KnowledgeBase',
        foreign_keys='KnowledgeBase.author_id',
        back_populates='author'
    )

    articles_created: Mapped[List['KnowledgeBase']] = relationship(
        'KnowledgeBase',
        foreign_keys='KnowledgeBase.created_by_id',
        back_populates='created_by'
    )

    cabs_attended: Mapped[List['CabDetails']] = relationship(
        'CabDetails',
        secondary=cab_attendees,
        back_populates='attendees'
    )

    cabs_chaired: Mapped[List['CabDetails']] = relationship(
        'CabDetails',
        back_populates='chaired_by',
        foreign_keys='CabDetails.cab_chair_id'
    )

    changes_approved: Mapped[list['ChangeApprover']] = relationship(
        'ChangeApprover',
        back_populates='user'
    )

    changes_created: Mapped[list['Change']] = relationship(
        'Change',
        foreign_keys=[Change.created_by_id],
        back_populates='created_by'
    )

    changes_ecab_approved: Mapped[list['Change']] = relationship(
        'Change',
        foreign_keys=[Change.ecab_approver_id],
        back_populates='ecab_approver'
    )

    changes_requested: Mapped[list['Change']] = relationship(
        'Change',
        foreign_keys=[Change.requester_id],
        back_populates='requester'
    )

    changes_supported: Mapped[list['Change']] = relationship(
        'Change',
        foreign_keys=[Change.supporter_id],
        back_populates='supporter'
    )

    changes_tested: Mapped[list['Change']] = relationship(
        'Change',
        foreign_keys=[Change.tester_id],
        back_populates='tester'
    )

    cis_created: Mapped[list['CmdbConfigurationItem']] = relationship(
        'CmdbConfigurationItem',
        foreign_keys=[CmdbConfigurationItem.created_by_id],
        back_populates='created_by'
    )

    cis_owned: Mapped[list['CmdbConfigurationItem']] = relationship(
        'CmdbConfigurationItem',
        foreign_keys=[CmdbConfigurationItem.owner_id],
        back_populates='owner'
    )

    department_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('department.id', ondelete='SET NULL'),
        nullable=True
    )

    department: Mapped['Department'] = relationship(
        'Department',
        back_populates='users'
    )

    ideas_created: Mapped[list['Idea']] = relationship(
        'Idea',
        foreign_keys='Idea.created_by_id',
        back_populates='created_by'
    )

    ideas_submitted: Mapped[list['Idea']] = relationship(
        'Idea',
        foreign_keys='Idea.requester_id',
        back_populates='requester'
    )

    location_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('office_hours.id', ondelete='SET NULL'),
        nullable=True
    )
    location: Mapped['OfficeHours'] = relationship(
        'OfficeHours',
        back_populates='users'
    )

    # self-referencing relationship. Define the relationship with the manager and sub-ordinates
    manager_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    manager: Mapped['User'] = relationship(
        'User',
        remote_side=[id],
        back_populates='subordinates',
        uselist=False
    )

    pause_history: Mapped[list['TicketPauseHistory']] = relationship(
        'TicketPauseHistory',
        back_populates='paused_by'
    )

    problems_created: Mapped[list['Problem']] = relationship(
        'Problem',
        foreign_keys=[Problem.created_by_id],
        back_populates='created_by'
    )

    problems_requested: Mapped[list['Problem']] = relationship(
        'Problem',
        foreign_keys=[Problem.requester_id],
        back_populates='requester'
    )

    problems_supported: Mapped[list['Problem']] = relationship(
        'Problem',
        foreign_keys=[Problem.supporter_id],
        back_populates='supporter'
    )

    releases_approved: Mapped[list['Release']] = relationship(
        'Release',
        foreign_keys=[Release.product_owner_id],
        back_populates='product_owner'
    )

    releases_built: Mapped[list['Release']] = relationship(
        'Release',
        foreign_keys=[Release.build_leader_id],
        back_populates='build_leader'
    )

    releases_created: Mapped[list['Release']] = relationship(
        'Release',
        foreign_keys=[Release.created_by_id],
        back_populates='created_by'
    )

    releases_deployed: Mapped[list['Release']] = relationship(
        'Release',
        foreign_keys=[Release.deployment_leader_id],
        back_populates='deployment_leader'
    )

    releases_requested: Mapped[list['Release']] = relationship(
        'Release',
        foreign_keys=[Release.requester_id],
        back_populates='requester'
    )

    releases_supported: Mapped[list['Release']] = relationship(
        'Release',
        foreign_keys=[Release.supporter_id],
        back_populates='supporter'
    )

    releases_tested: Mapped[list['Release']] = relationship(
        'Release',
        foreign_keys=[Release.test_leader_id],
        back_populates='test_leader'
    )

    roles: Mapped[list['Role']] = relationship(
        'Role',
        secondary=user_roles,
        back_populates='users',
        lazy='select'  # Enables query-like behavior
    )

    services_owned: Mapped[list['ServiceCatalogue']] = relationship(
        'ServiceCatalogue',
        foreign_keys='ServiceCatalogue.owner_id',
        back_populates='owner'
    )

    subordinates: Mapped[list['User']] = relationship(
        'User',
        back_populates='manager',
        uselist=True
    )

    team_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('team.id'), nullable=True)  # Foreign key to Team
    team: Mapped['Team'] = relationship(
        'Team',
        back_populates='members'
    )

    tickets_created: Mapped[list['Ticket']] = relationship(
        'Ticket',
        foreign_keys=[Ticket.created_by_id],
        back_populates='created_by'
    )

    tickets_requested: Mapped[list['Ticket']] = relationship(
        'Ticket',
        foreign_keys=[Ticket.requester_id],
        back_populates='requester'
    )

    tickets_supported: Mapped[list['Ticket']] = relationship(
        'Ticket',
        foreign_keys=[Ticket.supporter_id],
        back_populates='supporter'
    )

    voted_ideas: Mapped[list['Idea']] = relationship(
        'Idea',
        secondary='user_votes',
        back_populates='voters'
    )
    # Fields with default values
    active: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.true(), default=True)
    vip: Mapped[bool] = mapped_column(
        db.Boolean, nullable=True, server_default=expression.false(), default=False)

    def get_incident_count(self):
        return len(
            [ticket for ticket in self.tickets_requested if
             ticket.ticket_type == 'Incident' and ticket.status != 'closed'])

    def get_request_count(self):
        return len(
            [ticket for ticket in self.tickets_requested if
             ticket.ticket_type == 'Request' and ticket.status != 'closed'])

    # Add a method to get the count of ideas submitted by the user
    def get_ideas_count(self):
        return len(self.ideas_submitted)

    # Add a method to get the count of cis_owned by the user
    def get_cis_owned_count(self):
        return len(self.cis_owned)

    # Add a method to get links to the cis_owned by the user
    @property
    def owned_assets(self):
        # Return a simplified version of the data, or a list of names if the relationship is loaded
        if self.cis_owned:
            return [ci.name for ci in self.cis_owned]
        return []

    # Add a method to get links to the ideas submitted by the user
    def get_ideas_proposed(self):
        return self.ideas_submitted

    def get_manager(self):
        return self.manager

    def get_department(self):
        return self.department.name if self.department else None

    def get_us_totp_secrets(self):
        return self.us_totp_secrets

    def set_us_totp_secrets(self, secrets):
        self.us_totp_secrets = secrets

    @property
    def role_names(self):
        return [role.name for role in self.roles]

    @property
    def role_ids(self):
        return [role.id for role in self.roles]

    def __repr__(self):
        return self.full_name
