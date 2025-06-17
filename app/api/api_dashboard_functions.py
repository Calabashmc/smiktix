from collections import Counter
from flask import request, jsonify
from flask_security import login_required
import sqlalchemy as sa
from . import api_bp
from ..model import db
from ..model.model_change import Change
from ..model.model_knowledge import KnowledgeBase
from ..model.model_interaction import Ticket
from ..model.model_problem import Problem
from ..model.model_release import Release
from ..model.model_user import Team
from ..common.common_utils import get_model
from ..model.common_methods import get_priority_counts, get_status_counts, get_ticket_type_count

@api_bp.post('/get-open-tickets-priority-count/')
@login_required
def get_open_tickets_priority_count():
    """
    Used for Interaction, Problem, and Change dashboards to show open ticket count in graphs
    return: dict of ticket_types with a count
    """
    data = request.get_json(silent=True) or {}
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    scope = data.get('scope')
    ticket_type = data.get('ticket_type')

    if ticket_type == ['Problem', 'Known Error', 'Workaround']:
        model = Problem
    else:
        model = get_model(data.get('model'))

    if model == Change:
        counts_dict = Change.change_risk_count(ticket_type, scope)
    elif model == Problem:
        known_error_dict = get_priority_counts(model, 'Known Error', scope)
        workaround_dict = get_priority_counts(model, 'Workaround', scope)
        problems_dict = get_priority_counts(model, 'Problem', scope)
        counts_dict = dict(Counter(known_error_dict) + Counter(workaround_dict) + Counter(problems_dict))
    else:
        counts_dict = get_priority_counts(model, ticket_type, scope)

    return counts_dict


@api_bp.post('/get-open-tickets-category-count/')
@login_required
def get_open_tickets_category_count():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    model = get_model(data.get('model'))

    counts_dict = model.tickets_category_count()
    return counts_dict


@api_bp.post('/get-open-by-type-count/')
@login_required
def get_open_by_type_count():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400
    print(data)
    model = get_model(data.get('model'))
    scope = data.get('scope')
    counts_dict = {}

    if model in [Ticket, Problem]:
        counts_dict = get_ticket_type_count(model, scope)

    elif model == Change:
        counts_dict = Change.change_type_count(scope)

    elif model == KnowledgeBase:
        counts_dict = KnowledgeBase.article_type_count(scope)

    elif model == Release:
        counts_dict = Release.release_type_count(scope)

    return counts_dict


@api_bp.post('/get-open-tickets-status-count/')
@login_required
def get_open_ticket_status_count():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    scope = data.get('scope')
    model = get_model(data.get('model'))

    counts_dict = get_status_counts(model, scope)

    return counts_dict


@api_bp.post('/get-team-load/')
@login_required
def get_team_load():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    load = {}

    # Get all teams
    all_teams = db.session.scalars(
        sa.select(Team.name)
    ).all()

    # Initialize the load dictionary with empty counts
    for team_name in all_teams:
        load[team_name] = {
            'incidents': 0,
            'requests': 0,
            'changes': 0,
            'problems': 0
        }

    # Get incidents count per team
    incidents = db.session.execute(
        sa.select(Team.name, sa.func.count(Ticket.id))
        .join(Ticket, Team.id == Ticket.support_team_id)
        .where(sa.and_(Ticket.status != 'closed', Ticket.ticket_type == 'Incident'))
        .group_by(Team.name)
    ).all()

    for team_name, count in incidents:
        load[team_name]['incidents'] = count

    # Get requests count per team
    requests = db.session.execute(
        sa.select(Team.name, sa.func.count(Ticket.id))
        .join(Ticket, Team.id == Ticket.support_team_id)
        .where(sa.and_(Ticket.status != 'closed', Ticket.ticket_type == 'Request'))
        .group_by(Team.name)
    ).all()

    for team_name, count in requests:
        load[team_name]['requests'] = count

    # Get changes count per team
    changes = db.session.execute(
        sa.select(Team.name, sa.func.count(Change.id))
        .join(Change, Team.id == Change.support_team_id)
        .where(sa.or_(Change.status == 'cab', Change.status == 'implement'))
        .group_by(Team.name)
    ).all()

    for team_name, count in changes:
        load[team_name]['changes'] = count

    # Get problems count per team
    problems = db.session.execute(
        sa.select(Team.name, sa.func.count(Problem.id))
        .join(Problem, Team.id == Problem.support_team_id)
        .group_by(Team.name)
    ).all()

    for team_name, count in problems:
        load[team_name]['problems'] = count

    return jsonify(load), 200