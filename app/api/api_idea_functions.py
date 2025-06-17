from flask import request, jsonify
from flask_security import current_user, login_required

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from ..common.exception_handler import log_exception
from ..model import db
from ..model.model_category import Category
from ..model.model_idea import Idea
from ..model.model_user import User
from ..model.lookup_tables import LikelihoodLookup, StatusLookup
from . import api_bp


def handle_idea_params(stmt, params):
    """
    Handles filtering based on 'params'.
    """
    p_name = params['name']
    p_name = p_name.replace('\n', ' ')

    categories = [category.name for category in db.session.execute(sa.select(Category)).scalars()]

    likelihoods = [
        likelihood.likelihood for likelihood in
        db.session.execute(
            sa.select(LikelihoodLookup)
        ).scalars()
    ]

    statuses = [
        status.status for status in
        db.session.execute(
            sa.select(StatusLookup)
        ).scalars()
    ]

    if p_name in categories:
        return stmt.where(Idea.category.has(Category.name == p_name)), f"By category {p_name}"

    elif p_name in likelihoods:
        return stmt.where(Idea.likelihood == p_name) , f"By likelihood '{p_name}'"

    elif p_name in statuses:
        return stmt.where(Idea.status == p_name), f"By status {p_name}"

    else:
        return stmt, 'No filtering applied'


@api_bp.post('/idea_vote/')
@login_required
def idea_vote():
    data = request.get_json(silent=True) or {}
    ticket_number = int(data['ticket-number'])
    vote_score = int(data['vote-score'])
    user = db.session.get(User, current_user.id)

    voted_on = False

    idea = db.session.execute(
        sa.select(Idea)
        .where(Idea.ticket_number == ticket_number)
    ).scalar_one_or_none()

    if idea.status != 'voting':
        return jsonify({'status': idea.status})

    my_idea = True if idea.requester_id == user.id else False

    if not my_idea:
        # Check if the user has already voted for the idea
        if user not in idea.voters:
            idea.voters.append(user)
        else:
            voted_on = True

        if not voted_on:
            idea.vote_count += 1
            score = idea.vote_score + vote_score
            if score < 0:
                idea.vote_score = 0
            else:
                idea.vote_score = score

            try:
                likelihood = idea.vote_count / idea.vote_score
                if likelihood < 0.6:
                    idea.likelihood = 'Likely'  # likely the idea will be +60%
                elif likelihood > 110:
                    idea.likelihood = 'Unlikely'  # unlikely - the idea will be sub 40%
                else:
                    idea.likelihood = 'Possible'  # possible - the idea will be mid-range
            except ZeroDivisionError:
                idea.likelihood = 'Unlikely'  # unlikely - the idea will have votes but zero score

    response = {'count': idea.vote_count,
                'score': idea.vote_score,
                'my-idea': my_idea,
                'already-voted': voted_on,
                'likelihood': idea.likelihood,
                }

    try:
        db.session.commit()
        return jsonify(response), 200
    except SQLAlchemyError as e:
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500


@api_bp.get('/idea/get-idea/')
@login_required
def get_idea():
    ticket_number = request.args.get('ticket-number')

    idea = db.session.execute(
        sa.select(Idea)
        .options(
            joinedload(Idea.category),
            joinedload(Idea.requester)
        )
        .where(sa.and_(Idea.ticket_number == ticket_number))
    ).scalars().one_or_none()

    benefits = [str(benefit.id )for benefit in idea.benefits]
    impacts = [str(impact.id) for impact in idea.impact]

    if idea:
        result = {
            'benefits': benefits,
            'category': idea.category.name if idea.category else '',
            'created_at': idea.created_at,
            'created-by': idea.created_by_id,
            'current-issue': idea.current_issue,
            'cost': idea.estimated_cost,
            'details': idea.details,
            'dependencies': idea.dependencies,
            'effort': idea.estimated_effort,
            'impacts': impacts,
            'likelihood': idea.likelihood,
            'requested-by': idea.get_requester_name(),
            'risks': idea.risks_challenges,
            'short-desc': idea.short_desc,
            'ticket-number': idea.ticket_number,
            'ticket-type': idea.ticket_type,
            'status-select': idea.status,
            'vote-count': idea.vote_count,
            'vote-score': idea.vote_score,
        }
    else:
        result = {}

    return jsonify(result)


@api_bp.post('/get-likelihood-count/')
@login_required
def get_likelihood_count():
    return Idea.likelihood_count()
