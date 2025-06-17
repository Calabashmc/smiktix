from datetime import datetime, time
from email.policy import default
from flask import jsonify

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from typing import Optional
from . import db
from ..common.exception_handler import log_exception
from .relationship_tables import category_model, cmdb_compliance, idea_benefit, idea_impact, status_model
from ..model.model_interaction import TicketPauseHistory

class AppDefaults(db.Model):
    __tablename__ = 'app_defaults'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    change_default_risk: Mapped[Optional[str]] = mapped_column(db.String(4), nullable=True, default=None)
    cmdb_default_icon: Mapped[Optional[str]] = mapped_column(db.String(25), nullable=True, default=None)
    incident_default_impact: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True, default=None)
    incident_default_priority: Mapped[Optional[str]] = mapped_column(db.String(4), nullable=True, default=None)
    incident_default_urgency: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True, default=None)
    problem_default_priority: Mapped[Optional[str]] = mapped_column(db.String(4), nullable=True, default=None)
    servicedesk_close_hour: Mapped[Optional[str]] = mapped_column(db.String(5), nullable=True, default=None)
    servicedesk_email: Mapped[Optional[str]] = mapped_column(db.String(55), nullable=True, default=None)
    servicedesk_open_hour: Mapped[Optional[str]] = mapped_column(db.String(5), nullable=True, default=None)
    servicedesk_phone: Mapped[Optional[str]] = mapped_column(db.String(15), nullable=True, default=None)
    servicedesk_timezone: Mapped[Optional[str]] = mapped_column(db.String(4), nullable=True, default=None)
    support_team_default_id: Mapped[Optional[int]] = mapped_column(db.Integer(), nullable=True, default=None)

    @classmethod
    def get_app_defaults(cls):
        try:
            instance = db.session.get(cls, 1)
            return instance
        except Exception as e:
            log_exception(f'{e}')
            return None

    @classmethod
    def set_app_defaults(cls, data: dict):
        try:
            instance = db.session.get(cls, 1)
            if not instance:
                instance = cls(id=1)  # Create if missing

            valid_fields = cls.__table__.columns.keys()
            for key, value in data.items():
                if key in valid_fields:
                    setattr(instance, key, value)

            db.session.add(instance)
            db.session.commit()
            return jsonify({'success': True}), 200

        except Exception as e:
            db.session.rollback()
            log_exception(f'{e}')
            return jsonify({'success': False, 'error': str(e)}), 500


class BenefitsLookup(db.Model):
    __tablename__ = 'benefits_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    benefit: Mapped[str] = mapped_column(db.String(100))
    comment: Mapped[Optional[str]] = mapped_column(db.String(300), nullable=True)

    # Relationships
    ideas: Mapped[list['Idea']] = relationship(
        'Idea',
        secondary=idea_benefit,
        back_populates='benefits',
        cascade='save-update, merge',
    )


class BudgetBucketsLookup(db.Model):
    """
    Used only by CMDB but kept here as it might be useful for other models such as future versions of Change
    """
    __tablename__ = 'budget_buckets_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    budget_bucket: Mapped[str] = mapped_column(db.String(100))
    comment: Mapped[Optional[str]] = mapped_column(db.String(300), nullable=True)

class ChangeFreezeReasonLookup(db.Model):
    __tablename__ = 'change_freeze_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    reason: Mapped[str] = mapped_column(db.String(100))
    comment: Mapped[Optional[str]] = mapped_column(db.String(300), nullable=True)


class ChangeWindowLookup(db.Model):
    __tablename__ = 'change_window_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    day: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)
    start_time: Mapped[Optional[db.Time]] = mapped_column(db.Time, nullable=True)
    length: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    active: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)

    def __repr__(self):
        return f'id: {self.id}, day: {self.day}, start_time: {self.start_time}, length: {self.length}'


class ChangeTypeLookup(db.Model):
    __tablename__ = 'change_type_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    change_type: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)


class Compliance(db.Model):
    __tablename__ = 'compliance'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    compliance_standard: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Relationships
    cis: Mapped[list['CmdbConfigurationItem']] = relationship(
        'CmdbConfigurationItem',
        secondary=cmdb_compliance,
        back_populates='compliances'
    )

    # Equality needed to compare objects such as removing compliance
    # without this it will not work properly using  'if compliance in cmdb.compliances'
    def __eq__(self, other):
        if not isinstance(other, Compliance):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f'id: {self.id}, compliance_standard: {self.compliance_standard}, comment: {self.comment}'


class CostCenterLookup(db.Model):
    __tablename__ = 'cost_center_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    cost_center: Mapped[str] = mapped_column(db.String(20))
    code: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)


class DeliveryMethodLookup(db.Model):
    __tablename__ = 'delivery_method_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    delivery_method: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)


class HostingLookup(db.Model):
    __tablename__ = 'hosting_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    hosting: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

class ImpactLookup(db.Model):
    __tablename__ = 'impact_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    impact: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    ideas = db.relationship('Idea', secondary=idea_impact, back_populates='impact')

class Importance(db.Model):
    """
    Metalics lookup table for grouping CI's by importance to business function. Informs SLA
    """
    __tablename__ = 'importance'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    importance: Mapped[str] = mapped_column(db.String(20))
    rating: Mapped[int] = mapped_column(db.Integer)
    note: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    cmdb_importance = db.relationship(
        'CmdbConfigurationItem',
        foreign_keys='CmdbConfigurationItem.importance_id',
        back_populates='importance')


