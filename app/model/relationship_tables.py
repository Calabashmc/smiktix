from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:  # only used for type hinting so no circular import issues
    from model_change import Change
    from model_user import User

from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from . import db

class ChangeApprover(db.Model):
    __tablename__ = 'change_approvers'
    change_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('change.id'), primary_key=True)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    approval_date: Mapped[datetime] = mapped_column(db.DateTime, nullable=True)

    # Relationships to the Change and User models
    change: Mapped['Change'] = relationship(
        'Change',
        back_populates='change_approvers'
    )

    user: Mapped['User'] = relationship(
        'User',
        back_populates='changes_approved'
    )
    # Fields with default values
    approved: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    approver_acknowledged: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)

    def __init__(self, **kwargs):
        super().__init__()
        # Set default values for columns that need them
        # Ensure that values can be overwritten by kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

cab_attendees = db.Table(
    'cab_attendees',
    db.Column('cab_id', db.ForeignKey('cab_details.id'), primary_key=True),
    db.Column('user_id', db.ForeignKey('user.id'), primary_key=True)
)


category_model = db.Table(
   'category_model',
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True),
    db.Column('model_lookup_id', db.Integer, db.ForeignKey('model_lookup.id'), primary_key=True),
)

change_department = db.Table(
    'change_department',
    db.metadata,  # Explicitly pass db.metadata
    db.Column('department_id', db.Integer, db.ForeignKey('department.id', ondelete='CASCADE'), primary_key=True),
    db.Column('change_id', db.Integer, db.ForeignKey('change.id', ondelete='CASCADE'), primary_key=True)
)

change_followers = db.Table(
    'change_followers',
    db.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('change_id', db.Integer, db.ForeignKey('change.id'), primary_key=True),
)

cmdb_compliance = db.Table(
    'cmdb_compliance',
    db.metadata,
    db.Column('ci_id', db.Integer, db.ForeignKey('cmdb_configuration_item.id'), primary_key=True),
    db.Column('compliance_id', db.Integer, db.ForeignKey('compliance.id'), primary_key=True)
)

cmdb_hardware_dependencies = db.Table(
    'cmdb_hardware _dependencies',
    db.metadata,
    db.Column('parent_id', db.Integer, db.ForeignKey('cmdb_configuration_item.id'), primary_key=True),
    db.Column('child_id', db.Integer, db.ForeignKey('cmdb_configuration_item.id'), primary_key=True)
)

# Association table for CmdbSoftware installed on CmdbHardware
cmdb_software_hardware = db.Table(
    'cmdb_software_hardware',
    db.metadata,  # Explicitly pass db.metadata
    db.Column('software_id', db.Integer, db.ForeignKey('cmdb_software.id'), primary_key=True),
    db.Column('hardware_id', db.Integer, db.ForeignKey('cmdb_hardware.id'), primary_key=True)
)

cmdb_service_components = db.Table(
    'cmdb_service_components',
    db.metadata,
    db.Column('service_id', db.Integer, db.ForeignKey('cmdb_service.id'), primary_key=True),
    db.Column('component_id', db.Integer, db.ForeignKey('cmdb_configuration_item.id'), primary_key=True)
)

idea_benefit = db.Table(
    'idea_benefit',
    db.metadata,
    db.Column('idea_id', db.Integer, db.ForeignKey('idea.id', ondelete='CASCADE')),
    db.Column('benefit_id', db.Integer, db.ForeignKey('benefits_lookup.id'))
)

idea_impact = db.Table(
    'idea_impact',
    db.metadata,
    db.Column('idea_id', db.Integer, db.ForeignKey('idea.id', ondelete='CASCADE')),
    db.Column('impact_id', db.Integer, db.ForeignKey('impact_lookup.id'))
)

incident_followers = db.Table(
    'incident_followers',
    db.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('ticket_id', db.Integer, db.ForeignKey('ticket.id'), primary_key=True),
)

problem_followers = db.Table(
    'problem_followers',
    db.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('problem_id', db.Integer, db.ForeignKey('problem.id'), primary_key=True),
)

release_cis = db.Table(
    'release_cis',
    db.metadata,
    db.Column('release_id', db.Integer, db.ForeignKey('release.id'), primary_key=True),
    db.Column('cmdb_id', db.Integer, db.ForeignKey('cmdb_configuration_item.id'), primary_key=True)
)

status_model = db.Table(
    "status_model",
    db.Column("status_id", db.ForeignKey("status_lookup.id"), primary_key=True),
    db.Column("model_id", db.ForeignKey("model_lookup.id"), primary_key=True),
)

user_roles = db.Table(
    'user_roles',
    db.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

user_votes = db.Table(
    'user_votes',
    db.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('idea_id', db.Integer, db.ForeignKey('idea.id', ondelete='CASCADE'), primary_key=True)
)
