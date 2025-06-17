from flask import request, jsonify
from flask_security import login_required
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

from . import api_bp
from ..common.exception_handler import log_exception
from ..common.ticket_utils import datetime_to_string
from ..model import db
from ..model.model_change import Change, ChangeTemplates
from ..model.model_user import User
from ..model.relationship_tables import ChangeApprover
from ..views.change.change_utils import send_approval_needed, send_approval_removed, send_cab_outcome_email
from ..views.change.risk_calcs import risk_calcs



@api_bp.get('/change/changes-scheduled/')
@login_required
def changes_scheduled():
    return jsonify(Change.scheduled_changes())


@api_bp.get('/change/get-change-resources/')
@login_required
def get_change_resources():
    return jsonify(Change.get_change_resources())


@api_bp.post('/change/add-approver/')
@login_required
def add_approver():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    approver_id = data.get('approver')
    ticket_number = data.get('ticket-number')

    if not approver_id or not ticket_number:
        return jsonify({'error': 'Missing approver or ticket number'}), 400

    user = db.session.execute(
        sa.select(User)
        .where(User.id == approver_id)
    ).scalars().one_or_none()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    change = db.session.execute(
        sa.select(Change)
        .where(Change.ticket_number == ticket_number)
    ).scalars().one_or_none()

    if not change:
        return jsonify({'error': 'Change not found'}), 404

    # check if user is already added as an approver
    existing_approver = db.session.execute(
        sa.select(ChangeApprover)
        .where(ChangeApprover.change_id == change.id)
        .where(ChangeApprover.user_id == user.id)
    ).scalars().one_or_none()

    if not existing_approver:
        new_approver = ChangeApprover(change=change, user=user)
        db.session.add(new_approver)
        # Append to the relationship list
        change.change_approvers.append(new_approver)
        try:
            db.session.commit()
            send_approval_needed([approver_id], ticket_number)  # in change_utils.py
            return jsonify({'message': 'Approver added successfully'}), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            log_exception(f'Database error: {e}')
            return jsonify({'error': 'Database error: ' + str(e)}), 400
    else:
        # resend email to approver
        send_approval_needed([approver_id], ticket_number)
        return jsonify({'message': 'Approval(s) resent'}), 200

@api_bp.post('/change/remove-approver/')
@login_required
def remove_approver():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    approver_id = data.get('approver')
    ticket_number = data.get('ticket-number')

    if not approver_id or not ticket_number:
        return jsonify({'error': 'Missing approver or ticket number'}), 400

    # Get the Change by ticket number
    change = db.session.execute(
        sa.select(Change)
        .where(Change.ticket_number == ticket_number)
    ).scalars().one_or_none()

    if not change:
        return jsonify({'error': 'Change not found'}), 404

    # Get the User by ID (approver_id)
    user = db.session.execute(
        sa.select(User)
        .where(User.id == approver_id)
    ).scalars().one_or_none()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Remove the Approver from the Change
    approver_record = db.session.execute(
        sa.select(ChangeApprover)
        .where(sa.and_(ChangeApprover.change_id == change.id, ChangeApprover.user_id == user.id))
    ).scalars().one_or_none()

    if not approver_record:
        return jsonify({'error': 'Approver not linked to Change'}), 404

    try:
        db.session.delete(approver_record)
        db.session.commit()
        send_approval_removed([approver_id], ticket_number)  # in change_utils.py
        return jsonify({'message': 'Approver removed successfully'}), 200
    except SQLAlchemyError as e:
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500



