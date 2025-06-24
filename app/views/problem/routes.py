from datetime import datetime, timezone
from flask import Blueprint, flash, render_template, request, redirect
from jinja2.filters import Markup
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from flask_security import current_user, login_required
from wtforms import BooleanField
from . import problem_bp
from .form import ProblemForm
from ...api.api_people_functions import get_support_agents
from ...common.common_utils import get_highest_ticket_number
from ...common.ticket_utils import (
    add_journal_notes,
    get_child_tickets,
    get_ticket,
    handle_existing_ticket,
    populate_related_model_fields,
    populate_requester_details,
    render_ticket_dashboard,
    save_ticket,
    validate_and_update_ticket
)

from ...model import db
from ...model.lookup_tables import AppDefaults, PriorityLookup
from ...model.model_problem import FiveWhysAnalysis, KepnerTregoeAnalysis, Problem
from ...model.model_notes import Notes



@problem_bp.get("/ui/problem/ticket/")
@login_required
def problem_get():
    ticket_number = request.args.get("ticket")
    form = ProblemForm()
    exists = bool(ticket_number)  # used to hide or unhide tabs on form

    children = []
    child_count = 0

    if exists:  # existing ticket
        ticket = handle_existing_ticket(Problem, ticket_number, form)

        if not ticket:
            flash("Invalid ticket number in URL - defaulting to new ticket", "danger")
            return redirect(f"/ui/problem/ticket/")

        # Load related analysis data separately if not already loaded
        if not hasattr(ticket, 'kepner_tregoe') or not hasattr(ticket, 'five_whys'):
            # Reload with relationships
            ticket = db.session.execute(
                sa.select(Problem)
                .where(Problem.ticket_number == ticket_number)
                .options(
                    sa.orm.selectinload(Problem.kepner_tregoe),
                    sa.orm.selectinload(Problem.five_whys)
                )
            ).scalar_one_or_none()

        # Populate related model fields
        populate_analysis_fields(form, ticket)

        children = get_child_tickets(Problem,
                                     ticket_number)  # function in api_functions.py needs Model and ticket_number
        child_count = len(children)  # to display a count of children on the tab

    else:  # new Problem
        default = db.session.execute(select(AppDefaults)).scalar_one_or_none()
        form.ticket_type.data = "Problem"

        priority_details = db.session.execute(select(PriorityLookup).where(
            PriorityLookup.priority == default.problem_default_priority)).scalar_one_or_none()

        form.priority.data = priority_details.priority
        priority_radio = priority_details.id

    return render_template(
        "problem/problem.html",
        form=form,
        highest_number=get_highest_ticket_number(Problem) - 1,
        exists=exists,
        children=children,
        child_count=child_count,
        model="problem",
    )


def populate_analysis_fields(form, ticket):
    """
    Populate form fields from related KepnerTregoeAnalysis and FiveWhysAnalysis models
    """
    print(f"Debug: ticket.kepner_tregoe exists: {hasattr(ticket, 'kepner_tregoe')}")
    print(f"Debug: ticket.five_whys exists: {hasattr(ticket, 'five_whys')}")

    # Populate Kepner-Tregoe Analysis fields
    if hasattr(ticket, 'kepner_tregoe') and ticket.kepner_tregoe:
        print(f"Debug: Populating Kepner-Tregoe fields")
        kt_analysis = ticket.kepner_tregoe
        populate_related_model_fields(form, kt_analysis)

    # Populate Five Whys Analysis fields
    if hasattr(ticket, 'five_whys') and ticket.five_whys:
        print(f"Debug: Populating Five Whys fields")
        five_whys = ticket.five_whys
        populate_related_model_fields(form, five_whys)


@problem_bp.post("/ui/problem/ticket/")
@login_required
def problem_post():
    ticket_number = request.args.get("ticket")
    form = ProblemForm()
    form.ticket_type.data = "Problem"
    exists = bool(ticket_number)

    # Handle main problem ticket
    ticket = get_ticket(Problem, ticket_number)

    if not validate_and_update_ticket(form, ticket, exists):
        db.session.rollback()
        return redirect(f"/ui/problem/ticket/?ticket={ticket.ticket_number}")

    save_analysis(ticket, form, FiveWhysAnalysis)
    save_analysis(ticket, form, KepnerTregoeAnalysis)

    if form.journal.data:
        add_journal_notes(ticket, form.journal.data, is_system=False)

    # Commit all changes if everything succeeded
    if save_ticket(ticket, exists):
        return redirect(f"/ui/problem/ticket/?ticket={ticket.ticket_number}")

    return redirect(f"/ui/problem/tickets/")


def save_analysis(ticket, form, analysis_model):
    """
    Helper function to save analysis forms manually using hasattr/setattr
    """
    if analysis_model == KepnerTregoeAnalysis:
        analysis = ticket.kepner_tregoe
    else:
        analysis = ticket.five_whys

    if not analysis:
        analysis = analysis_model()
        if analysis_model == KepnerTregoeAnalysis:
            ticket.kepner_tregoe = analysis
        else:
            ticket.five_whys = analysis

    # Use the public API to iterate over fields
    for field in form:
        field_name = field.name
        if hasattr(analysis, field_name):
            setattr(analysis, field_name, field.data)

    analysis.problem = ticket
    db.session.add(analysis)



@problem_bp.get("/ui/problem/")
@problem_bp.get("/ui/problem/tickets/")
@login_required
def ticket_table():
    """
    calls open_problems function to get list of all open problems owned by the current user
    :return: renders template with table of all problem tickets owned by logged-in user
    """
    return render_ticket_dashboard(Problem)
