from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from typing import Optional
from . import db


class CommsJournal(db.Model):
    __tablename__ = 'comms_journal'
    id: Mapped[int] = mapped_column(db.Integer, sa.Identity(), primary_key=True)

    subject: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    timestamp: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)

    ticket_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('ticket.id'), nullable=True)
    ticket: Mapped['Ticket'] = relationship(
        'Ticket',
        back_populates='comms_journal'
    )

    problem_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('problem.id'), nullable=True)
    problem: Mapped['Problem'] = relationship(
        'Problem',
        back_populates='comms_journal'
    )

    def __repr__(self):
        return f'{self.subject}, {self.message}, {self.timestamp}'


class Notes(db.Model):
    __tablename__ = 'notes'

    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    note: Mapped[str] = mapped_column(db.Text)
    noted_by: Mapped[str] = mapped_column(db.String)
    note_date: Mapped[datetime] = mapped_column(db.DateTime(timezone=True))
    ticket_type: Mapped[str] = mapped_column(db.String)
    ticket_number: Mapped[int] = mapped_column(db.Integer)  # of the associated ticket

    # relationships
    idea_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('idea.id', ondelete='CASCADE'), nullable=True)
    idea: Mapped['Idea'] = relationship(
        'Idea',
        foreign_keys=[idea_id],
        back_populates='notes'
    )

    change_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('change.id', ondelete='CASCADE'), nullable=True)
    change: Mapped['Change'] = relationship(
        'Change',
        foreign_keys=[change_id],
        back_populates='notes'
    )

    cmdb_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('cmdb_configuration_item.id', ondelete='CASCADE'), nullable=True)
    cmdb: Mapped['CmdbConfigurationItem'] = relationship(
        'CmdbConfigurationItem',
        foreign_keys=[cmdb_id],
        back_populates='notes'
    )

    knowledgebase_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('knowledgebase.id', ondelete='CASCADE'), nullable=True)
    knowledgebase: Mapped['KnowledgeBase'] = relationship(
        'KnowledgeBase',
        foreign_keys=[knowledgebase_id],
        back_populates='notes'
    )

    problem_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('problem.id', ondelete='CASCADE'), nullable=True)
    problem: Mapped['Problem'] = relationship(
        'Problem',
        foreign_keys=[problem_id],
        back_populates='notes'
    )

    release_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('release.id', ondelete='CASCADE'), nullable=True)
    release: Mapped['Release'] = relationship(
        'Release',
        foreign_keys=[release_id],
        back_populates='notes'
    )

    ticket_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('ticket.id', ondelete='CASCADE'), nullable=True)
    ticket: Mapped['Ticket'] = relationship(
        'Ticket',
        foreign_keys=[ticket_id],
        back_populates='notes'
    )
    # Fields with default values
    is_system: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)


