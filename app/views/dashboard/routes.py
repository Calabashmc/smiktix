from flask import render_template
from flask_security import login_required, current_user
import sqlalchemy as sa
from . import dashboard_bp
from .form import DashboardForm
from ...common.common_utils import get_highest_ticket_number, check_sla_breach
from ...model import db
from ...model.model_interaction import Ticket
from ...model.model_user import Team, User


@dashboard_bp.get('/ui/dashboard/dashboard/')
@login_required
def dashboard():
    form = DashboardForm()
    form.dash_title = "Dashboard"
    form.dash_subtitle = "Current Work Load"

    check_sla_breach()  # Update SLA breach flags

    # Total tickets
    total = db.session.execute(
        sa.select(sa.func.count())
        .select_from(Ticket)
        .where(Ticket.status != 'closed')
    ).scalar()

    # Fetch agents and their ticket counts
    agents_with_counts = db.session.execute(
        sa.select(
            User.id,
            User.full_name,
            User.team_id,
            Team.name,
            sa.func.count(Ticket.id)
        )
        .join(Ticket, User.id == Ticket.supporter_id)
        .join(Team, User.team_id == Team.id, isouter=True)
        .where(Ticket.status != 'Closed')
        .group_by(User.id, User.full_name, User.team_id, Team.name)
    ).all()

    agent_tickets = [
        {
            'supporter': full_name,
            'ticket_count': ticket_count,
            'percent': round(ticket_count / total * 100) if total else 0,
            'team': team_name or "No Team"
        }
        for user_id, full_name, team_id, team_name, ticket_count in agents_with_counts
    ]

    # Fetch team ticket counts and names
    all_teams = db.session.execute(
        sa.select(Ticket.support_team_id)
        .where(Ticket.support_team_id.isnot(None))
        .distinct()
    ).scalars().all()

    team_counts = db.session.execute(
        sa.select(Ticket.support_team_id, sa.func.count())
        .where(Ticket.support_team_id.isnot(None))
        .group_by(Ticket.support_team_id)
    ).all()

    team_names = db.session.execute(
        sa.select(Team.id, Team.name)
        .where(Team.id.in_(all_teams))
    ).all()

    team_name_dict = {team_id: name for team_id, name in team_names}
    team_count_dict = {team_id: count for team_id, count in team_counts}

    team_tickets = [
        {
            'team': team_name_dict.get(team_id, "Unknown"),
            'ticket_count': team_count_dict.get(team_id, 0),
            'percent': round(team_count_dict.get(team_id, 0) / total * 100) if total else 0
        }
        for team_id in all_teams
    ]

    # Reusable helper for ticket counts
    def count_tickets(filter_conditions):
        return db.session.execute(
            sa.select(sa.func.count())
            .select_from(Ticket)
            .where(*filter_conditions)
        ).scalar() or 0

    # Specific ticket counts
    incidents_total_open = count_tickets([Ticket.status != 'closed', Ticket.ticket_type == 'Incident'])
    requests_total_open = count_tickets([Ticket.status != 'closed', Ticket.ticket_type == 'Request'])
    open_sla_respond_breach = count_tickets([Ticket.sla_response_breach, Ticket.status != 'closed'])
    open_sla_resolve_breach = count_tickets([Ticket.sla_resolve_breach, Ticket.status != 'closed'])

    return render_template('dashboard/dashboard.html',
                           incidents_total_open=incidents_total_open,
                           requests_total_open=requests_total_open,
                           open_sla_respond_breach=open_sla_respond_breach,
                           open_sla_resolve_breach=open_sla_resolve_breach,
                           form=form,
                           agent_tickets=agent_tickets,
                           team_tickets=team_tickets,
                           total_tickets=total,
                           highest_number=get_highest_ticket_number(Ticket))

