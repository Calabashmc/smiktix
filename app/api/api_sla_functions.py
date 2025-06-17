from datetime import datetime, timezone, timedelta
from flask import g, jsonify, request
from flask_login import current_user
from flask_security import login_required

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

from . import api_bp
from app.common.sla import calculate_sla_times, calculate_resolve_time
from ..common.exception_handler import log_exception
from ..model import db
from ..model.lookup_tables import Importance, PriorityLookup, PauseReasons, OfficeHours, AppDefaults
from ..model.model_interaction import Ticket, TicketPauseHistory
from ..model.model_user import User


@api_bp.post('/sla/get-metallics/')
@login_required
def get_metallics():
    """
    Endpoint for getting table of metallics for grouping device or service by importance
    :return: json of metallics records
    """
    metallics = db.session.execute(
        sa.select(Importance)
        .order_by(Importance.rating)
    ).scalars().all()
    # total_tickets = Importance.query.count()

    response = {
        # 'total': total_tickets,
        # 'last_page': 1,
        'data': [{'rating': metallic.rating,
                  'importance': metallic.importance,
                  'note': metallic.note} for metallic in metallics]
    }
    return jsonify(response)


@api_bp.post('/sla/set-metallics/')
@login_required
def set_metallics():
    """
    Sets the importance of a ticket. Called from sla-config.js handleTtableEdit()
    sends json in format {row: {rating: 1, importance: 'Rust', note: 'Of no importance'}}
    :return: True or False
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    row = data['row']

    if data:
        metallic = db.session.execute(
            sa.select(Importance)
            .where(Importance.rating == row['rating'])
        ).scalars().first()

        metallic.rating = row['rating']  # adding for if an entire new row is added
        metallic.importance = row['importance']
        metallic.note = row['note']
        try:
            db.session.add(metallic)
            db.session.commit()
        except SQLAlchemyError as e:
            log_exception(f'Database error: {e}')
            return jsonify({'error': 'Database error: ' + str(e)}), 500
        return jsonify(), 200
    else:
        return jsonify({'error': 'Invalid JSON data: '}), 500


@api_bp.post('/sla/get-sla-priority-from-urgency-impact/')
@login_required
def get_sla_priority():
    """
    Endpoint for getting table of slas by priority for app-defaults configuration
    :return: json of sla records
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    urgency = data.get('urgency')
    impact = data.get('impact')

    if not urgency or not impact:
        return jsonify({'error': 'Missing urgency or impact'}), 400

    priority = {
        ('high', 'high'): 'P1',
        ('high', 'medium'): 'P2',
        ('high', 'low'): 'P3',
        ('medium', 'high'): 'P2',
        ('medium', 'medium'): 'P3',
        ('medium', 'low'): 'P4',
        ('low', 'high'): 'P3',
        ('low', 'medium'): 'P4',
        ('low', 'low'): 'P5',

    }

    priority = priority.get((urgency, impact), 'P5')

    if not priority:
        return jsonify({'error': 'Priority not found'}), 404

    timing = db.session.execute(
        sa.select(PriorityLookup)
        .where(PriorityLookup.priority == priority)
    ).scalar_one_or_none()
    if timing:
        response = timing.respond_by
        resolve = timing.resolve_by
    else:
        response = 'NA'
        resolve = 'NA'

    return jsonify({'priority': priority, 'response': response, 'resolve': resolve}), 200

