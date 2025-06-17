import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, UTC
from . import db
from flask_security import current_user
from .lookup_tables import PriorityLookup
from .model_category import Subcategory
from ..model.model_change import Change
from .model_problem import Problem

class CommonFieldsMixin:
    ticket_number: Mapped[int] = mapped_column(
        db.Integer,
        sa.Identity(start=1000, increment=1),
        unique=True,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    created_by: Mapped[str] = mapped_column(db.String(100), nullable=False)
    details: Mapped[str] = mapped_column(db.Text)
    last_updated: Mapped[datetime] = mapped_column(onupdate=lambda: datetime.now(UTC))
    resolved_at: Mapped[datetime] = mapped_column(nullable=True)
    short_desc: Mapped[str] = mapped_column(db.String(255))
    status: Mapped[str] = mapped_column(db.String(50))


def get_priority_counts(model, ticket_type, scope):
    # Ensure ticket_type matches the database format
    team_id = current_user.team_id
    # Base filters
    status_filter = model.status != 'closed'
    scope_filter = []

    # Apply scope-specific filters
    if scope == 'me':
        scope_filter.append(model.supporter_id == current_user.id)
    elif scope == 'portal':
        scope_filter.append(model.requester_id == current_user.id)
    elif scope == 'team':
        scope_filter.append(
            sa.and_(
                sa.or_(model.supporter_id.is_(None), model.supporter_id != current_user.id),
                model.support_team_id == team_id
            )
        )
    elif scope == 'cab':
        scope_filter.append(model.cab_ready)

    # Construct the query
    stmt = (
        sa.select(model.priority, sa.func.count())
        .where(sa.and_(model.ticket_type == ticket_type, status_filter, *scope_filter))
        .group_by(model.priority)
    )

    # Execute and fetch results
    priority_counts = db.session.execute(stmt).all()

    # Fetch priority labels in one query
    priority_labels = {
        p: p for p in db.session.execute(
            sa.select(PriorityLookup.priority)
            .where(PriorityLookup.priority.in_([p for p, _ in priority_counts]))
        ).scalars()
    }

    # Populate counts_dict
    counts_dict = {priority_labels.get(priority, priority): count for priority, count in priority_counts}

    # Query total count with the same filters
    total_count_stmt = (sa.select(sa.func.count())
                        .where(sa.and_(model.ticket_type == ticket_type, status_filter, *scope_filter))
                        )
    total_count = db.session.execute(total_count_stmt).scalar_one()

    # Add total count to the dictionary under 'All'
    counts_dict['All'] = total_count

    return counts_dict


def get_status_counts(model, scope=None):
    if not current_user.is_authenticated and scope == 'team':
        return {}  # Return empty if user is not authenticated and 'team' scope is selected

    # Initialize filters
    scope_filter = []

    # Apply scope-specific filters
    if scope == 'me':
        scope_filter.append(model.supporter_id == current_user.id)
    elif scope == 'portal':
        scope_filter.append(model.requester_id == current_user.id)
    elif scope == 'team':
        scope_filter.append(
            sa.and_(
                sa.or_(model.supporter_id != current_user.id, model.supporter_id.is_(None)),
                model.support_team_id == current_user.team_id
            )
        )
    elif scope == 'cab':
        scope_filter.append(sa.and_(model.status == 'cab'))
    else:  # Default case (e.g., 'all')
        scope_filter.append(model.status != 'closed')

    # Construct the query
    stmt = (
        sa.select(model.status, sa.func.count())
        .where(*scope_filter)
        .group_by(model.status)
    )

    # Execute the query and return results as a dictionary
    return {status: count for status, count in db.session.execute(stmt).all()}


def get_ticket_type_count(model, scope):
    # Common filters
    status_filter = model.status != 'closed'
    scope_filters = []

    # Apply scope-specific filters
    if scope == 'me':
        scope_filters.append(model.supporter_id == current_user.id)
    elif scope == 'team':
        scope_filters.append(
            sa.and_(
                sa.or_(model.supporter_id.is_(None), model.supporter_id != current_user.id),
                model.support_team_id == current_user.team_id
            )
        )
    elif scope == 'portal':
        scope_filters.append(model.requester_id == current_user.id)


    # Construct the base filter
    base_filter = sa.and_(*scope_filters, status_filter)

    # Fetch ticket type counts
    ticket_type_counts = db.session.execute(
        sa.select(model.ticket_type, sa.func.count()).where(base_filter).group_by(model.ticket_type)
    ).fetchall()

    # Initialize counts_dict only if model isn't Change
    counts_dict = {ticket_type: count for ticket_type, count in ticket_type_counts} if model not in [Change] else {}

    # Fetch total count and add to dictionary
    counts_dict['All'] = db.session.execute(
        sa.select(sa.func.count()).where(base_filter)
    ).scalar_one()

    return counts_dict



def get_subcats(category_id):
    """
    Used to populate choice= for subcategory.
    This is done by javascript for new tickets but needs this for existing.
    :param category_id:
    :return: list of tuples with subcategory id and name
    """
    subcategories = db.session.execute(
        sa.select(Subcategory)
        .where(Subcategory.category_id == category_id)
    ).scalars().all()

    result = [(subcategory.id, subcategory.name) for subcategory in subcategories]

    return sorted(result)
