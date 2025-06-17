import os
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from unittest.mock import DEFAULT

import pytz
from flask import (
    g,
    request,
    jsonify,
    current_app,
    session,
    render_template,
    url_for
)
from flask_mailing import Mail, Message
from flask_security import current_user, login_required
from jinja2.filters import Markup
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

from . import api_bp
from .api_common import apply_filters, create_ticket_response, get_paginated_results
from .api_cmdb_functions import handle_cmdb_params
from .api_idea_functions import handle_idea_params
from .api_incident_problem_functions import handle_interaction_params
from .api_knowledge_functions import handle_knowledge_params
from .api_release_functions import handle_release_params
from .api_people_functions import handle_user_params
from ..model import db
from ..model.model_user import Team, User
from ..model.model_category import Category, Subcategory
from ..model.model_change import Change
from ..model.model_idea import Idea
from ..model.model_knowledge import KnowledgeBase
from ..model.model_interaction import Ticket
from ..model.model_notes import Notes
from ..model.model_portal import PortalAnnouncements
from ..model.model_problem import Problem
from ..model.model_release import Release
from ..model.model_user import Department, User
from ..model.lookup_tables import (
    OfficeHours,
    PriorityLookup,
    VendorLookup, ResolutionLookup,
)

from ..common.sla import calculate_sla_times
from ..common.common_utils import (
    get_highest_ticket_number,
    my_teams,
    my_teams_dashboard,
    get_model,
    run_async_in_thread,
    send_notification
)
from ..model.common_methods import get_priority_counts, get_status_counts, get_subcats, get_ticket_type_count
from ..common.BusinessHours import BusinessHoursCalculator
from ..common.ticket_utils import add_journal_notes, get_child_tickets
from ..views.admin.form import AdminUserForm
from ..views.change.change_utils import handle_change_params

mail = Mail()


@api_bp.get('/get_subcategory/')
@login_required
def get_subcategory():
    '''
    Called by javascript on change of category SelectField. Queries database for all
    subcategories of the selected category
    :return: json 'sub_categories' with list of all related sub-cats from database
    '''
    category = request.args.get('category')
    result = get_subcats(category)
    return jsonify({'subcategories': result})


@api_bp.get('/get-vendor-details/')
@login_required
def get_vendor_details():
    '''
    Endpoint for user-details-populate.js jquery.
    Fills phone, department, and email based on the user selected from the QuerySelectField
    :return: json of user record
    '''
    vendor_id = request.args.get('id', type=int)

    # this is needed as the javascript returns __None on first load due to blank field
    # which causes a postgresql error as expecting an integer for User.id
    if vendor_id:
        vendor = db.session.execute(
            sa.select(VendorLookup)
            .where(VendorLookup.id == vendor_id)
        ).scalars().first()

        data = {
            'contact': vendor.contact_name if vendor.contact_name else 'Unknown',
            'email': vendor.contact_email if vendor.contact_email else 'none',
            'phone': vendor.contact_phone if vendor.contact_phone else 'none',
        }
    else:
        data = {
            'contact': 'Unknown',
            'phone': 'phone',
            'email': 'email',
        }
    return jsonify(data)


@api_bp.get('/get-ticket-type/')
@login_required
def get_type():
    '''
    API end point called from javascript on change of subcategory.
    Used to tag a ticket as an Incident or Request (future: problem/Change?)
    using information from sub-category database
    :return: json 'type': 'Incident' or 'type': 'Request'
    '''
    subcat = request.args.get('subcat')

    if not subcat:
        return jsonify({'error', 'URL error, need to include subcat'}), 400

    try:
        ticket_type = db.session.execute(
            sa.select(Subcategory.ticket_type)
            .where(Subcategory.id == subcat)
        ).scalars().first()
    except SQLAlchemyError as e:
        return jsonify({'error', f'Database error {str(e)}'})

    return jsonify({'ticket-type': ticket_type})


