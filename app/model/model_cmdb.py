from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:  # only used for type hinting so no circular import issues
    from lookup_tables import Compliance, Importance
    from .model_category import Category
    from model_change import Change
    from model_notes import Notes
    from model_interaction import Ticket
    from model_portal import ServiceCatalogue
    from model_problem import Problem
    from model_release import Release
    from model_user import Team, User

from datetime import datetime, timezone, date
from sqlalchemy import func, select, Identity
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from . import db
from .relationship_tables import (
    cmdb_compliance,
    cmdb_hardware_dependencies,
    cmdb_software_hardware,
    cmdb_service_components,
    release_cis
)


class CmdbConfigurationItem(db.Model):
    __tablename__ = 'cmdb_configuration_item'
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    ticket_number: Mapped[int] = mapped_column(
        db.Integer,
        Identity(start=1000, increment=1),  # Auto-incrementing sa.Identity column
        unique=True,
        nullable=False
    )

    brand: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)
    change_freeze_end_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    change_freeze_start_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    change_freeze_reason: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime)

    details: Mapped[Optional[str]] = mapped_column(db.Text,
                                                   nullable=True)  # labeled a 'configuration' in the form for CMDB records
    delivery_method: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    disposed_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    end_of_life_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)
    install_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    last_updated_at: Mapped[Optional[date]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    name: Mapped[str] = mapped_column(db.String, nullable=False)
    obtained_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    replacement_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    retirement_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    short_desc: Mapped[str] = mapped_column(db.String)
    status: Mapped[str] = mapped_column(db.String(50), nullable=False)
    support_end_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    support_type: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    ticket_type: Mapped[str] = mapped_column(db.String(50), nullable=False)

    type: Mapped[str] = mapped_column(db.String(50), nullable=False)  # To specify the CI type
    vendor_sales_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    vendor_support_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    # Fields with default values - because they do not do default=False they technically do not have
    # to come after the other fields. But can't add default=False as it screws with inheriting classes
    continuity_planning: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false())
    twentyfour_operation: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false())
    virtual_machine: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false())

    # Polymorphic inheritance
    __mapper_args__ = {
        'polymorphic_identity': 'cmdb_configuration_item',
        'polymorphic_on': type,
    }

    # relationships
    category_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('category.id'))
    category: Mapped['Category'] = relationship('Category', foreign_keys=[category_id],
                                                back_populates='configuration_items')

    changes: Mapped[list['Change']] = relationship(
        'Change',
        back_populates='cmdb'
    )

    change_freezes: Mapped[list['ChangeFreeze']] = relationship(  # Changed name to plural to indicate multiple
        'ChangeFreeze',
        back_populates='ci',
        cascade='all, delete-orphan'  # Optional: automatically delete change freezes when CI is deleted
    )

    created_by_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('user.id'))
    created_by: Mapped['User'] = relationship(
        'User',
        foreign_keys=[created_by_id],
        back_populates='cis_created',
    )

    compliances: Mapped[list['Compliance']] = relationship(
        'Compliance',
        secondary=cmdb_compliance,
        back_populates='cis'
    )

    importance_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('importance.id'), nullable=True)
    importance: Mapped['Importance'] = relationship(
        'Importance',
        foreign_keys=[importance_id],
        back_populates='cmdb_importance'
    )

    notes: Mapped[list['Notes']] = relationship(
        'Notes',
        back_populates='cmdb',
        lazy=True,
        cascade='delete,delete-orphan'
    )

    problems: Mapped[list['Problem']] = relationship(
        'Problem',
        back_populates='cmdb'
    )

    release_cis: Mapped[list["Release"]] = relationship(
        "Release",
        secondary=release_cis,
        back_populates="affected_cis"
    )

    replaced_with_id: Mapped[Optional[int]] = mapped_column(db.Integer,
                                                            db.ForeignKey('cmdb_configuration_item.id',
                                                                          ondelete='SET NULL'),
                                                            nullable=True)
    replaced_with: Mapped['CmdbConfigurationItem'] = relationship(
        'CmdbConfigurationItem',
        remote_side=[id],
        back_populates='replacing',
        passive_deletes=False
    )

    replacing: Mapped['CmdbConfigurationItem'] = relationship(
        'CmdbConfigurationItem',
        back_populates='replaced_with',
        passive_deletes=False
    )

    services: Mapped[list['CmdbService']] = relationship(
        'CmdbService',
        secondary=cmdb_service_components,
        primaryjoin=(id == cmdb_service_components.c.component_id),
        secondaryjoin='CmdbService.id == cmdb_service_components.c.service_id',
        back_populates='components',

    )

    owner_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    owner: Mapped['User'] = relationship(
        'User',
        foreign_keys=[owner_id],
        back_populates='cis_owned'
    )

    # Relationships for dependencies
    service_catalogue_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('service_catalogue.id', ondelete='SET NULL'),
        nullable=True
    )

    service_catalogue: Mapped['ServiceCatalogue'] = relationship(
        'ServiceCatalogue',
        back_populates='cmdb_items',
        foreign_keys=[service_catalogue_id],
        passive_deletes='all'
    )

    support_team_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    support_team: Mapped['Team'] = relationship(
        'Team',
        foreign_keys=[support_team_id],
        back_populates='cis'
    )

    tickets: Mapped[list['Ticket']] = relationship(
        'Ticket',
        back_populates='cmdb'
    )

    def get_change_freeze_list(self):
        return self.change_freezes

    def get_compliances(self):
        return self.compliances

    def get_support_team(self):
        if self.support_team:
            return self.support_team.name
        else:
            return None

    def get_requester_name(self):
        if self.owner:
            return self.owner.full_name
        else:
            return None

    def get_vendor_sales(self):
        from ..model.lookup_tables import VendorLookup
        if self.vendor_sales_id:
            return db.session.execute(
                select(VendorLookup)
                .where(VendorLookup.id == self.vendor_sales_id)
            ).scalars()
        else:
            return None

    def get_vendor_support(self):
        from ..model.lookup_tables import VendorLookup
        if self.vendor_support_id:
            return db.session.execute(
                select(VendorLookup)
                .where(VendorLookup.id == self.vendor_support_id)
            ).scalars()
        else:
            return None

    @classmethod
    def category_counts(cls):
        from .model_category import Category
        counts_dict = {}

        # Query to get category counts
        category_counts = (
            db.session.execute(
                select(Category.name, func.count(CmdbConfigurationItem.id).label('count'))
                .join(CmdbConfigurationItem, CmdbConfigurationItem.category_id == Category.id)
                .where(CmdbConfigurationItem.status != 'disposed')
                .group_by(Category.name)
            )
        ).all()

        # Populate the dictionary with results
        for category_name, count in category_counts:
            counts_dict[category_name] = count

        # Add the 'All' count
        counts_dict['All'] = db.session.execute(
            select(func.count()).where(CmdbConfigurationItem.status != 'disposed')
        ).scalar()

        return counts_dict

    @classmethod
    def importance_counts(cls):
        from .lookup_tables import Importance
        counts_dict = {}

        # Query to get importance counts
        importance_counts = (
            db.session.execute(
                select(Importance.importance, func.count(CmdbConfigurationItem.id).label('count'))
                .join(CmdbConfigurationItem, CmdbConfigurationItem.importance_id == Importance.id)
                .where(CmdbConfigurationItem.status != 'disposed')
                .group_by(Importance.importance)
            )
        ).all()

        # Populate the dictionary with results
        for importance_name, count in importance_counts:
            counts_dict[importance_name] = count

        # Add the 'All' count
        counts_dict['All'] = db.session.execute(
            select(func.count()).where(CmdbConfigurationItem.status != 'disposed')
        ).scalar()

        return counts_dict

    @classmethod
    def ticket_type_counts(cls):
        counts_dict = {}

        # Query to get ticket type counts
        ticket_type_counts = (
            db.session.execute(
                select(cls.ticket_type, func.count(cls.id).label('count'))
                .where(CmdbConfigurationItem.status != 'disposed')
                .group_by(cls.ticket_type)
            )
        ).all()

        # Populate the dictionary with results
        for ticket_type, count in ticket_type_counts:
            counts_dict[ticket_type] = count

        # Add the 'All' count
        counts_dict['All'] = db.session.execute(
            select(func.count()).where(CmdbConfigurationItem.status != 'disposed')
        ).scalar()

        return counts_dict

    def __eq__(self, other):
        if not isinstance(other, CmdbConfigurationItem):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f'<CmdbConfigurationItem id={self.id} name={self.name} ticket_type={self.ticket_type}>'


