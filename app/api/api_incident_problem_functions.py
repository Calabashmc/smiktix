from datetime import datetime, timezone

from flask import request, jsonify, g
from flask_login import login_required

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from . import api_bp
from ..common.BusinessHours import BusinessHoursCalculator
from ..common.common_utils import my_teams_dashboard
from ..common.exception_handler import log_exception

from ..model import db
from ..model.model_cmdb import CmdbConfigurationItem
from ..model.model_interaction import Ticket, TicketTemplate
from ..model.model_problem import Problem
from ..model.lookup_tables import PriorityLookup, StatusLookup, OfficeHours


def handle_interaction_params(stmt, params):
    """
    Handles filtering for the Ticket model based on 'params'.
    """
    # Fetch priorities, statuses, and teams as sets
    p_name = params['name']
    p_name = p_name.replace('\n', ' ')

    p_ticket_type = params['ticket_type']
    
    priorities = {
        priority.priority
        for priority in db.session.execute(
            sa.select(PriorityLookup)
        ).scalars()
    }

    statuses = [
        status.status for status in
        db.session.execute(
            sa.select(StatusLookup)
        ).scalars()
    ]

    # Apply filtering based on params
    interactions = {'Incident', 'Request'}
    problems = {'Problem', 'Known Error', 'Workaround'}
    
    if p_ticket_type in ['Interaction']:
        if p_name in statuses:
            return (stmt.where(Ticket.status == p_name), 
                    f'By status {p_name}')
        elif p_name in interactions:
            return (stmt.where(sa.and_(Ticket.ticket_type == p_name)), 
                    f'By type {p_name}')
        elif p_name in ['All']:
            return (stmt.where(sa.and_(Ticket.ticket_type.in_(interactions))), 
                    f'By type {p_name}')

    elif p_ticket_type in interactions:
        if p_name in priorities:
            return (stmt.where(sa.and_(Ticket.priority == p_name, Ticket.ticket_type == p_ticket_type)), 
                    f'By priority {p_name}')
        elif p_name in ['All']:
            return (stmt.where(sa.and_(Ticket.ticket_type == p_ticket_type)), 
                    f'By type {p_name}')
        elif p_name in statuses:
            return (stmt.where(Ticket.status == p_name), 
                    f'By status {p_name}')

    elif p_ticket_type in problems:
        if p_name in priorities:
            return (stmt.where(Problem.priority == p_name), 
                    f'By priority {p_name}')
        elif p_name in statuses:
            return (stmt.where(Problem.status == p_name), 
                    f'By status {p_name}')
        elif p_name in ['All']:
            return (stmt.where(Problem.ticket_type.in_(problems)),
                    f'By type {p_name}')
        elif p_name in problems:
            return (stmt.where(Problem.ticket_type == p_name),
                    f'By type {p_name}')

    return stmt, 'No filtering applied'

@api_bp.post('/check-for-children/')
@login_required
def check_for_children():
    data = request.get_json(silent=True)
    if not data:
        raise ValueError('Invalid JSON data or incorrect Content-Type header')

    ticket = db.session.execute(
        sa.select(Ticket)
        .where(Ticket.ticket_number == data['ticket-number'])
    ).scalar_one_or_none()

    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    child_count = db.session.execute(
        sa.select(sa.func.count(Ticket.id))
        .select_from(Ticket)
        .where(Ticket.parent_id == ticket.id)
    ).scalar()

    return jsonify({'children': child_count}), 200