@api_bp.post('/set-type/')
@login_required
def set_type():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    problem = db.session.execute(
        sa.select(Problem)
        .where(Problem.ticket_number == data['ticket-number'])
    ).scalars().first()

    problem.ticket_type = data['ticket-type']

    try:
        db.session.commit()
        return jsonify({'success': 'Ticket type updated'}), 200
    except SQLAlchemyError as e:
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500


@api_bp.get('/check_ticket_number/')
@login_required
def check_ticket_number():
    """
    Checks if the entered ticket number exists in the database.

    :return: JSON response with 'isvalid' ('valid' or 'invalid') and highest existing ticket number.
    """
    ticket_number = request.args.get('ticket')
    model = get_model(request.args.get('model'))

    # Validate the model
    if model is None:
        return jsonify({'error': 'Invalid model'}), 400

    # Validate and convert ticket_number
    if not ticket_number or not ticket_number.isdigit():
        return jsonify({'isvalid': 'invalid', 'error': 'Invalid ticket number'}), 400

    ticket_number = int(ticket_number)

    ticket = db.session.execute(
        sa.select(model).where(model.ticket_number == ticket_number)
    ).scalars().first()

    if ticket:
        return jsonify({'isvalid': 'valid'})

    highest_number = get_highest_ticket_number(model) or 0
    return jsonify({'isvalid': 'invalid', 'highest_number': max(0, highest_number - 1)})