class CmdbHardware(CmdbConfigurationItem):
    __tablename__ = 'cmdb_hardware'
    id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('cmdb_configuration_item.id'), primary_key=True)
    asset_tag: Mapped[Optional[str]] = mapped_column(db.String(255), unique=True, nullable=True)
    capacity_cpu: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)  # e.g., 2, 4
    capacity_memory: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)  # e.g., 1GB, 2GB
    capacity_storage: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)  # e.g., CPU, RAM, Storage
    capacity_throughput: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)  # e.g., 100MB/s, 200MB/s
    fixed_ip_address: Mapped[Optional[str]] = mapped_column(db.String(45), nullable=True)  # IPv4/IPv6
    location: Mapped[Optional[str]] = mapped_column(db.String(255),
                                                    nullable=True)  # e.g., Data Center A, Data Center B (submenu)  # e.g., Data Center A
    mac_address: Mapped[Optional[str]] = mapped_column(db.String(17), nullable=True)  # MAC address format
    model: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    operating_system: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    purchase_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(db.String(255), unique=True, nullable=True)
    ssid: Mapped[Optional[str]] = mapped_column(db.String(150), nullable=True)

    vendor_warranty_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    warranty_expiration_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)

    upstream: Mapped[list['CmdbHardware']] = relationship(
        'CmdbHardware',
        secondary=cmdb_hardware_dependencies,
        primaryjoin=(id == cmdb_hardware_dependencies.c.parent_id),
        secondaryjoin=(id == cmdb_hardware_dependencies.c.child_id),
        back_populates='downstream',

    )

    downstream: Mapped[list['CmdbHardware']] = relationship(
        'CmdbHardware',
        secondary=cmdb_hardware_dependencies,
        primaryjoin=(id == cmdb_hardware_dependencies.c.child_id),
        secondaryjoin=(id == cmdb_hardware_dependencies.c.parent_id),
        back_populates='upstream',

    )

    # Relationship to software installed on hardware
    installed_software: Mapped[list['CmdbSoftware']] = relationship(
        'CmdbSoftware',
        secondary=cmdb_software_hardware,
        back_populates='upstream',

    )

    def get_downstream(self):
        return self.downstream

    def get_upstream(self):
        return self.upstream

    def get_vendor_warranty(self):
        from ..model.lookup_tables import VendorLookup
        if self.vendor_warranty_id:
            return db.session.execute(
                select(VendorLookup)
                .where(VendorLookup.id == self.vendor_warranty_id)
            ).scalars()
        else:
            return None

    __mapper_args__ = {
        'polymorphic_identity': 'cmdb_hardware',
        'inherit_condition': id == CmdbConfigurationItem.id
    }