@api_bp.get('/interaction/get-incident-ticket/')
@login_required
def get_incident_ticket():
    ticket_number = request.args.get('ticket-number')
    ticket = db.session.execute(
        sa.select(Ticket)
        .options(joinedload(Ticket.category),
                 joinedload(Ticket.support_team),
                 joinedload(Ticket.requester),
                 joinedload(Ticket.supporter))
        .where(sa.and_(Ticket.ticket_number == ticket_number))
    ).scalar_one_or_none()

    if not ticket:
        return jsonify({'error': 'Incident Ticket not found'})

        # Helper function to format date-time fields

    def format_datetime(dt):
        return dt.strftime(g.datetime_format) if dt else ''

    result = {
        'category': ticket.category.name if ticket.category else '',
        'created-at': ticket.created_at.strftime(g.datetime_format),
        'created-by': format_datetime(ticket.created_at),
        'details': ticket.details,
        'is-major': ticket.is_major,
        'last-updated': format_datetime(ticket.last_updated_at),
        'priority': ticket.priority,
        'priority-impact': ticket.priority_impact,
        'priority-urgency': ticket.priority_urgency,
        'respond-by': format_datetime(ticket.sla_respond_by),
        'resolve-by': format_datetime(ticket.sla_resolve_by),
        'requested-by': ticket.get_requester_name(),
        'support-agent': ticket.get_supporter_name(),
        'short-desc': ticket.short_desc,
        'status-select': ticket.status,
        'support-team': ticket.get_support_team_name(),
        'ticket-number': ticket.ticket_number,
        'ticket-type': ticket.ticket_type,
        'updated_at': format_datetime(ticket.last_updated_at) or format_datetime(ticket.created_at),
    }

    return jsonify(result)


@api_bp.get('/get-problem-ticket/')
@login_required
def get_problem_ticket():
    ticket_number = request.args.get('ticket-number')
    problem = db.session.execute(
        sa.select(Problem)
        .where(sa.and_(Problem.ticket_number == ticket_number))
    ).scalar_one_or_none()

    if not problem:
        return jsonify({'error': 'Problem Ticket not found'})

        # Helper function to format date-time fields

    def format_datetime(dt):
        return dt.strftime('%Y-%m-%dT%H:%M') if dt else ''

    child_tickets_data = [
        {
            'ticket_number': ticket.ticket_number,
            'ticket-type': ticket.ticket_type,
            'short_desc': ticket.short_desc,
            'status': ticket.status,
            'requested_by': ticket.requester.full_name if ticket.requester else '',
            'supported_by': ticket.supporter.full_name if ticket.supporter else 'Unassigned',
            'support_team': ticket.support_team.name if ticket.support_team else '',
            'priority': ticket.priority,
            'created_at': format_datetime(ticket.created_at),
            'last_updated_at': format_datetime(ticket.last_updated_at),
        }
        for ticket in problem.child_tickets
    ]

    result = {
        'category': problem.category.name if problem.category else '',
        'created-at': problem.created_at,
        'created-by': problem.created_by_id,
        'details': problem.details,
        'last-updated': problem.last_updated_at,
        'priority': problem.priority,
        'requested-by': problem.get_requester_name(),
        'support-agent': problem.get_supporter_name(),
        'short-desc': problem.short_desc,
        'status-select': problem.status,
        'support_team': problem.support_team.name if problem.support_team else '',
        'ticket-number': problem.ticket_number,
        'ticket-type': problem.ticket_type,
        'updated_at': format_datetime(problem.last_updated_at) or format_datetime(problem.created_at),
        'child_tickets': child_tickets_data,
    }

    return jsonify(result)

