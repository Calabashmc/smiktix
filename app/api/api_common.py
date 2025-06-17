import pytz
from flask import g, current_app, jsonify
from flask_login import current_user
import sqlalchemy as sa
from ..model import db
from ..model.model_change import Change
from ..model.model_cmdb import CmdbConfigurationItem
from ..model.model_idea import Idea
from ..model.model_knowledge import KnowledgeBase
from ..model.model_interaction import Ticket
from ..model.model_release import Release
from ..model.model_user import Team, User
from ..common.ticket_utils import format_time


def apply_filters(model, stmt, filters):
    if not filters:
        return stmt, 'No filters provided'

    filter_by = filters[0]
    field = filter_by.get('field', '').strip().lower()
    value = filter_by.get('value')

    match field:
        case 'article_type':
            return stmt.where(model.article_type == value), f'Article type: "{value}"'

        case 'author':
            return stmt.join(model.author).filter(
                User.full_name.ilike(f'{value}%')), f'Author: "{value}"'

        case 'email':
            return stmt.where(model.email.ilike(f'{value}%')), f'Email: "{value}"'

        case 'full_name':
            return stmt.where(model.full_name.ilike(f'{value}%')), f'Full name: "{value}"'

        case 'requested_by' | 'owned_by':
            return stmt.join(model.requester).where(
                User.full_name.ilike(f'{value}%')), f'Requester: "{value}"'

        case 'supported_by':
            return stmt.join(model.supporter).where(
                User.full_name.ilike(f'{value}%')), f'Supporter: "{value}"'

        case 'support_team':
            return stmt.join(model.support_team).where(
                Team.name.ilike(f'{value}%')), f'Team: "{value}"'

        case 'ticket_number':
            return stmt.filter(
                sa.cast(model.ticket_number, sa.String).like(f'{value}%')), f'Ticket #: "{value}"'

        case 'phone':
            return stmt.where(model.phone.ilike(f'{value}%')), f'Phone: "{value}"'

        case 'name':
            return stmt.where(model.name.ilike(f'{value}%')), f'Name: "{value}"'

        case _:
            return stmt, f'Unrecognized filter field: "{field}"'


def create_ticket_response(ticket, model, user_timezone):
    """
    Creates a dictionary response for a ticket based on its model. The response is used by table.js
    The field names match the table column names defined there.

    Args:
        ticket: The ticket object.
        model: The model class of the ticket.
        user_timezone: The user's timezone.

    Returns:
        A dictionary containing the ticket's information.
    """
    response = {}

    # common fields for all models except User
    if hasattr(ticket, 'ticket_number'):
        response.update({
            'ticket_number': ticket.ticket_number,
            'ticket_type': ticket.ticket_type,
            'status': ticket.status,
            'created': format_time(ticket.created_at, user_timezone),
        })

    # Common fields for all models except Cmdb, KnowledgeBase, and User
    if hasattr(ticket, 'get_requester_name'):
        response.update({
            'requested_by': ticket.get_requester_name(),
            'shortDesc': ticket.short_desc
        })

    # Fields specific to Ticket and Problem models
    if hasattr(ticket, 'priority'):
        response['priority'] = ticket.priority

    # Fields specific to Ticket, Problem, and Change models
    if hasattr(ticket, 'get_supporter_name'):
        response['supported_by'] = ticket.get_supporter_name() or 'Unassigned'

    if model == Ticket:
        response.update({
            'respond_by': format_time(ticket.sla_respond_by, user_timezone) if ticket.sla_respond_by else None,
            'resolve_by': format_time(ticket.sla_resolve_by, user_timezone) if ticket.sla_resolve_by else None,
            'sla_response_breach': ticket.sla_response_breach,
            'sla_resolve_breach': ticket.sla_resolve_breach,
            'support_team': ticket.get_support_team_name() if ticket.support_team else None,
        })
    elif model == Idea:
        response.update({
            'likelihood': ticket.likelihood,
            'votes': ticket.vote_count,
            'score': ticket.vote_score,
            'category': ticket.category.name if ticket.category else 'not specified',
        })
    elif model == Change:
        response.update({
            'cab_approval_status': ticket.cab_approval_status,
            'change_type': ticket.change_type,
            'risk': ticket.risk_set,
            'start_date': ticket.start_date.strftime(g.date_format),
            'start_at': ticket.start_time.strftime('%H:%M') if ticket.start_time else None,
            'end_at': ticket.end_time.strftime('%H:%M') if ticket.end_time else None,
        })
    elif model == KnowledgeBase:
        response.update({
            'author': ticket.get_author_name(),
            'title': ticket.get_title(),
            'article_category': ticket.category.name if ticket.category else 'not specified',
            'article_type': ticket.get_article_type(),
            'short_desc': ticket.short_desc,
            'times_viewed': ticket.get_times_viewed(),
            'times_useful': ticket.get_times_useful(),
        })
    elif model == User:
        response.update({
            'id': ticket.id,
            'full_name': ticket.full_name,
            'occupation': ticket.occupation or 'not specified',
            'last_login_at': ticket.last_login_at,
            'current_login_ip': ticket.current_login_ip,
            'phone': ticket.phone,
            'email': ticket.email,
            'department': ticket.get_department(),
            'manager': ticket.manager.full_name if ticket.manager else 'not specified',
            'team': ticket.team.name if ticket.team else 'not specified',
            'active': ticket.active,
            'role': [role.name for role in ticket.roles],
        })
    elif model == CmdbConfigurationItem:
        response.update({
            'name': ticket.name,
            'category': ticket.category.name if ticket.category else 'not specified',
            'ticket_type': ticket.ticket_type,
            'owned_by': ticket.get_requester_name(),
            'support_team': ticket.get_support_team(),
        })
    elif model == Release:
        response.update({
            'release_type': ticket.release_type.release_type,
            'support_team': ticket.get_support_team_name(),
            'release_name': ticket.get_release_name()
        })

    return response