class KBATypesLookup(db.Model):
    __tablename__ = 'kba_types_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    article_type: Mapped[str] = mapped_column(db.String(30))
    comment: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)

    # relationships
    knowledge_articles: Mapped[list['KnowledgeBase']] = relationship(
        'KnowledgeBase',
        foreign_keys='KnowledgeBase.article_type_id',
        back_populates='article_type'
    )


class LikelihoodLookup(db.Model):
    __tablename__ = 'likelihood_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    likelihood: Mapped[str] = mapped_column(db.String(20))
    comment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)


class LocationLookup(db.Model):
    __tablename__ = 'location_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    location: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)


class ModelLookup(db.Model):
    __tablename__ = 'model_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(db.String(50), nullable=False, unique=True)

    categories: Mapped['Category'] = relationship(
        'Category',
        secondary=category_model,
        back_populates='model',
    )

    statuses: Mapped[list["StatusLookup"]] = relationship(
        "StatusLookup",
        secondary=status_model,
        back_populates="models",
    )

    def __eq__(self, other):
        return self.name == other

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f'{self.name}'


class OfficeHours(db.Model):
    __tablename__ = 'office_hours'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    location: Mapped[Optional[str]] = mapped_column(db.String(150), nullable=True, unique=True)
    open_hour: Mapped[time] = mapped_column(db.Time, nullable=False)
    close_hour: Mapped[Optional[time]] = mapped_column(db.Time, nullable=False)
    country: Mapped[str] = mapped_column(db.String(20))
    country_code: Mapped[str] = mapped_column(db.String(2))
    address: Mapped[Optional[str]] = mapped_column(db.String(150), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    province: Mapped[str] = mapped_column(db.String(15))
    timezone: Mapped[str] = mapped_column(db.String(50))

    # relationships
    users: Mapped['User'] = relationship(
        'User',
        back_populates='location'
    )
    # fields with defaults
    datetime_format: Mapped[str] = mapped_column(db.String(20), default="%Y-%m-%dT%H:%M", nullable=True)
    date_format: Mapped[str] = mapped_column(db.String(20), default="%Y-%m-%d", nullable=True)


class PauseReasons(db.Model):
    """
    This is a lookup table to populate SLA pause reasons modal. No relationships to other tables.
    """
    __tablename__ = 'pause_reasons'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    reason: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)

    pause_history: Mapped[list["TicketPauseHistory"]] = relationship(
        "TicketPauseHistory",
        back_populates="reason"
    )

    @classmethod
    def get_sla_pause_reasons(cls):
        session = db.session  # or use your session object directly if you have one
        results = session.query(cls).order_by(cls.id).all()
        return [{'id': result.id, 'reason': result.reason} for result in results]

    def __repr__(self):
        return f'{self.reason}'


class PlatformLookup(db.Model):
    __tablename__ = 'platform_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    platform: Mapped[str] = mapped_column(db.String(50))
    comment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)


class PriorityLookup(db.Model):
    """
    Lookup table for Priorities. Used for SLA calculation
    """
    __tablename__ = 'priority_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    priority: Mapped[str] = mapped_column(db.String(12))
    image_url: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    respond_by: Mapped[float] = mapped_column(db.Float)  # response time in minutes e.g. created time + this many minutes
    resolve_by: Mapped[float] = mapped_column(db.Float)  # resolve in minutes as per above
    twentyfour_seven: Mapped[bool] = mapped_column(db.Boolean, server_default=expression.false())  # set to true if SLA calc is only for business hours
    metalic: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)  # used for if services or devices are grouped for different SLA levels

    def __repr__(self):
        return f'{self.priority}'


class ResolutionLookup(db.Model):
    __tablename__ = 'resolution_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    resolution: Mapped[str] = mapped_column(db.String(100))
    comment: Mapped[Optional[str]] = mapped_column(db.String(300), nullable=True)
    model: Mapped[str] = mapped_column(db.String(20), nullable=False)


class RiskLookup(db.Model):
    """
    Lookup table for Change Risk.
    """
    __tablename__ = 'risk_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    risk: Mapped[str] = mapped_column(db.String(20))
    comment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)


class StatusLookup(db.Model):
    """
    Lookup table for Ticket statuses. Used for filtering tables. Referenced in get_paginated() (api_functions.py)
    """
    __tablename__ = 'status_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    # todo possibly use these fields instead of steps in js files. Would allow for more customisation of process steps
    allowedNext: Mapped[str] = mapped_column(db.String(200), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    label: Mapped[str] = mapped_column(db.String(20), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)

    status: Mapped[str] = mapped_column(db.String(20))

    tabs: Mapped[str] = mapped_column(db.String, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)

    models: Mapped[list["ModelLookup"]] = relationship(
        "ModelLookup",
        secondary=status_model,
        back_populates="statuses",
    )


class SupportTypeLookup(db.Model):
    __tablename__ = 'support_type_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    support_type: Mapped[str] = mapped_column(db.String(50))
    comment: Mapped[str] = mapped_column(db.Text, nullable=True)


class VendorLookup(db.Model):
    __tablename__ = 'vendor_lookup'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    vendor: Mapped[Optional[str]] = mapped_column(db.String(150), nullable=True)
    contact_name: Mapped[Optional[str]] = mapped_column(db.String(150), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(db.String(150), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
