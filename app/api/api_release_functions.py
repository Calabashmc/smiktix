
from flask import g, request, jsonify
from flask_security import login_required
import sqlalchemy as sa

from . import api_bp
from ..model import db
from ..model.model_category import Category
from ..model.model_release import Release, ReleaseTypesLookup
from ..model.lookup_tables import KBATypesLookup, StatusLookup
from ..model.model_user import Team


@api_bp.get('/get_release_details/')
@login_required
def get_release_details():
    response = {}
    ticket_number = request.args.get('ticket_number')

    article = db.session.execute(
        sa.select(Release)
        .where(Release.ticket_number == ticket_number)
    ).scalars().first()

    article_type = db.session.execute(
        sa.select(KBATypesLookup)
        .where(KBATypesLookup.id == article.article_type)
    ).scalars().first()

    response['release-category'] = article.category.name
    response['release-created'] = article.created_at.strftime('%B %Y')
    response['release-details'] = article.details
    response['article-type'] = article_type.type
    response['release-review'] = article.review_at.strftime('%B %Y')
    response['status'] = article.status
    response['release-title'] = article.title

    return jsonify(response)


def handle_release_params(stmt, params):
    """
    Handles filtering for Ticket model based on 'params'.
    """
    # Fetch statuses, and teams as sets
    p_name = params['name']
    p_name = p_name.replace('\n', ' ')

    categories = [category.name for category in db.session.execute(sa.select(Category)).scalars()]

    statuses = [
        status.status for status in
        db.session.execute(
            sa.select(StatusLookup)
        ).scalars()
    ]

    release_types = [
        release_type.release_type for release_type in
        db.session.execute(
            sa.select(ReleaseTypesLookup)
        ).scalars()
    ]

    teams = [
        team.name for team in db.session.execute(
            sa.select(Team)
        ).scalars()
    ]

    # Apply filtering based on params
    if p_name in statuses:
        return stmt.where(Release.status == p_name), f"By status {p_name}"

    elif p_name in teams:
        return stmt.where(Release.support_team.has(name=p_name)), f"By team {p_name}"

    elif p_name in categories:
        return stmt.where(Release.category.has(Category.name == p_name)), f"By category {p_name}"

    elif p_name in release_types:
        return stmt.where(Release.release_type.has(ReleaseTypesLookup.release_type == p_name)), f"By type {p_name}"

    elif p_name not in ['All']:
        return stmt.where(Release.release_type == p_name), f"By type {p_name}"
    else:
        return stmt, 'No filtering applied'


@api_bp.get('/release/get-release-ticket/')
@login_required
def get_release_ticket():
    ticket_number = request.args.get('ticket-number')
    if not ticket_number:
        return jsonify({'error': 'Ticket number not provided'}), 400

    release = db.session.execute(
        sa.select(Release)
        .where(Release.ticket_number == ticket_number)
    ).scalar_one_or_none()

    if not release:
        return jsonify({'error': 'Release Ticket not found'})

    def format_datetime(dt):
        return dt.strftime(g.datetime_format) if dt else ''

    result = {
        'category-id': release.category.name if release.category else '',
        'created_at': release.created_at,
        'created-by': release.get_creator_name(),
        'details': release.details,
        'last-updated': release.last_updated_at,
        'short-desc': release.short_desc,
        'status-select': release.status,
        'ticket-number': release.ticket_number,
        'title': release.title,
        'ticket-type': release.ticket_type,
        'updated_at': format_datetime(release.last_updated_at) or format_datetime(release.created_at),
    }
    return jsonify(result)


@api_bp.post('/release-ticket-info/')
@login_required
def release_ticket_info():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    ticket_number = data['ticket_number']
    release = db.session.execute(
        sa.select(Release)
        .where(Release.ticket_number == ticket_number)
    ).scalar_one_or_none()

    if not release:
        return jsonify({'error': 'Knowledge Ticket not found'})

    result = {
        'category': release.category.name if release.category else '',
        'created': release.created_at.strftime('%H:%M on %b %d %Y '),
        'last-updated': release.last_updated_at,
    }

    return jsonify(result)


@api_bp.post('/get-releases-by-category/')
@login_required
def get_releases_by_category():
    """
    For graphing by cis category
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    scope = data.get('scope')

    return Release.category_counts(scope)