@api_bp.post('/sla/set-app-default-sla-priority/')
@login_required
def set_sla_app_default_priority():
    """
    Endpoint for setting app-defaults SLA priority's from sla-config.js
    :return: json of sla records
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    row = data['row']

    if data:
        priority = db.session.execute(
            sa.select(PriorityLookup)
            .where(PriorityLookup.priority == row['priority'])
        ).scalars().first()

        priority.priority = row['priority']  # adding for if an entire new row is added
        priority.respond_by = row['respond_by']
        priority.resolve_by = row['resolve_by']
        priority.twentyfour_seven = row['twentyfour_seven']
        try:
            db.session.add(priority)
            db.session.commit()
        except SQLAlchemyError as e:
            log_exception(f'Database error: {e}')
            return jsonify({'error': 'Database error: ' + str(e)}), 500
        return jsonify(), 200
    else:
        return jsonify({'error': 'Invalid JSON data: '}), 500


@api_bp.post('/sla/set-sla-details/')
@login_required
def set_sla_details():
    """
    Endpoint for setting SLA details for a ticket.
    Updates priority, urgency, impact and calculates SLA times
    :return: json response with sla details and status
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    urgency = str.lower(data.get('urgency', 'low'))
    impact = str.lower(data.get('impact', 'low'))
    priority = data.get('priority')
    ticket_number = data.get('ticket_number')

    if not ticket_number:
        return jsonify({'error': 'Missing ticket number'}), 400

    ticket = db.session.execute(
        sa.select(Ticket)
        .where(Ticket.ticket_number == ticket_number)
    ).scalars().first()

    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    if not priority:
        # set based on urgency and impact. Default fetched in case urgency or impact are missing
        priority = db.session.execute(
            sa.select(AppDefaults.incident_default_priority)
        ).scalar_one_or_none()

        match (urgency, impact):
            case ('low', 'low'):
                priority = 'P5'
            case ('low', 'medium') | ('medium', 'low'):
                priority = 'P4'
            case ('high', 'low') | ('medium', 'medium') | ('low', 'high'):
                priority = 'P3'
            case ('high', 'medium') | ('medium', 'high'):
                priority = 'P2'
            case ('high', 'high'):
                priority = 'P1'

    # Update ticket properties
    ticket.priority = priority
    ticket.priority_urgency = urgency
    ticket.priority_impact = impact

    # Calculate and set SLA times
    respond, resolve = calculate_sla_times(ticket.created_at, priority=priority)
    ticket.sla_respond_by = respond
    ticket.sla_resolve_by = resolve

    # Check for SLA breaches
    current_time = datetime.now(timezone.utc)
    ticket.sla_response_breach = ticket.sla_resolve_by < current_time
    ticket.sla_resolve_breach = ticket.sla_resolve_by < current_time

    response = {
        'respond-by': ticket.sla_respond_by.strftime(g.datetime_format),
        'resolve-by': ticket.sla_resolve_by.strftime(g.datetime_format),
        'responded': ticket.sla_responded,
        'respond-breach': ticket.sla_response_breach,
        'resolved': ticket.sla_resolved,
        'resolve-breach': ticket.sla_resolve_breach,
        'sla-paused': ticket.sla_paused
    }

    try:
        db.session.commit()
        return jsonify(response), 200
    except SQLAlchemyError as e:
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500


@api_bp.post('/get_sla_pause_reasons/')
@login_required
def get_sla_pause_reasons():
    """
    Endpoint for sla-pause-reasons.js
    :return: json of sla pause reasons
    """
    sla_pause_reasons = PauseReasons.get_sla_pause_reasons()
    return jsonify({'data': sla_pause_reasons})


@api_bp.post('/set_sla_pause_reason/')
@login_required
def set_sla_pause_reason():
    """
    Sets the importance of a ticket. Called from sla-config.js handleTtableEdit()
    sends json in format {row: {rating: 1, importance: 'Rust', note: 'No importance'}}
    :return: True or False
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    row = data['row']
    if data:
        reason = db.session.execute(
            sa.select(PauseReasons).where(PauseReasons.id == row['id'])).scalars().first() or PauseReasons()
        reason.reason = row['reason']  # adding for if an entire new row is added

        try:
            db.session.add(reason)
            db.session.commit()
        except SQLAlchemyError as e:
            log_exception(f'Database error: {e}')
            return jsonify({'error': 'Database error: ' + str(e)}), 500
        return jsonify(), 200
    else:
        return jsonify({'error': 'Invalid JSON data: '}), 500


@api_bp.post('/sla/pause-sla/')
@login_required
def pause_sla():
    """
    Pauses SLA. Called from sla-settings.js pause slaButtonListeners()
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    ticket_number = data['ticket_number']
    sla_pause_reason = data['pause_reason']
    current_time = datetime.now(timezone.utc)

    if ticket_number:
        ticket = db.session.execute(
            sa.select(Ticket)
            .where(Ticket.ticket_number == ticket_number)
        ).scalars().first()

        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404

        ticket.sla_paused = True

        reason = db.session.execute(
            sa.select(PauseReasons)
            .where(PauseReasons.id == sla_pause_reason)
        ).scalars().first()

        # Create a new TicketPauseHistory record
        new_pause_record = TicketPauseHistory(
            paused_at=current_time,
            reason=reason,
            paused_by=current_user,
            ticket=ticket  # Assign relationship
        )

        # Append to ticket.pause_history
        ticket.pause_history.append(new_pause_record)

        try:
            db.session.add(new_pause_record)
            db.session.commit()
        except SQLAlchemyError as e:
            log_exception(f'Database error: {e}')
            return jsonify({'error': 'Database error: ' + str(e)}), 500
        return jsonify({'success': 'SLA paused'}), 200
    else:
        return jsonify({"error": "Invalid JSON data: "}), 500


