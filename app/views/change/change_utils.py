import os
import sqlalchemy as sa
from flask import url_for, current_app
from flask_login import current_user

from ...model.model_change import Change
from ...model.model_user import User
from ...model.lookup_tables import AppDefaults, ChangeTypeLookup, RiskLookup, StatusLookup
from ...common.common_utils import send_email
from ...common.exception_handler import log_exception
from ...model import db


def handle_change_params(stmt, params):
    """
    Handles filtering for Ticket model based on 'params'.
    """
    p_name = params['name']
    p_name = p_name.replace('\n', ' ')

    change_types = {
        change_type.change_type for change_type in
        db.session.execute(
            sa.select(ChangeTypeLookup)
        ).scalars().all()
    }

    risks = {
        risk.risk for risk in db.session.execute(
            sa.select(RiskLookup)
        ).scalars().all()
    }

    statuses = {
        status.status for status in
        db.session.execute(
            sa.select(StatusLookup)
        ).scalars().all()
    }

    if p_name in risks:
        return stmt.where(Change.risk_set == p_name), f'Change with risk \'{params["name"]}\''

    elif p_name in change_types:
        return stmt.where(Change.change_type == p_name), f'Change with risk \'{params["name"]}\''

    elif p_name in statuses:
        return stmt.where(Change.status == p_name), f'Change with risk \'{params["name"]}\''

    else:
        return stmt, 'No filtering applied'


def send_approval_needed(stakeholder_list, ticket_number):
    change_short_dec = db.session.execute(
        sa.select(Change.short_desc)
        .where(Change.ticket_number == ticket_number)
    ).scalar_one_or_none()

    body_text = change_short_dec if change_short_dec else 'No details available'

    addresses = []
    for stakeholder_id in stakeholder_list:
        recipient = db.session.execute(
            sa.select(User.email)
            .where(User.id == stakeholder_id)
        ).scalar_one_or_none()

        if recipient:
            addresses.append(recipient)

    if not addresses:
        return {'error': 'No valid recipients found'}, 400

    subject = f'Change {ticket_number} - Approval Needed'
    ticket_url = url_for('change_bp.change_get', _external=True, ticket=ticket_number)
    service_desk_phone = db.session.execute(
        sa.select(AppDefaults.servicedesk_phone)
    ).scalar_one_or_none()

    template_params = {
        'title': f'Approval Needed for Change {ticket_number}',
        'body_text': body_text,
        'ticket_number': ticket_number,
        "ticket_url": ticket_url,
        "service_desk_phone": service_desk_phone,
        "approve_url": url_for(
            'change_bp.change_approve',
            _external=True,
            ticket=ticket_number,
            user=current_user.id
        ),
        "reject_url": url_for(
            'change_bp.change_reject',
            _external=True,
            ticket=ticket_number,
            user=current_user.id
        ),
    }

    # Define image paths
    approve_image_path = os.path.join(current_app.root_path, 'static', 'images', 'feedback', 'approve.png')
    reject_image_path = os.path.join(current_app.root_path, 'static', 'images', 'feedback', 'deny.png')

    # Create attachments list with Content-IDs
    attachments = [
        {
            'file': approve_image_path,
            'mimetype': "image",
            "mime_subtype": "png",
            'headers': {"Content-ID": "<approve_button>", "Content-Disposition": "inline"}
        },
        {
            'file': reject_image_path,
            'mimetype': "image",
            "mime_subtype": "png",
            'headers': {"Content-ID": "<reject_button>", "Content-Disposition": "inline"}
        }
    ]
    try:
        send_email(
            subject,
            addresses,
            template='change_approver_added.html',
            template_params=template_params,
            attachments=attachments
        )

        return {'status': 'success', 'message': 'Email has been sent'}, 200
    except Exception as e:
        log_exception(f'Error in email_approvers: {e}')
        return {'error': 'An unexpected error occurred'}, 500


def send_approval_removed(stakeholder_list, ticket_number):
    change_short_dec = db.session.execute(
        sa.select(Change.short_desc)
        .where(Change.ticket_number == ticket_number)
    ).scalar_one_or_none()

    if not change_short_dec:
        return {'error': 'Change not found'}, 404

    body_text = change_short_dec if change_short_dec else 'No details available'

    addresses = []
    for stakeholder_id in stakeholder_list:
        recipient = db.session.execute(
            sa.select(User.email)
            .where(User.id == stakeholder_id)
        ).scalar_one_or_none()

        if recipient:
            addresses.append(recipient)

    if not addresses:
        return {'error': 'No valid recipients found'}, 400

    subject = f'Change {ticket_number} - Approver removed'
    ticket_url = url_for('change_bp.change_get', _external=True, ticket=ticket_number)
    service_desk_phone = db.session.execute(
        sa.select(AppDefaults.servicedesk_phone)
    ).scalar_one_or_none()

    template_params = {
        'title': 'Approval No longer needed',
        'body_text': body_text,
        'ticket_number': ticket_number,
        "ticket_url": ticket_url,
        "service_desk_phone": service_desk_phone
    }

    try:
        send_email(
            subject,
            addresses,
            template='change_approver_removed.html',
            template_params=template_params,
            attachments=[],
        )
        return {'status': 'success', 'message': 'Email has been sent'}, 200
    except Exception as e:
        log_exception(f'Error in email_approvers: {e}')
        return {'error': 'An unexpected error occurred'}, 500


def send_cab_outcome_email(recipient, ticket_number, outcome, body_text):
    addresses = [recipient]

    subject = f'Change {ticket_number} - CAB Approval Status'

    template_params = {
        'title': 'Change CAB Approval Status',
        'body_text': body_text,
        'outcome': outcome,
        'ticket_number': ticket_number,
    }

    try:
        send_email(
            subject,
            addresses,
            template='cab-outcome.html',
            template_params=template_params,
        )

        return {'status': 'success', 'message': 'Email has been sent'}, 200
    except Exception as e:
        log_exception(f'Error in email_approvers{e}')
        return {'error': 'An unexpected error occurred'}, 500