def get_paginated_results(model, data, handle_params_func):
    """
    Generic function to handle paginated results and dynamic filtering for any model.

    Args:
        model: SQLAlchemy model to stmt.
        data: The request data containing parameters for pagination and filtering.
        handle_params_func: Function to handle model-specific 'params' logic.

    Returns:
        A paginated JSON response.
    """
    # data = request_data
    page = data.get('page', 1)  # Default to page 1
    per_page = data.get('size', current_app.config['ROWS_PER_PAGE'])
    scope = data.get('scope')

    user_timezone = pytz.timezone(data.get('timezone', 'UTC'))  # Default to UTC if not provided

    # Handle model-specific params
    params = data.get('params')
    if model == User:
        stmt = sa.select(model).order_by(model.last_name.asc())
    else:
        stmt = sa.select(model).order_by(model.ticket_number.asc())

    if hasattr(model, 'status'):
        # All Open tickets (including Resolved)
        stmt = stmt.where(sa.and_(model.status != 'closed'))

    filter_description = None

    # Scope-based filtering
    if scope:
        if scope == 'me':
            stmt = stmt.where(sa.and_(model.supporter == current_user))
        elif scope == 'portal':
            if hasattr(model, 'requester_id'):
                stmt = stmt.where(sa.and_(model.requester_id == current_user.id))
        elif scope == 'team':
            stmt = stmt.where(sa.and_(sa.or_(model.supporter_id.is_(None), model.supporter != current_user),
                                      model.support_team == current_user.team))
        elif scope == 'cab':
            stmt = stmt.where(model.status == 'cab')
        elif scope == 'top':
            stmt = KnowledgeBase.get_top_useful_records(10)  # limit to 10
        elif scope == 'published':
            stmt = KnowledgeBase.get_published_articles()
        elif scope == 'votable':
            stmt = stmt.where(model.status == 'voting')

    if params:
        stmt, filter_description = handle_params_func(stmt, params)

    # Apply additional filters
    filters = data.get('filter', [])
    if filters:
        stmt, filter_description = apply_filters(model, stmt, filters)
    # Paginate results
    paginated_items = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
    items = paginated_items.items
    # Build response
    response = {
        'filter_description': filter_description,
        'last_page': paginated_items.pages,
        'last_row': paginated_items.total,
        'data': [create_ticket_response(item, model, user_timezone) for item in items],
    }
    return jsonify(response)
