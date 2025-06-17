from datetime import datetime, timezone
from flask import Blueprint, flash, redirect, render_template, request
from flask_security import login_required
from . import idea_bp
from ...views.idea.form import IdeasForm
from ...model import db
from ...model.model_idea import Idea
from ...model.model_notes import Notes
from ...common.common_utils import get_highest_ticket_number
from ...common.ticket_utils import (
    handle_existing_ticket,
    get_ticket,
    render_ticket_dashboard,
    save_ticket,
    validate_and_update_ticket,

)


@idea_bp.get("/ui/idea/ticket/")
@login_required
def idea_get():
    ticket_number = request.args.get("ticket")
    form = IdeasForm()
    exists = bool(ticket_number)
    form.ticket_type.data = "Idea"

    if exists:  # existing ticket
        ticket = handle_existing_ticket(Idea, ticket_number, form)

        if not ticket:
            flash("Invalid ticket number in URL - defaulting to new ticket", "danger")
            return redirect(f"/ui/idea/ticket/")

        voting = bool(ticket.status == "voting")
    else:
        form.ticket_number.data = get_highest_ticket_number(Idea)
        form.created_at.data = datetime.now(timezone.utc)
        form.likelihood.data = "TBD"
        form.vote_count.data = 0
        form.vote_score.data = 0
        voting = False
    return render_template(
        "/idea/idea.html",
        form=form,
        highest_number=get_highest_ticket_number(Idea) - 1,
        exists=exists,
        voting=voting,
        model="idea",
    )


@idea_bp.post("/ui/idea/ticket/")
@login_required
def idea_post():
    """
    Saves new Idea or updates existing. Uses common functions from ticket_utils.py
    :return: redirect to ticket page
    """
    ticket_number = request.args.get("ticket")
    form = IdeasForm()
    exists = bool(ticket_number)
    ticket = get_ticket(Idea, ticket_number)

    if ticket.status == "adopting" and form.resolution_code_id.data:
        ticket.resolution_code_id = form.resolution_code_id.data
        ticket.resolution_notes = form.resolution_journal.data

    if not validate_and_update_ticket(form, ticket, exists):
        return redirect(f"/ui/idea/tickets/")

    if save_ticket(ticket, exists):
        return redirect(f"/ui/idea/ticket/?ticket={ticket.ticket_number}")

    return redirect(f"/ui/idea/ticket/")


@idea_bp.get("/ui/idea/tickets/")
@login_required
def ticket_table():
    """
    :return: renders template with table of all problem tickets owned by logged-in user
    """
    return render_ticket_dashboard(Idea)
