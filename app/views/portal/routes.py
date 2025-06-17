from datetime import datetime, timezone
from flask import Blueprint, render_template, jsonify, redirect, flash
import sqlalchemy as sa
from flask_security import login_required, current_user

from . import portal_bp
from ...common.sla import calculate_sla_times
from ...common.ticket_utils import validate_and_update_ticket, save_ticket
from ...model import db
from ...model.lookup_tables import AppDefaults
from ...model.model_idea import Idea
from ...model.model_interaction import Ticket
from ...model.model_portal import ServiceCatalogue
from ...model.model_user import Team
from ...views.portal.form import PortalForm, PortalTicketForm, PortalIdeasForm, PortalKnowledgeForm



@portal_bp.get('/')
@login_required
def index_get():
    """
    Displays portal page for End Users. Provides capability to log tickets, view their ticket
    status, and search the knowledge base to self-help
    :return:
    """
    defaults = db.session.execute(
        sa.select(AppDefaults)
    ).scalar_one_or_none()

    form = PortalForm()
    form.dash_title = "Welcome to the support centre"
    form.dash_title = "How can we help you today?"
    form.service_desk_phone.data = defaults.servicedesk_phone
    form.service_desk_email.data = defaults.servicedesk_email

    services = db.session.execute(
        sa.select(ServiceCatalogue)
    ).scalars()

    return render_template('portal/index.html',
                           form=form,
                           services=services,
                           exists=True,
                           portal=True
                           )


@portal_bp.post('/')
@login_required
def index_put():
    form = PortalForm()

    if form.validate_on_submit():
        flash('Your support request has been logged', 'success')
        return redirect("/")
    flash(f'Fail! {form.errors}', 'danger')
    return redirect("/")



@portal_bp.get('/portal/my-tickets/')
@login_required
def get_my_tickets():
    form = PortalTicketForm()
    form.created_at.data = datetime.now(timezone.utc)
    form.requested_by.data = current_user.id
    form.created_by_id.data = current_user.id

    return render_template("portal/my-tickets.html",
                           form=form,
                           dash_title="My Tickets",
                           model="Interaction",
                           portal=True
                           )


@portal_bp.post('/portal/my-tickets/')
@login_required
def post_my_tickets():
    exists = False
    form = PortalTicketForm()
    ticket = Ticket()
    respond_by, resolve_by = calculate_sla_times(form.created_at.data, priority=form.priority.data)
    form.sla_respond_by.data = respond_by
    form.sla_resolve_by.data = resolve_by

    if not ticket:
        flash("There was an error saving the ticket", "danger")
        return redirect("/portal/my-tickets/")

    if not validate_and_update_ticket(form, ticket, exists):
        return redirect("/portal/my-tickets/")

    if save_ticket(ticket, exists):
        return redirect("/portal/my-tickets/")

    return redirect("/portal/my-tickets/")


@portal_bp.get('/portal/self-help/')
@login_required
def self_help():
    form = PortalKnowledgeForm()

    return render_template("portal/knowledgebase.html",
                           form=form,
                           dash_title="Knowledgebase",
                           model="Knowledgebase",
                           portal=True
                           )


@portal_bp.get('/portal/ideas/')
@login_required
def get_ideas():
    form = PortalIdeasForm()
    form.created_at.data = datetime.now(timezone.utc)
    form.requester_id.data = current_user.id

    return render_template("portal/ideas.html",
                           form=form,
                           dash_title="Improvement Ideas",
                           model="Ideas",
                           portal=True
                           )


@portal_bp.post('/portal/ideas/')
@login_required
def post_ideas():
    form = PortalIdeasForm()
    idea = Idea()
    form.ticket_type.data = "Idea"
    exists = False
    form.created_by_id.data = current_user.id


    form.support_team_id.data = db.session.execute(
        sa.select(Team.id)
        .where(Team.name == 'Service Desk')
    ).scalar_one_or_none()

    if not idea:
        flash("There was an error saving the ticket", "danger")
        return redirect("/portal/ideas/")

    if not validate_and_update_ticket(form, idea, exists):
        return redirect("/portal/ideas/")

    if save_ticket(idea, exists):
        return redirect("/portal/ideas/")

    return redirect("/portal/ideas/")