@api_bp.post("/sla/resume-sla/")
@login_required
def resume_sla():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON data or incorrect Content-Type header"}), 400

    ticket_number = data["ticket_number"]
    current_time = datetime.now(timezone.utc)

    if not ticket_number:
        return jsonify({"error": "Missing ticket number"}), 400

    ticket = db.session.execute(
        sa.select(Ticket)
        .where(Ticket.ticket_number == ticket_number)
    ).scalars().first()

    results = db.session.execute(
        sa.select(TicketPauseHistory)
        .join(Ticket, TicketPauseHistory.ticket_id == Ticket.id)
        .where(Ticket.ticket_number == ticket_number)
        .where(TicketPauseHistory.resumed_at == None)
        .order_by(TicketPauseHistory.paused_at.desc())
    ).scalars().one_or_none()

    if results:
        results.resumed_at = current_time
        # Calculate the duration in seconds (or minutes if needed)
        duration_seconds = (current_time - results.paused_at).total_seconds()
        results.duration = duration_seconds  # Store the duration as a float (in seconds)

        ticket.sla_paused = False
        ticket.sla_resumed_at = current_time
        ticket.sla_respond_by = ticket.sla_respond_by + timedelta(seconds=duration_seconds)
        ticket.sla_resolve_by = ticket.sla_resolve_by + timedelta(seconds=duration_seconds)

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500
    return jsonify({"success": "SLA resumed"}), 200


@api_bp.post("/get-sla-resolve-time/")
@login_required
def get_sla_resolve_time():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON data or incorrect Content-Type header"}), 400
    respond_by = data["respond_by"]
    priority = data["priority"]

    priority = db.session.execute(
        sa.select(PriorityLookup)
        .where(PriorityLookup.priority == priority)
    ).scalars().first()
    wait_hours = priority.resolve_by - priority.respond_by

    resolve_by = calculate_resolve_time(respond_by, wait_hours)

    return jsonify({"wait_time": wait_hours, "resolve_by": resolve_by})


@api_bp.post("/check-response-time/")
@login_required
def check_response_time():
    """
    Returns true if the response time is in business hours
    :return: True or False
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON data or incorrect Content-Type header"}), 400

    priority = db.session.execute(
        sa.select(PriorityLookup)
        .where(PriorityLookup.priority == data["priority"])
    ).scalars().first()

    if priority.twentyfour_seven:
        return jsonify({"in_hours": True}), 200  # 24/7 coverage so any response time is acceptable

    business_hours = db.session.execute(
        sa.select(OfficeHours)
    ).scalars().first()

    respond_by = datetime.strptime(data["respond_by"], "%Y-%m-%dT%H:%M").time()

    if not (business_hours.open_hour <= respond_by <= business_hours.close_hour):
        return jsonify({"in_hours": False}), 200
    else:
        return jsonify({"in_hours": True}), 200


@api_bp.post('/sla/get-sla-pause-history/')
@login_required
def get_pause_history():
    data = request.get_json(silent=True)
    if not data or 'ticket-number' not in data:
        return jsonify({'error': 'Invalid Ticket Number'}), 400

    ticket_number = data['ticket-number']

    results = db.session.execute(
        sa.select(
            TicketPauseHistory,
            PauseReasons.reason,
            User.full_name
        ).join(
            Ticket, TicketPauseHistory.ticket_id == Ticket.id
        ).join(
            PauseReasons, TicketPauseHistory.reason_id == PauseReasons.id
        ).outerjoin(
            User, TicketPauseHistory.paused_by_id == User.id
        ).where(
            Ticket.ticket_number == ticket_number
        ).order_by(
            TicketPauseHistory.paused_at.desc()
        )
    ).all()

    if not results:
        return jsonify({'info': 'No pause history found'}), 200

    pause_history = []
    for ph, reason, full_name in results:
        pause_history.append({
            'paused_at': ph.paused_at,
            'resumed_at': ph.resumed_at if ph.resumed_at else 'TBD',
            'duration': round(ph.duration, 0) if ph.duration else 'TBD',
            'reason': reason,
            'paused_by': full_name
        })

    pause_history = sorted(pause_history, key=lambda x: x['paused_at'], reverse=True)

    return jsonify({'pause_history': pause_history}), 200
