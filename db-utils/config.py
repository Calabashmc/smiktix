# config.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

db_uri = 'postgresql://postgres:Melenkurian.321@localhost/sm4sb'
engine = create_engine(db_uri)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class Ticket(Base):
    __tablename__ = 'ticket'
    id = Column(Integer, primary_key=True)
    ticket_number = Column(Integer)
    status = Column(String(15))
    sla_paused = Column(Boolean)
    sla_respond_by = Column(DateTime, nullable=True)
    sla_resolve_by = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    notes = relationship('Notes', back_populates='ticket', lazy=True)

    parent_id = Column(Integer, ForeignKey('ticket.id'), nullable=True)
    parent = relationship(
        'Ticket',
        remote_side=[id],
        foreign_keys=[parent_id],
        backref='ticket_parent',
        uselist=False
    )

    problem_id = Column(Integer, ForeignKey("problem.id"), nullable=True)
    problem = relationship(
        "Problem",
        back_populates="child_tickets",
        uselist=False,
        foreign_keys=[problem_id]
    )

    resolution_code_id = Column(Integer, ForeignKey('resolution_codes.id'), nullable=True)
    resolution_code = relationship(
        'ResolutionCodes',
        foreign_keys=[resolution_code_id],
        back_populates='ticket_resolution'
    )
    resolution_notes = Column(Text)


class Problem(Base):
    __tablename__ = "problem"
    id = Column(Integer, primary_key=True)
    ticket_number = Column(Integer)
    type = Column(String(15))
    status = Column(String(15))

    notes = relationship('Notes', back_populates='problem', lazy=True)

    last_updated_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    resolution_notes = Column(Text)
    resolution_code_id = Column(Integer, ForeignKey("resolution_codes.id"), nullable=True)

    resolution_code = relationship("ResolutionCodes", foreign_keys=[resolution_code_id],
                                   back_populates="problem_resolution",
                                   )

    child_tickets = relationship("Ticket", back_populates="problem")

    def __repr__(self):
        return f"{self.ticket_number}"


class Notes(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True)
    ticket_type = Column(String)
    ticket_number = Column(Integer)
    note = Column(Text)
    noted_by = Column(String)
    note_date = Column(DateTime)

    ticket_id = Column(Integer, ForeignKey("ticket.id"), nullable=True)
    ticket = relationship(
        "Ticket", foreign_keys=[ticket_id], back_populates="notes"
    )
    problem_id = Column(Integer, ForeignKey('problem.id'), nullable=True)
    problem = relationship(
        "Problem", foreign_keys=[problem_id], back_populates="notes"
    )
    # change_id = Column(Integer, ForeignKey('change.id'), nullable=True)
    # change = relationship(
    #     "Change", foreign_keys=[change_id], back_populates="notes"
    # )


class ResolutionCodes(Base):
    __tablename__ = 'resolution_codes'
    id = Column(Integer, primary_key=True)
    ticket_resolution = relationship('Ticket', back_populates='resolution_code')
    problem_resolution = relationship("Problem", foreign_keys="Problem.resolution_code_id",
                                      back_populates="resolution_code",
                                      )