@api_bp.post('/interaction/outage-calc/')
@login_required
def outage_calc():
    # Parse JSON input
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400
    # Validate required fields
    required_fields = ['outage_start', 'outage_end', 'priority']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({'error': f"Missing required fields: {', '.join(missing_fields)}"}), 400

    try:
        # Parse dates
        date_format = '%Y-%m-%d %H:%M'  # ISO format
        outage_start = datetime.strptime(data['outage_start'], date_format)
        outage_end = datetime.strptime(data['outage_end'], date_format)

        if outage_end < outage_start:
            return jsonify({'error': 'Outage end time must be after outage start time'}), 400

        # Calculate total outage time in 'hh:mm' format
        total_seconds = int((outage_end - outage_start).total_seconds())
        total_time = f'{total_seconds // 3600:02d}:{(total_seconds % 3600) // 60:02d}'

        # Fetch priority and determine business hours
        priority = db.session.execute(
            sa.select(PriorityLookup)
            .where(PriorityLookup.priority == data['priority'])
        ).scalars().one_or_none()

        if not priority:
            log_exception(f'Invalid priority value')
            return jsonify({'error': 'Invalid priority value'}), 400

        office_hours = db.session.execute(
            sa.select(OfficeHours)
        ).scalars().one_or_none()

        if not office_hours:
            log_exception(f'Office hours configuration not found')
            return jsonify({'error': 'Office hours configuration not found'}), 500

        if priority.twentyfour_seven:
            open_time = '00:00'
            close_time = '23:59'
            open_at = datetime.strptime(open_time, '%H:%M').time()
            close_at = datetime.strptime(close_time, '%H:%M').time()
            business_hours = [open_at, close_at]
        else:
            business_hours = [office_hours.open_hour, office_hours.close_hour]

        country_code = office_hours.country_code
        time_zone = office_hours.timezone
        state = office_hours.state

        # Calculate SLA outage time
        outage_time = BusinessHoursCalculator(outage_start, outage_end, business_hours, country_code, time_zone, state)
        sla_minutes = outage_time.get_minutes()
        sla_time = f'{round(sla_minutes) // 60:02d}:{round(sla_minutes) % 60:02d}'

        # Return results
        return jsonify({'total_time': total_time, 'sla_time': sla_time}), 200

    except (ValueError, KeyError) as e:
        log_exception(f'Value or Key error: {e}')
        return jsonify({'error': f'Invalid data: {str(e)}'}), 400

    except SQLAlchemyError as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@api_bp.post('/interaction/set-interaction-ticket/')
@login_required
def update_interaction_ticket():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    impact = data.get('impact')
    is_major = data.get('is_major')
    outage = data.get('outage')
    outage_duration_total = data.get('outage_duration_total')
    outage_duration_sla = data.get('outage_duration_sla')
    outage_end = data.get('outage_end') or None
    outage_start = data.get('outage_start') or None
    priority = data.get('priority')
    ticket_number = data.get('ticket_number')
    urgency = data.get('urgency')

    ticket = db.session.execute(
        sa.select(Ticket)
        .where(Ticket.ticket_number == ticket_number)
    ).scalar_one_or_none()

    if ticket:
        # Updating the ticket
        ticket.outage = outage
        ticket.outage_end = outage_end
        ticket.outage_start = outage_start
        ticket.outage_duration_sla = outage_duration_sla
        ticket.outage_duration_total = outage_duration_total
        ticket.priority = priority
        ticket.is_major = is_major
        ticket.impact = impact
        ticket.urgency = urgency

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            log_exception(f'Database error: {e}')
            return jsonify({'error': 'Database error: ' + str(e)}), 500
        return jsonify(), 200
    else:
        return jsonify({'error': 'Invalid JSON data: '}), 500


@api_bp.post('/interaction/set-rapid-resolution/')
@login_required
def set_rapid_resolution():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    resolution_id = data.get('resolution-id')

    rapid_resolution = db.session.execute(
        sa.select(TicketTemplate)
        .where(TicketTemplate.id == resolution_id)
    ).scalars().one_or_none()

    if not rapid_resolution:
        return jsonify({'error': 'Rapid Resolution not found'}), 404

    response = {
        'category_id': rapid_resolution.category_id,
        'details': rapid_resolution.details,
        'priority': f'P{rapid_resolution.priority_id}',
        'priority_impact': rapid_resolution.priority_impact,
        'priority_urgency': rapid_resolution.priority_urgency,
        'resolution_code_id': rapid_resolution.resolution_code_id,
        'short_description': rapid_resolution.short_description,
        'source_id': rapid_resolution.source_id,
        'subcategory_id': rapid_resolution.subcategory_id,
        'support_team_id': rapid_resolution.support_team_id,
        'ticket_type': rapid_resolution.ticket_type
    }

    return jsonify(response), 200


@api_bp.post('/set-as-parent/')
@login_required
def set_as_parent():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    ticket_number = data.get('ticket-number')

    ticket = db.session.execute(
        sa.select(Ticket)
        .where(Ticket.ticket_number == ticket_number)
    ).scalars().one_or_none()

    ticket.parent_id = None
    ticket.is_parent = True
    ticket.last_updated = datetime.now(timezone.utc)

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500
    return jsonify({'status': 'success'}), 200


