from datetime import datetime, timezone
from flask import Blueprint, flash, redirect, render_template, request
from flask_security import current_user, login_required
from . import release_bp
from .form import ReleaseForm
from ...model.model_release import Release
from ...common.common_utils import get_highest_ticket_number
from ...common.ticket_utils import (
    get_ticket,
    handle_existing_ticket,
    render_ticket_dashboard,
    save_ticket,
    validate_and_update_ticket, populate_relationship_select_choices
)


@release_bp.get('/ui/release/ticket/')
@login_required
def release_get():
    ticket_number = request.args.get('ticket')
    form = ReleaseForm()
    exists = bool(ticket_number)

    if exists:
        ticket = handle_existing_ticket(Release, ticket_number, form)

        if not ticket:
            flash('invalid release number in URL - defaulting to new release', 'danger')
            return redirect(f'/ui/release/ticket/')

        if hasattr(form, 'affected_cis'):  # Release
            form.affected_cis.choices = [
                (node.id, f'{node.ticket_number} | {node.name}') for node in ticket.affected_cis
            ]

        populate_relationship_select_choices(form, ticket, Release)
    else:
        form.created_at.data = datetime.now(timezone.utc)
        form.created_by_id.data = current_user.id
        # form.ticket_number.data = get_highest_ticket_number(Release)
        form.ticket_type.data = "Release"



    return render_template("release/release.html",
                           exists=exists,
                           highest_number=get_highest_ticket_number(Release) - 1,
                           form=form,
                           model="Release",
                           )


@release_bp.post('/ui/release/ticket/')
@login_required
def release_post():
    ticket_number = request.args.get('ticket')
    form = ReleaseForm()
    exists = bool(ticket_number)
    ticket = get_ticket(Release, ticket_number)

    if not validate_and_update_ticket(form, ticket, exists):
        return redirect(f"/ui/release/ticket/?ticket={ticket.ticket_number}")

    if save_ticket(ticket, exists):
        return redirect(f"/ui/release/ticket/?ticket={ticket.ticket_number}")

    return redirect(f"/ui/release/ticket/")


@release_bp.get('/ui/release/')
@release_bp.get('/ui/release/tickets/')
@login_required
def ticket_table():
    """
    Dashboard showing work owned by current user
    :return: renders a template with JavaScript which fetches JSON from api
    """
    return render_ticket_dashboard(Release)