class CmdbSoftware(CmdbConfigurationItem):
    __tablename__ = 'cmdb_software'
    id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('cmdb_configuration_item.id'), primary_key=True)
    hosted: Mapped[Optional[str]] = mapped_column(db.String(50),
                                                  nullable=True)
    host_name: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    licence_cost: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    licence_count: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    licence_expiration_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    licence_key: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    licence_type: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    maintenance_expires: Mapped[Optional[date]] = mapped_column(db.DateTime, nullable=True)
    maintenance_vendor: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    support_ends: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    supported_platforms: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    version: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)

    # Relationship to hardware where the software is installed
    upstream: Mapped[list['CmdbHardware']] = relationship(
        'CmdbHardware',
        secondary=cmdb_software_hardware,
        back_populates='installed_software',
    )

    def get_upstream(self):
        return self.upstream

    __mapper_args__ = {
        'polymorphic_identity': 'cmdb_software',
        'inherit_condition': id == CmdbConfigurationItem.id
    }


class CmdbService(CmdbConfigurationItem):
    __tablename__ = 'cmdb_service'
    id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('cmdb_configuration_item.id'), primary_key=True)
    sla: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)  # Service Level Agreement
    provider: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)  # Vendor or team responsible
    business_criticality: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)  # e.g., High, Medium, Low
    dependencies: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    interfaces: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    service_cost: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)

    components: Mapped[list['CmdbConfigurationItem']] = relationship(
        'CmdbConfigurationItem',
        secondary=cmdb_service_components,
        primaryjoin=(id == cmdb_service_components.c.service_id),
        secondaryjoin='CmdbConfigurationItem.id == cmdb_service_components.c.component_id',
        back_populates='services',
    )

    def get_related_cis(self):
        return self.components

    def get_hardware_components(self):
        return list(filter(lambda component: component.type == 'cmdb_hardware', self.components))

    def get_software_components(self):
        return list(filter(lambda component: component.type == 'cmdb_software', self.components))

    __mapper_args__ = {
        'polymorphic_identity': 'cmdb_service',
        'inherit_condition': id == CmdbConfigurationItem.id
    }

    def __init__(self, **kwargs):
        # Set default values for columns that need them
        # Ensure that values can be overwritten by kwargs
        super().__init__()
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc))
        self.ticket_type = kwargs.get('ticket_type', 'Service')

        for key, value in kwargs.items():
            setattr(self, key, value)


class OperatingSystem(db.Model):
    __tablename__ = 'operating_system'
    id: Mapped[int] = mapped_column(Identity(), primary_key=True, server_default=None)
    flavour: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    os: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)

    def __repr__(self):
        return f'{self.os}'


class ChangeFreeze(db.Model):
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)

    # relationships
    ci_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('cmdb_configuration_item.id'), nullable=True)
    ci: Mapped['CmdbConfigurationItem'] = relationship(
        'CmdbConfigurationItem',
        foreign_keys=[ci_id],
        back_populates='change_freezes',  # Update to match the new plural name
    )