@api_bp.post('/set-parent-id/')
@login_required
def set_parent_id():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    ticket_number = data.get('ticket-number')
    parent_id = data.get('parent-id')

    ticket = db.session.execute(
        sa.select(Ticket)
        .where(Ticket.ticket_number == ticket_number)
    ).scalars().one_or_none()

    ticket.parent_id = parent_id
    ticket.last_updated = datetime.now(timezone.utc)

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500
    return jsonify({'status': 'success'}), 200


@api_bp.post('/problem/tickets/')
@login_required
def problem_tickets():
    page = request.args.get('page', 1, type=int)  # for pagination of table
    page_team = request.args.get('team', 'any')
    ticket_type = request.args.get('ticket-type').lower()

    ticket_query = my_teams_dashboard(Problem, page, page_team, ticket_type)
    tickets = []
    for item in ticket_query:
        tickets.append(
            {
                'ticket_number': f"<a class='text-primary fw-bold' href='/ui/problem/?ticket={item.ticket_number}'>{item.ticket_number}</a>",
                'ticket-type': item.ticket_type,
                'priority': item.priority.priority,
                'supporter': item.supporter.full_name,
                'sort_desc': item.short_desc,
                'created_at': item.created_at.strftime('%b %d %Y %H:%M'),
            }
        )
    return jsonify(
        {
            'table_tickets': tickets,
            'page': ticket_query.page,
            'per_page': ticket_query.per_page,
            'total': ticket_query.total,
            'first': ticket_query.first,
            'last': ticket_query.last,
            'pages': ticket_query.pages,
            'has_prev': ticket_query.has_prev,
            'prev_num': ticket_query.prev_num,
            'has_next': ticket_query.has_next,
            'next_num': ticket_query.next_num,
        }
    )


@api_bp.post('/interaction/get-ci-importance/')
@login_required
def get_ci_importance():
    data = request.get_json(silent=True)
    ci_id = data.get('ci_id')

    if ci_id is None:
        log_exception(f'Invalid JSON data or incorrect Content-Type header')
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    ci = db.session.execute(
        sa.select(CmdbConfigurationItem)
        .where(CmdbConfigurationItem.id == ci_id)
    ).scalars().one_or_none()

    if not ci:
        return jsonify({'error': 'CI not found'}), 404

    importance = {
        'Platinum': {'priority': 'P1', 'impact': 'High', 'urgency': 'High'},
        'Gold': {'priority': 'P2', 'impact': 'High', 'urgency': 'Medium'},
        'Silver': {'priority': 'P3', 'impact': 'Medium', 'urgency': 'Medium'},
        'Bronze': {'priority': 'P4', 'impact': 'Low', 'urgency': 'Medium'},
        'Tin': {'priority': 'P5', 'impact': 'Low', 'urgency': 'Low'},
        'Rust': {'priority': 'P5', 'impact': 'Low', 'urgency': 'Low'}
    }
    response = importance.get(ci.importance.importance, 'P5')

    return jsonify(response), 200


@api_bp.post('/problem/set-problem-priority/')
@login_required
def save_problem_priority():
    """
    Endpoint for setting SLA priority for a Problem ticket from problem-priority-button-class.js
    Interaction and Change deal with priority differently so each is handled separately
    :return: JSON status
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    priority = data.get('priority')
    ticket_number = data.get('ticket_number')

    if not ticket_number:
        return jsonify({'error': 'Missing ticket number'}), 400

    ticket = db.session.execute(
        sa.select(Problem)
        .where(Problem.ticket_number == ticket_number)
    ).scalars().first()

    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    ticket.priority = priority

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500
    return jsonify({'status': 'success'}), 200


@api_bp.post('/interaction/get-ticket-stats/')
@login_required
def get_ticket_stats():
    response = Ticket.get_ticket_stats()
    return jsonify(response)