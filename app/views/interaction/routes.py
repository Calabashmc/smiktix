from datetime import datetime, timezone
from flask import (
    copy_current_request_context,
    Blueprint,
    render_template,
    request,
    redirect,
    flash,
    g
)

from flask_security import current_user, login_required
from sqlalchemy import select

from . import interaction_bp
from ...api.api_functions import get_subcats
from ...common.sla import calculate_sla_times
from ...common.common_utils import (
    get_highest_ticket_number,
    run_async_in_thread,
    send_notification
)
from ...api.api_lookup_table_functions import get_app_defaults
from ...common.ticket_utils import (
    get_child_tickets,
    get_ticket,
    handle_existing_ticket,
    render_ticket_dashboard,
    save_ticket,
    validate_and_update_ticket
)
from ...model import db
from ...model.lookup_tables import AppDefaults
from ...model.model_interaction import Ticket
from ...model.model_user import User
from ...model.model_notes import Notes
from .form import InteractionForm


@interaction_bp.get("/ui/interaction/ticket/")
@login_required
def interaction_get():
    ticket_number = request.args.get("ticket")
    exists = bool(ticket_number)  # used to hide/unhide tabs on form
    form = InteractionForm()
    children = []
    child_count = 0

    if exists:  # existing ticket
        ticket = handle_existing_ticket(Ticket, ticket_number, form)

        if not ticket:
            flash("Invalid ticket number in URL - defaulting to new ticket", "danger")
            return redirect(f"/ui/interaction/ticket/")

        children = get_child_tickets(Ticket,
                                     ticket_number)  # function in api_functions.py needs Model and ticket_number
        child_count = len(children)
        form.subcategory_id.choices = get_subcats(ticket.category_id)

    else:  # new ticket
        form.created_at.data = datetime.now(timezone.utc)
        created_at_str = form.created_at.data.strftime('%Y-%m-%dT%H:%M')  # format needed for calculate_sla_times

        default_priority = db.session.execute(
            select(AppDefaults.incident_default_priority)
        ).scalar_one()

        respond, resolve = calculate_sla_times(created_at_str, priority=default_priority)  # function in sla.py
        form.sla_respond_by.data = respond
        form.sla_resolve_by.data = resolve
        form.sla_breach = False
        form.ticket_type.data = "Incident"

        # set defaults from database
        defaults = db.session.execute(
            select(AppDefaults)
        ).scalars().first()
        form.priority.data = defaults.incident_default_priority
        form.priority_impact.data = defaults.incident_default_impact
        form.priority_urgency.data = defaults.incident_default_urgency

    return render_template(
        "/interaction/interaction.html",
        form=form,
        highest_number=get_highest_ticket_number(Ticket) - 1,
        exists=exists,
        is_parent=form.is_parent.data,
        children=children,
        child_count=child_count,
        role_names=[role.name for role in current_user.roles],
        model="interaction",
        current_user=current_user,
    )


@interaction_bp.post("/ui/interaction/ticket/")
@login_required
def interaction_post():
    """
    Saves new ticket or updates existing ticket. Uses common functions from ticket_utils.py
    :return: redirect to ticket page
    """
    ticket_number = request.args.get("ticket")
    form = InteractionForm()
    exists = bool(ticket_number)
    ticket = get_ticket(Ticket, ticket_number)
    print(f'ticket type: {form.ticket_type.data}')

    if not validate_and_update_ticket(form, ticket, exists):
        log_exception(f'Invalid JSON data or incorrect Content-Type header')
        redirect(f"/ui/interaction/ticket/")

    if save_ticket(ticket, exists):
        print(f'ticket type: {ticket.ticket_type} and ticket number: {ticket.ticket_number}')
        send_notification(
            ticket_number=ticket.ticket_number,
            ticket_type=ticket.ticket_type,
            exists=exists
        )
        return redirect(f"/ui/interaction/ticket/?ticket={ticket.ticket_number}")

    return redirect(f"/ui/interaction/ticket/")  # should never get here - redirects to dashboard


@interaction_bp.get("/ui/interaction/")
@interaction_bp.get("/ui/interaction/tickets/")
@login_required
def ticket_table():
    """
        calls open_problems function to get list of all open problems owned by the current user
        :return: renders template with table of all problem tickets owned by logged-in user
        """
    return render_ticket_dashboard(Ticket)
