import os
from datetime import datetime, timezone
import threading
import asyncio

from flask_mailing import Message
from flask import copy_current_request_context, current_app, flash, jsonify, render_template, url_for
from flask_security import current_user
import sqlalchemy as sa

from . import mail
from ..model import db
from ..model.model_category import Category
from ..model.model_change import Change
from ..model.model_idea import Idea
from ..model.model_knowledge import KnowledgeBase
from ..model.model_notes import CommsJournal, Notes
from ..model.model_portal import PortalAnnouncements
from ..model.model_problem import Problem
from ..model.model_release import Release
from ..model.model_user import Team
from ..model.model_interaction import Source, Ticket
from ..model.model_user import Department, Role, User
from ..model.model_cmdb import CmdbConfigurationItem
from ..model.lookup_tables import (
    BenefitsLookup,
    ChangeTypeLookup,
    ChangeWindowLookup,
    LikelihoodLookup,
    KBATypesLookup,
    OfficeHours,
    PriorityLookup,
    ResolutionLookup,
    RiskLookup,
    StatusLookup
)


def get_highest_ticket_number(model):
    '''
    set ticket number sequence starts at 1001
    if no records yet set to 1001 else set to last ticket number plus 1
    :param: stip_length: length of Ticket_number prefix. Used to strip prefix to get just number
    :dbmodel: the Model to query
    :return: new ticket number
    '''
    last_number = db.session.execute(
        sa.select(sa.func.max(model.ticket_number))
    ).scalar_one_or_none()

    return last_number + 1 if last_number else 1001


def get_email_addresses(users):
    '''
    gets the users email address
    :param users: the list of users
    :return: a list of email addresses
    '''
    addresses = []
    for user_name in users:
        addresses.append(user_name.email)

    return ', '.join(addresses)


def check_sla_breach():
    '''
    Checks for SLA Respond and Resolve breach and updates ticket Boolean for dashboard display
    :return: Nothing but ticket should be updated if SLA breached else does nothing
    '''
    all_open = db.session.execute(
        sa.select(Ticket)
        .where(Ticket.status != 'closed')
    ).scalars().all()

    for ticket in all_open:
        if ticket.sla_respond_by < datetime.now(timezone.utc):
            ticket.sla_response_breach = True
        else:
            ticket.sla_response_breach = False

        if ticket.sla_resolve_by < datetime.now(timezone.utc):
            ticket.sla_resolve_breach = True
        else:
            ticket.sla_resolve_breach = False

        db.session.commit()


def run_async_in_thread(coro):
    '''
    Run an async coroutine in a separate thread with Flask request context.
    '''

    @copy_current_request_context  # Copy the current request context to the background task
    def thread_function():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        except Exception as e:
            log_exception(f'Error in async background task: {e}')
        finally:
            loop.close()

    thread = threading.Thread(target=thread_function)
    thread.start()


def get_endpoint(model):
    endpoint_mapping = {
        'ticket': 'interaction_bp.interaction_get',
        'interaction': 'interaction_bp.interaction_get',
        'incident': 'interaction_bp.interaction_get',
        'request': 'interaction_bp.interaction_get',
        'change': 'change_bp.change_get',
        'idea': 'idea_bp.idea_get',
        'knowledge': 'knowledge_bp.knowledge_get',
        'problem': 'problem_bp.problem_get',
        'cmdbconfigurationitem': 'cmdb_bp.cmdb_get',
        'hardware': 'cmdb_bp.cmdb_get',
        'software': 'cmdb_bp.cmdb_get',
        'service': 'cmdb_bp.cmdb_get',
    }
    return endpoint_mapping.get(model.lower())


def send_notification(
        ticket_number,
        ticket_type,
        template='ticket-notify.html',
        subject_line=None,
        body_text=None,
        exists=True,
        addresses=None):
    '''
    Send email notifications via background task.
    '''
    from ..model.lookup_tables import AppDefaults
    model = get_model(ticket_type)

    ticket = db.session.execute(
        sa.select(model)
        .where(model.ticket_number == ticket_number)
    ).scalars().first()

    if not ticket:
        raise ValueError(f'Ticket with ticket number {ticket_number} not found')

    if not subject_line:
        subject_line = 'Updated' if exists else 'Created'

    subject = f'{ticket.ticket_type}-{ticket.ticket_number}: {subject_line}'

    endpoint = get_endpoint(ticket_type)

    ticket_url = url_for(
        endpoint,
        _external=True,
        ticket=ticket.ticket_number
    )

    if not addresses:
        addresses = [ticket.requester.email]
    # Create template parameters dictionary
    template_params = {
        'name': ticket.requester.full_name,
        'ticket_number': f'{ticket.ticket_type}-{ticket.ticket_number}',
        'status': ticket.status,
        'support_team': ticket.support_team.name,
        'priority': ticket.priority,
        'resolve_by': ticket.sla_resolve_by.strftime('%H:%M on %b %d'),
        'time_stamp': ticket.created_at.isoformat(),
        'ticket_url': ticket_url,
        'service_desk_phone': db.session.execute(sa.select(AppDefaults.servicedesk_phone)).scalar_one_or_none(),
        'body_text': body_text
    }

    message = Message(
        subject=subject,
        recipients=addresses,
        template_body=template_params,
    )

    try:
        send_email(subject, addresses, template=template, template_params=template_params)
    except Exception as e:
        log_exception(f'{e}')
        flash(f'Error sending email: {str(e)}')
        raise


