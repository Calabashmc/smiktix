from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from typing import Optional
from . import db


class PortalAnnouncements(db.Model):
    __tablename__ = 'portal_announcements'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    associated_ticket_model: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    associated_ticket_number: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    announcement: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    start: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    end: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)
    
    #Fields with default values
    active: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)



class ServiceCatalogue(db.Model):
    __tablename__ = 'service_catalogue'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    service: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    service_hours: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    sla_response_time: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    sla_resolve_time: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)

    # relationships
    owner_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    owner: Mapped['User'] = relationship(
        'User',
        foreign_keys=[owner_id],
        back_populates='services_owned'
    )

    cmdb_items: Mapped[list['CmdbConfigurationItem']] = relationship(
        'CmdbConfigurationItem',
        back_populates='service_catalogue'
    )

    # Fields with default values
    active: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)