@api_bp.post('/change/set-cab-outcome/')
@login_required
def set_cab_outcome():
    """
    Saves CAB approval status and associated fields, requirements checks, and cab notes
    then calls send_outcome_email
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    outcome = data.get('cab-approval')
    check_box_data = data.get('checkbox-data')
    ticket_number = data.get('ticket-number')

    if ticket_number is None:
        return jsonify({'error': 'Missing ticket number or CAB approval status'}), 400


    change = db.session.execute(
        sa.select(Change)
        .where(Change.ticket_number == ticket_number)
    ).scalars().one_or_none()

    if not change:
        return jsonify({'error': 'Change not found'}), 404

    recipient = change.requester.email  # get the requester email address
    if recipient is None:
        return jsonify({'error': 'Recipient not found or has no email address'}), 400

    for key, value in check_box_data.items():
        setattr(change, key, value)

    change.cab_approval_status = outcome

    body_text = change.cab_notes

    try:
        db.session.commit()
        send_cab_outcome_email(recipient, ticket_number, outcome, body_text)
        return jsonify({'success': 'CAB approval status set successfully'}), 200

    except Exception as e:
        log_exception(f'{e}')
        return jsonify({'error': 'Error sending email: ' + str(e)}), 500


@api_bp.post('/change/get-cab-status-count/')
@login_required
def get_cab_status_count():
    try:
        response = Change.cab_status_count()
        return jsonify(response), 200
    except Exception as e:
        log_exception(f'{e}')
        return jsonify({'error': f'Error getting Change CAB status {e}'})


@api_bp.get('/change/get-change-ticket/')
@login_required
def get_change_ticket():
    """
    Get a specific change ticket by ticket number. Used by admin change dashboard
    """
    ticket_number = request.args.get('ticket-number')
    change = db.session.execute(
        sa.select(Change)
        .where(sa.and_(Change.ticket_number == ticket_number))
    ).scalar_one_or_none()
    if not change:
        return jsonify({'error': 'Change Ticket not found'}), 404

    result = {
        'category': change.category.name if change.category else '',
        'created_at': datetime_to_string(change.created_at),
        'created-by': change.created_by.full_name if change.created_by else '',
        'details': change.details,
        'last-updated': datetime_to_string(change.last_updated_at),
        'priority': change.risk_set,
        'risk-calc': change.risk_calc,
        'requested-by': change.requester.full_name if change.requester else '',
        'support-agent': change.supporter.full_name if change.supporter else '',
        'short-desc': change.short_desc,
        'status-select': change.status,
        'support-team': change.support_team.name if change.support_team else '',
        'ticket-number': change.ticket_number,
        'ticket-type': change.ticket_type,
        'updated-at': datetime_to_string(change.last_updated_at),
    }

    return jsonify(result)


@api_bp.post('/change/set-calculated-risk/')
@login_required
def set_calculated_risk():
    """
    set the risk level for a Change based on variables from change-risk.js
    Where a value is used it uses the value of the select field option not the text.

    return: the calculated risk CR1 through to CR5
    """
    from ..views.change.risk_calcs import ci_importance_risk

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    risk_checks = data['risk']
    ci_id = data.get('ci_id')
    change_timing = data.get('change_timing')  # change window, in hours, after hours
    downtime = float(data.get('downtime', 0))
    people_impact = int(data.get('people_impact') or 0)
    scale = data.get('scale')

    metalic_points = ci_importance_risk(ci_id, change_timing)
    risk_points = risk_calcs(risk_checks, people_impact, change_timing)

    outage_modifier = (
        2 if 0 < downtime < 1 else
        3 if 1 <= downtime < 4 else
        4 if 4 <= downtime < 8 else
        5
    )
    # because Availability is not affected if the Change is made in a change window the modifier is set to 1
    if change_timing == 'change_window':
        outage_modifier = 1

    scale_multipliers = {
        'minor': 1,
        'medium': 1.25,
        'major': 1.5
    }
    scale_multiplier = scale_multipliers.get(scale, 1)

    total_points = metalic_points * scale_multiplier + risk_points * outage_modifier
    # Risk Level Determination
    if total_points <= 10:
        return jsonify({'risk': 'CR5'}), 200
    elif total_points <= 20:
        return jsonify({'risk': 'CR4'}), 200
    elif total_points <= 40:
        return jsonify({'risk': 'CR3'}), 200
    elif total_points <= 60:
        return jsonify({'risk': 'CR2'}), 200
    else:
        return jsonify({'risk': 'CR1'}), 200


@api_bp.post('change/set-change-risk/')
@login_required
def set_change_risk():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    risk = data['risk']
    ticket_number = data.get('ticket-number')

    if not ticket_number or not risk:
        return jsonify({'error': 'Missing ticket number or risk'}), 400


    change = db.session.execute(
        sa.select(Change)
        .where(Change.ticket_number == ticket_number)
    ).scalar_one_or_none()

    if not change:
        return jsonify({'error': 'Change not found'}), 404

    change.risk_set = risk
    db.session.commit()

    return jsonify({'success': 'Change risk set'}), 200

@api_bp.post('/change/get-standard-template/')
@login_required
def get_standard_template():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    template_id = data.get('template-id')

    if not template_id:
        return jsonify({'error': 'Template not found'}), 404

    template = db.session.execute(
        sa.select(ChangeTemplates)
        .where(ChangeTemplates.id == template_id)
    ).scalar_one_or_none()

    if not template:
        return jsonify({'error': 'Template not found'}), 404

    result = {
        'change-reason': template.change_reason,
        'category-id': template.category if template.category else '',
        'set-risk': template.risk_set,
        'departments-impacted': [dpt for dpt in template.departments_impacted],
        'impacted-ci': template.cmdb_id if template.cmdb_id else '',
        'short-desc': template.short_desc,
        'support-team': template.support_team if template.support_team else '',
    }

    return jsonify(result), 200
