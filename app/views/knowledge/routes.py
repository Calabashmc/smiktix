from datetime import datetime, timezone
from flask import Blueprint, flash, redirect, render_template, request
from jinja2.filters import Markup
from sqlalchemy.exc import SQLAlchemyError
from flask_security import current_user, login_required
from wtforms import BooleanField
from . import knowledge_bp
from ...common.common_utils import get_highest_ticket_number
from ...model import db
from ...model.model_knowledge import KnowledgeBase
from ...model.model_notes import Notes
from ...views.knowledge.form import KnowledgeForm
from ...common.ticket_utils import (
    add_journal_notes,
    handle_existing_ticket,
    get_ticket,
    render_ticket_dashboard,
    save_ticket,
    validate_and_update_ticket
)


@knowledge_bp.get("/ui/knowledge/ticket/")
@login_required
def knowledge_get():
    ticket_number = request.args.get("ticket")
    form = KnowledgeForm()
    exists = bool(ticket_number)

    if exists:  # existing ticket
        ticket = handle_existing_ticket(KnowledgeBase, ticket_number, form)

        if not ticket:
            flash("Invalid ticket number in URL - defaulting to new ticket", "danger")
            return redirect(f"/ui/knowledge/ticket/")

    else:
        form.ticket_type.data = "Knowledge"

    return render_template(
        "/knowledge/knowledge.html",
        form=form,
        highest_number=get_highest_ticket_number(KnowledgeBase) - 1,
        exists=exists,
        model="knowledge",
    )


@knowledge_bp.post("/ui/knowledge/ticket/")
@login_required
def knowledge_post():
    ticket_number = request.args.get("ticket")
    form = KnowledgeForm()
    exists = bool(ticket_number)

    ticket = get_ticket(KnowledgeBase, ticket_number)
    ticket.update_search_vector()

    if not validate_and_update_ticket(form, ticket, exists):
        return redirect(f"/ui/knowledge/ticket/?ticket={ticket.ticket_number}")

    if save_ticket(ticket, exists):
        return redirect(f"/ui/knowledge/ticket/?ticket={ticket.ticket_number}")

    return redirect(f"/ui/knowledge/tickets/")  # should never get here - redirects to dashboard


@knowledge_bp.get("/ui/knowledge/tickets/")
@login_required
def ticket_table():
    """
    calls open_problems function to get list of all open problems owned by the current user
    :return: renders template with table of all problem tickets owned by logged-in user
    """
    return render_ticket_dashboard(KnowledgeBase)