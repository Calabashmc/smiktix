from __future__ import annotations
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:  # only used for type hinting so no circular import issues
    from .model_knowledge import KnowledgeBase
    from .lookup_tables import ModelLookup
    from .model_release import Release

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db
from .model_change import Change
from .model_cmdb import CmdbConfigurationItem
from .model_idea import Idea
from .model_interaction import Ticket
from .model_problem import Problem
from .relationship_tables import category_model


class Category(db.Model):
    __tablename__ = 'category'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    comment: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    name: Mapped[str] = mapped_column(db.String(50), nullable=False, unique=True)

    change_category: Mapped['Change'] = relationship(
        'Change',
        foreign_keys='Change.category_id',
        back_populates='category',
        lazy='select'
    )

    configuration_items: Mapped['CmdbConfigurationItem'] = relationship(
        'CmdbConfigurationItem',
        back_populates='category'
    )

    idea_category: Mapped['Idea'] = relationship(
        'Idea',
        foreign_keys='Idea.category_id',
        back_populates='category'
    )

    knowledge_category: Mapped['KnowledgeBase'] = relationship(
        'KnowledgeBase',
        foreign_keys='KnowledgeBase.category_id',
        back_populates='category'
    )

    model: Mapped['ModelLookup'] = relationship(
        'ModelLookup',
        secondary=lambda: category_model,
        back_populates='categories',
    )

    problem_category: Mapped['Problem'] = relationship(
        'Problem',
        foreign_keys='Problem.category_id',
        back_populates='category'
    )

    release_category: Mapped['Release'] = relationship(
        'Release',
        foreign_keys='Release.category_id',
        back_populates='category'
    )

    subcategories: Mapped['Subcategory'] = relationship(
        'Subcategory',
        back_populates='category',
        cascade='all, delete-orphan'
    )

    ticket_category: Mapped['Ticket'] = relationship(
        'Ticket',
        foreign_keys='Ticket.category_id',
        back_populates='category'
    )

    def __eq__(self, other):
        return self.name == other

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f'{self.name}'



class Subcategory(db.Model):
    __tablename__ = 'subcategory'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(db.String(50))
    ticket_type: Mapped[str] = mapped_column(db.String(15))

    # Define the many-to-one relationship with Category
    category_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category: Mapped['Category'] = relationship(
        'Category',
        foreign_keys=[category_id],
        back_populates='subcategories'
    )

    ticket_subcategory: Mapped['Ticket'] = relationship(
        'Ticket',
        foreign_keys='Ticket.subcategory_id',
        back_populates='subcategory'
    )

    problem_subcategory: Mapped['Problem'] = relationship(
        'Problem', foreign_keys='Problem.subcategory_id',
        back_populates='subcategory'
    )

    def __repr__(self):
        return f'{self.name}'