@api_bp.post('/get-children/')
@login_required
def get_children():
    """
    Used to populate child-ticket table. Called from children-class.js
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    page = data.get('page', 1)
    per_page = data.get('size', 10)

    user_timezone = pytz.timezone(data.get('timezone'))
    parent_ticket_number = data['parent_ticket_number']
    parent_type = data['parent_type']  # Parent is Ticket, Problem, or Change

    parent_model = get_model(parent_type)  # in common_utils

    ticket_data = []
    problem_data = []
    release_data = []
    total_tickets = 0
    total_problems = 0
    total_releases = 0

    parent_ticket = db.session.execute(
        sa.select(parent_model)
        .where(parent_model.ticket_number == parent_ticket_number)
    ).scalar_one_or_none()

    if parent_ticket is None:
        return jsonify({'error': f'{parent_type} {parent_ticket_number} not found'}), 404

    # Handle tickets based on parent type
    if parent_type in ['Incident', 'Request', 'Ticket']:
        stmt = (
            sa.select(Ticket)
            .where(Ticket.parent_id == parent_ticket.id)
            .order_by(Ticket.ticket_number)
        )

        paginated_tickets = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
        tickets = paginated_tickets.items
        ticket_data = [create_ticket_response(ticket, Ticket, user_timezone) for ticket in tickets]
        total_tickets = paginated_tickets.total

    elif parent_type in ['Problem', 'Known Error', 'Workaround']:
        stmt = (
            sa.select(Ticket)
            .where(Ticket.problem_id == parent_ticket.id)
            .order_by(Ticket.ticket_number)
        )

        paginated_tickets = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
        tickets = paginated_tickets.items
        ticket_data = [create_ticket_response(ticket, Ticket, user_timezone) for ticket in tickets]
        total_tickets = paginated_tickets.total

    elif parent_type in ['Change']:
        # Get ticket children for Change
        ticket_stmt = (
            sa.select(Ticket)
            .where(Ticket.change_id == parent_ticket.id)
            .order_by(Ticket.ticket_number)
        )

        paginated_tickets = db.paginate(ticket_stmt, page=page, per_page=per_page, error_out=False)
        tickets = paginated_tickets.items
        ticket_data = [create_ticket_response(ticket, Ticket, user_timezone) for ticket in tickets]
        total_tickets = paginated_tickets.total

        # Get problem children for Change
        problem_stmt = (
            sa.select(Problem)
            .where(Problem.change_id == parent_ticket.id)
            .order_by(Problem.ticket_number)
        )

        paginated_problems = db.paginate(problem_stmt, page=page, per_page=per_page, error_out=False)
        problems = paginated_problems.items
        problem_data = [create_ticket_response(problem, Problem, user_timezone) for problem in problems]
        total_problems = paginated_problems.total

        # Get release children for Change
        release_stmt = (
            sa.select(Release)
            .where(Release.change_id == parent_ticket.id)
            .order_by(Release.ticket_number)
        )

        paginated_releases = db.paginate(release_stmt, page=page, per_page=per_page, error_out=False)
        releases = paginated_releases.items
        release_data = [create_ticket_response(release, Release, user_timezone) for release in releases]
        total_releases = paginated_releases.total

    # Calculate the total count of all children
    total = total_tickets + total_problems + total_releases

    # Combine all child data
    all_data = ticket_data + problem_data + release_data

    # Determine the last page based on total results and per_page
    last_page = (total + per_page - 1) // per_page if per_page > 0 else 1

    response = {
        'total': total,
        'last_page': last_page,
        'data': all_data
    }
    return jsonify(response), 200


@api_bp.post('/add-children/')
@login_required
def add_children():
    '''
    Incidents/Requests can be added to a Parent Ticket, a Problem, or a Change
    :return: HTTP response code 200
    '''
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    parent_ticket_number = data['parent-ticket-number']
    parent_type = data['parent-type']  # Parent is Ticket, Problem, or Change
    child_ticket_number = data['child-ticket-number']
    child_type = data['child-type']

    parent_model = get_model(parent_type)  # in common_utils
    child_model = get_model(child_type)
    current_time = datetime.now(timezone.utc)

    parent_ticket = db.session.execute(
        sa.select(parent_model)
        .where(parent_model.ticket_number == parent_ticket_number)
    ).scalar_one_or_none()

    child_ticket = db.session.execute(
        sa.select(child_model)
        .where(child_model.ticket_number == child_ticket_number)
    ).scalar_one_or_none()

    if parent_ticket is None or child_ticket is None:
        return jsonify({'error': 'Invalid JSON data: '}), 400

    match parent_type:
        case 'Incident' | 'Request':
            child_ticket.parent_id = parent_ticket.id
        case 'Problem':
            child_ticket.problem_id = parent_ticket.id
        case 'Change':
            child_ticket.change_id = parent_ticket.id

    child_ticket.last_updated_at = current_time
    child_ticket.status = parent_ticket.status

    try:
        db.session.commit()
        return jsonify(), 200
    except SQLAlchemyError as e:
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500


@api_bp.get('/remove_children/')
@login_required
def remove_children():
    '''
    iterates through all child tickets of parent and removes parent_id. This is called when
    the is_parent checkbox is unchecked (so no longer want the 'parent' to be a parent for whatever reason)

    :return: Str(200) as HTML response code
    '''
    parent = request.args.get('parent')

    if not parent:
        return jsonify({'error': 'Parent ticket number is required'}), 400

    parent_ticket = db.session.execute(
        sa.select(Ticket)
        .where(Ticket.ticket_number == parent)
    ).scalar_one_or_none()

    if not parent_ticket:
        return jsonify({'error': 'Parent ticket not found'}), 404

    parent_id = parent_ticket.id
    parent_ticket.is_parent = False
    db.session.add(parent_ticket)

    children = db.session.execute(
        sa.select(Ticket)
        .where(Ticket.parent_id == parent_id)
    ).scalars().all()

    if not children:
        try:
            db.session.commit()
            return jsonify({'message': 'No child tickets found'}), 200
        except SQLAlchemyError as e:
            return jsonify({'error': f'Database error: {str(e)}'}), 500

    current_time = datetime.now(timezone.utc)
    for child in children:
        child.parent_id = None
        child.last_updated_at = current_time

        journal_note = (f'<span name="worklog-time">{current_time}'
                        f'</span>Parent ID removed - ticket is no longer associated with another ticket '
                        f'Parent Ticket number was {parent_id}'
                        )
        add_journal_notes(child, journal_note, True)

    try:
        db.session.commit()
        return jsonify({'message': 'Children removed successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@api_bp.post('/get_paginated/')
@login_required
def get_paginated():
    '''
    Retrieves a paginated list of tickets based on filters.
    '''
    data = request.get_json(silent=True) or {}
    # Dynamically determine the model based on the 'model' field
    model_txt = data.get('model')
    model = get_model(model_txt)

    # Determine the Ticket-specific params handler
    handle_params_func = None
    match model_txt.lower():
        case 'change':
            handle_params_func = handle_change_params
        case 'cmdb':
            handle_params_func = handle_cmdb_params
        case 'idea':
            handle_params_func = handle_idea_params
        case 'interaction' | 'problem':
            handle_params_func = handle_interaction_params
        case 'knowledge':
            handle_params_func = handle_knowledge_params
        case 'release':
            handle_params_func = handle_release_params
        case 'users':
            handle_params_func = handle_user_params

            # Check if a handler was found for the model
    if handle_params_func is None:
        return {'error': 'Invalid model type provided'}, 400

    # Pass the Ticket model, corresponding data, and the Ticket-specific params handler
    return get_paginated_results(model, data, handle_params_func)


@api_bp.post('/get-worknotes/')
@login_required
def get_worknotes():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    ticket_type = data.get('ticket_type')
    ticket_number = data.get('ticket_number')
    model = get_model(ticket_type)

    if not ticket_type or not ticket_number:
        return jsonify({'error': 'Missing required fields'}), 400

    ticket = db.session.execute(
        sa.select(model)
        .where(model.ticket_number == ticket_number)
    ).scalars().one_or_none()

    if not ticket:
        return jsonify({'error': f'Ticket not found: {ticket_number}'}), 404

    worknotes = ticket.notes

    response = [{
        'note_date': note.note_date.strftime(g.datetime_format),
        'noted_by': note.noted_by,
        'note': note.note,
        'is_system': note.is_system or False,  # Handle nullable is_system
        'record_id': note.id
    } for note in sorted(worknotes, key=lambda note: note.id, reverse=True)
    ]

    return jsonify(response), 200


@api_bp.post('/save-worknote/')
@login_required
def save_worknote():
    '''
    Saves worknotes and resolution details
    :return: 200
    '''
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    model = get_model(data.get('ticket_type'))
    ticket_number = data.get('ticket_number')
    note_content = data.get('note')
    is_system = data.get('is_system') or False

    if not ticket_number or not note_content:
        return jsonify({'error': 'Missing required fields'}), 400

    ticket = db.session.execute(
        sa.select(model)
        .where(model.ticket_number == ticket_number)
    ).scalar_one_or_none()

    add_journal_notes(ticket, note_content, is_system)

    return jsonify({'success': 'Worknote saved'}), 200


@api_bp.post('/update-worknote/')
@login_required
def update_worknote():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    model = get_model(data.get('ticket_type'))
    ticket_number = data.get('ticket_number')
    record_id = data.get('record_id')
    note_content = data.get('updated_note')

    if not ticket_number or not record_id or not note_content:
        return jsonify({'error': 'Missing required fields'}), 400

    note = db.session.execute(
        sa.select(Notes)
        .where(Notes.id == record_id)
    ).scalar_one_or_none()

    if not note:
        return jsonify({'error': 'Note not found'}), 404

    ticket = db.session.execute(
        sa.select(model)
        .where(model.ticket_number == ticket_number)
    ).scalar_one_or_none()

    if not ticket:
        return jsonify({'error': f'Ticket not found: {ticket_number}'}), 404

    note.note = Markup(note_content)

    # also add a note to the system journal to log that this note has changed
    add_journal_notes(ticket, f'Updated worknote originally created on {note.note_date}', True)

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error: ' + str(e)}), 500
    return jsonify({'success': 'Worknote updated'}), 200


@api_bp.post('/update-status/')
@login_required
def update_status():
    '''
    Updates the status of the ticket. Ticket number and status are in json as 'Ticket_number': 123, 'status': 'Resolved'
    :return:
    '''
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    ticket_number = data.get('ticket_number')
    model = get_model(data.get('ticket-type'))

    if not ticket_number or not model:
        return jsonify({'error': 'Missing required fields'}), 400

    ticket = db.session.execute(
        sa.select(model)
        .where(model.ticket_number == ticket_number)
    ).scalars().one_or_none()

    if ticket:
        ticket.status = data.get('status')
        ticket.last_updated = datetime.now(timezone.utc)

        if ticket.ticket_type in ["Incident", "Request"]:
            if ticket.status == 'in-progress':
                # so respond timestap is not overwritten if respond step if clicked multiple times
                if not ticket.sla_responded:
                    ticket.sla_responded = True
                    ticket.sla_responded_at = datetime.now(timezone.utc)
                # status might go back to in-progress so need to reset
                if ticket.sla_resolved:
                    ticket.sla_resolved = False

            if ticket.status == 'resolved':
                # so resolve timestamp is not overwritten if resolve step if clicked multiple times
                if not ticket.sla_resolved:
                    ticket.sla_resolved = True
                    ticket.sla_resolved_at = datetime.now(timezone.utc)

            if ticket.is_parent:
                #
                children = db.session.execute(
                    sa.select(Ticket)
                    .where(Ticket.parent_id == ticket.id)
                ).scalars().all()

                for child in children:
                    child.status = ticket.status

        if ticket.status in ['cab']:
            ticket.cab_ready = True  # setting here because it is possible to check it and move status to cab without saving

        try:
            db.session.commit()
            return jsonify({'success': 'Ticket status updated'}), 200
        except SQLAlchemyError as e:
            log_exception(f'Database error: {e}')
            return jsonify({'error': 'Database error: ' + str(e)}), 500
    else:
        return jsonify({
            'info': 'Ticket does not exist or has not been saved for the first time yet'}), 200  # do nothing if ticket doesn't exist


@api_bp.post('/save-resolution/')
@login_required
def save_resolution():
    # Parse JSON input
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    # Extract and validate inputs
    resolution_notes = data.get('resolution_notes')
    resolution_code_id = data.get('resolution_code_id')
    ticket_number = data.get('ticket_number')
    ticket_type = data.get('ticket-type')

    if not ticket_number or not ticket_type or resolution_code_id is None:
        return jsonify({'error': 'Missing required fields'}), 400

    # Get the model for the ticket type
    model = get_model(ticket_type)
    if not model:
        return jsonify({'error': f'Invalid ticket type: {ticket_type}'}), 400

    # Fetch the ticket
    ticket = db.session.execute(
        sa.select(model)
        .where(model.ticket_number == ticket_number)
    ).scalars().one_or_none()

    if not ticket:
        return jsonify({'error': f'Ticket not found: {ticket_number}'}), 404

    resolution_code = db.session.execute(
        sa.select(ResolutionLookup.resolution)
        .where(ResolutionLookup.id == resolution_code_id)
    ).scalars().one_or_none()

    if not resolution_code:
        return jsonify({'error': f'Resolution code not found: {resolution_code_id}'}), 404

    # Update ticket details
    ticket.resolution_notes = resolution_notes
    ticket.resolution_code_id = resolution_code_id

    ticket.resolution_journal = (f'Resolution Code: {resolution_code} <br> '
                                 f'Resolution Notes: {resolution_notes} '
                                 f'Date: {datetime.now(timezone.utc).strftime("%H:%M %b %d, %Y")} <hr>'
                                 ) + (ticket.resolution_journal or '')

    ticket.resolved_at = datetime.now(timezone.utc)

    if hasattr(ticket, 'sla_resolved'):
        ticket.sla_resolved = True
        if ticket.resolved_at > ticket.sla_resolve_by:
            ticket.sla_resolve_breach = True

    # Update status based on ticket type
    ticket.status = {
        'Change': 'implement',
        'Idea': 'adopting'
    }.get(ticket_type, 'resolved')

    children = get_child_tickets(model, ticket_number)  # fuction in this file
    if children:
        for child in children:
            child.status = ticket.status

    try:
        db.session.commit()
        return jsonify({'success': 'Resolution saved successfully', 'resolution': ticket.resolution_journal}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@api_bp.get('/get_active_announcements/')
@login_required
def get_active_announcements():
    try:
        # Query active announcements
        announcements = db.session.execute(
            sa.select(PortalAnnouncements)
            .where(PortalAnnouncements.active.is_(True))
        ).scalars().all()

        # Transform data into the desired format
        response_data = [
            {
                'title': announcement.title,
                'announcement': announcement.announcement,
                'start': announcement.start.strftime('%H:%M on %B %d'),
                'end': announcement.end.strftime('%H:%M on %B %d'),
            }
            for announcement in announcements
        ]

        # Return the response
        return jsonify(response_data), 200

    except SQLAlchemyError as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@api_bp.get('/get_business_hours/')
@login_required
def get_business_hours():
    try:
        location_id = current_user.location.id
        # Allow for multiple locations. Defaults to 1 if not set. Regionalisation not fully implemented though
        if not location_id:
            location_id = 1

        # Fetch business hours
        business_hours = db.session.execute(
            sa.select(OfficeHours)
            .where(OfficeHours.id == location_id)
        ).scalars().one_or_none()

        if not business_hours:
            return jsonify({'error': 'Business hours not found'}), 404

        # Format response
        response = {
            'start': business_hours.open_hour.strftime('%H:%M'),
            'end': business_hours.close_hour.strftime('%H:%M'),
        }

        return jsonify(response), 200

    except SQLAlchemyError as e:
        log_exception(f'Database error: {e}')
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@api_bp.post('/get_sibling_tickets/')
@login_required
def get_sibling_tickets():
    response = {}
    data = request.get_json(silent=True)
    if data is None:
        log_exception(f'Invalid JSON data or incorrect Content-Type header: {e}')
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400
    model = get_model(data['model'])
    ticket_number = data.get('ticket_number')

    if not ticket_number or not model:
        log_exception(f'Missing required fields')
        return jsonify({'error': 'Missing required fields'}), 400

    # Fetch the current ticket to get its ticket_type
    current_ticket = db.session.execute(
        sa.select(model)
        .where(model.ticket_number == ticket_number)
    ).scalars().one_or_none()

    if current_ticket is None:
        return jsonify({'error': 'Ticket not found'}), 404

    # Find the previous ticket of the same type, ordered by ticket_number descending (to get the closest prior record)
    previous_ticket = db.session.execute(
        sa.select(model)
        .where(model.ticket_number < ticket_number)
        .order_by(model.ticket_number.desc())
    ).scalars().first()

    if previous_ticket is None:
        response['previous'] = None
    else:
        response['previous'] = previous_ticket.ticket_number

    # Find the next ticket of the same type, ordered by ticket_number ascending (to get the closest next record)
    next_ticket = db.session.execute(
        sa.select(model)
        .where(model.ticket_number > ticket_number)
        .order_by(model.ticket_number.asc())
    ).scalars().first()

    if next_ticket is None:
        response['next'] = None
    else:
        response['next'] = next_ticket.ticket_number

    return jsonify(response)


@api_bp.get('/get_password_reset_url/')
@login_required
def get_password_reset_url():
    return current_app.config['SECURITY_CHANGE_URL']


@api_bp.post('/delete_table_row/')
@login_required
def delete_table_row():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    model = get_model(data['model']);
    ticket_number = data.get('ticket_number');
    ticket_id = data.get('id');

    if ticket_number:
        row = db.session.execute(
            sa.select(model)
            .where(model.ticket_number == data['ticket_number'])
        ).scalars().one_or_none()

    elif ticket_id:
        row = db.session.execute(
            sa.select(model)
            .where(model.id == data['id'])
        ).scalars().one_or_none()

    else:
        return jsonify({'error': 'Invalid JSON data'}), 400

    if row:
        try:
            db.session.delete(row)
            db.session.commit()

        except SQLAlchemyError as e:
            log_exception(f'Database error: {e}')
            return jsonify({'error': 'Database error: ' + str(e)}), 500
        return jsonify(), 200
    else:
        return jsonify({'error': 'Invalid JSON data: '}), 500


@api_bp.post('/update_table_row/')
@login_required
def update_table_row():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400
    model = get_model(data['model'])

    if not model:
        return jsonify({'error': 'Invalid JSON data'}), 400

    ticket = db.session.execute(
        sa.select(model)
        .where(model.ticket_number == data['ticket_number'])
    ).scalars().one_or_none()

    for key, value in data.items():
        if not hasattr(ticket, key):
            continue

        if value in [None, '']:  # Skip empty data
            continue

        model_field = getattr(ticket.__class__, key, None)
        if isinstance(model_field, db.Column):
            # Convert data to the column's Python type
            column_type = model_field.type.python_type
            setattr(ticket, key, column_type(value))
        else:
            if value == 0:  # Skip select fields with value 0 that are foriegn keys
                continue
            setattr(ticket, key, value)

    try:
        ticket.last_updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify(), 200
    except SQLAlchemyError as e:
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500


@api_bp.post('/unlink-children/')
@login_required
def unlink_children():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    child_ticket_number = data.get('ticket-number')
    child_type = data.get('ticket-type')

    if not all([child_ticket_number, child_type]):
        return jsonify({'error': 'Missing required fields in the request body'}), 400

    child_model = get_model(child_type)

    if not child_model:
        log_exception(f'Invalid child or parent type')
        return jsonify({'error': 'Invalid child or parent type'}), 400

    # Fetch child tickets
    child_ticket = db.session.execute(
        sa.select(child_model)
        .where(child_model.ticket_number == child_ticket_number)
    ).scalars().one_or_none()

    if not child_ticket:
        return jsonify({'error': 'Child tickets not found'}), 404

    if hasattr(child_ticket, 'problem_id'):
        child_ticket.problem_id = None

    if hasattr(child_ticket, 'change_id'):
        child_ticket.change_id = None

    if hasattr(child_ticket, 'parent_id'):
        child_ticket.parent_id = None

    try:
        db.session.commit()
        return jsonify({'message': 'Child ticket has been unlinked'}), 200
    except SQLAlchemyError as e:
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500


@api_bp.post('/send_requester_email/')
@login_required
def send_requester_email():
    # Parse JSON data
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    DEFAULT_SUBJECT = 'A message from the IT Support team'
    # Extract required fields
    recipients = data.get('recipients')
    ticket_number = data.get('ticket-number')
    subject_line = data.get('subject', DEFAULT_SUBJECT)
    body_text = data.get('body-text')
    model = data.get('model')
    # Validate required fields
    if not all([ticket_number, subject_line, body_text, model]):
        return jsonify({'error': 'Missing required fields in the request body'}), 400

    # Execute email sending asynchronously
    send_notification(
        ticket_number=ticket_number,
        model=model,
        template='email.html',
        subject_line=subject_line,
        body_text=body_text,
        exists=True,
    )

    return jsonify({'message': 'Email notification has been sent'}), 200