async def send_email_async(subject, addresses, template=None, template_params=None, attachments=None):
    '''
    Send email using Flask-Mailing asynchronously
    :param subject: The subject of the email
    :param addresses: List of recipient email addresses
    :param template: Name of the template file (optional)
    :param template_params: Dictionary of parameters to be used in the template (optional)
    :param attachments: List of file paths or tuples for attachments (optional)
    :return: None
    '''
    if template_params is None:
        template_params = {}

    if attachments is None:
        attachments = []

    message = Message(
        subject=subject,
        recipients=addresses,
        template_body=template_params,
        attachments=attachments
    )

    try:
        await mail.send_message(message, template_name=template)
    except Exception as e:
        log_exception(f'{e}')
        flash(f'Error sending email: {str(e)}')
        raise


def send_email(subject, addresses, template=None, template_params=None, attachments=[]):
    '''
    Initiate the sending of an email asynchronously.
    '''
    run_async_in_thread(
        send_email_async(subject, addresses, template, template_params, attachments)
    )


def my_teams():
    '''
    Uses current logged-in user id to query the User model for teams they are in
    :return: list of teams
    '''
    user = db.session.execute(
        sa.select(User)
        .where(User.id == current_user.id)
    ).scalars().one_or_none()

    return user.team


def my_teams_dashboard(model, page, team_name, ticket_type):
    '''
    Fetches tickets assigned to the current user, filtering by their team and ticket type.

    :param model: This is Ticket, Problem, or Change.
    :param page: pagination page number
    :param team_name: Team model (not used in the query, might be used for other logic)
    :param ticket_type: 'incident', 'request', 'problem', 'change', or 'any'
    :return: paginated tickets based on user, team, and ticket type
    '''
    filters = [
        model.status != 'closed',
        model.status != 'resolved',
        model.supporter == current_user
    ]

    if ticket_type != 'any':
        filters.append(model.ticket_type == ticket_type.capitalize())

    paginated_results = db.session.execute(
        sa.select(model)
        .where(sa.and_(*filters))
        .order_by(model.ticket_number)
    ).scalars().paginate(
        page=page,
        per_page=current_app.config['ROWS_PER_PAGE'],
        error_out=False
    )

    return paginated_results


def get_model(model):
    '''
    Provides the database model to use for various ticket functions.
    :param model: A text variable from which to determine the model to return.
    :return: The Flask-SQLAlchemy model that can be queried, or None if not recognized.
    '''
    model = model.lower()

    model_mapping = {
        # Category model
        'category': Category,

        # Change-related models
        'change': Change,
        'emergency': Change,
        'normal': Change,
        'standard': Change,
        'change_risk_lookup': RiskLookup,
        'change_type_lookup': ChangeTypeLookup,
        'change_window_lookup': ChangeWindowLookup,

        # CMDB models
        'cmdb': CmdbConfigurationItem,
        'hardware': CmdbConfigurationItem,
        'software': CmdbConfigurationItem,
        'service': CmdbConfigurationItem,

        # Department model
        'department': Department,

        # Idea-related models
        'idea': Idea,
        'ideas': Idea,
        'idea_benefit_lookup': BenefitsLookup,
        'idea_likelihood_lookup': LikelihoodLookup,

        # Release model
        'release': Release,

        # Team model
        'team': Team,

        # Ticket-related models
        'interaction': Ticket,
        'incident': Ticket,
        'request': Ticket,
        'ticket': Ticket,

        # Knowledge Base models
        'kba_type_lookup': KBATypesLookup,
        'knowledge': KnowledgeBase,

        # Office Hours model
        'office_hours': OfficeHours,

        # Priority model
        'priority_lookup': PriorityLookup,

        # Problem-related models
        'problem': Problem,
        'workaround': Problem,
        'known error': Problem,

        # Role model
        'role': Role,

        # Source model
        'source': Source,

        # Status model
        'status_lookup': StatusLookup,
        'resolution_lookup': ResolutionLookup,
        # User models
        'user': User,
        'users': User,
    }

    return model_mapping.get(model)
