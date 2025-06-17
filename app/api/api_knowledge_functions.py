from datetime import timezone, datetime

from flask import request, jsonify
from flask_security import login_required
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

from . import api_bp
from ..common.common_utils import get_highest_ticket_number
from ..common.exception_handler import log_exception
from ..common.sla import calculate_sla_times
from ..model import db
from ..model.model_category import Subcategory, Category
from ..model.model_interaction import Ticket, Source
from ..model.model_knowledge import KnowledgeBase
from ..model.lookup_tables import KBATypesLookup, StatusLookup
from ..model.model_user import Team


@api_bp.get('/knowledge/get-knowledge-details/')
@login_required
def get_knowledge_details():
    ticket_number = request.args.get('ticket_number')

    if not ticket_number:
        return jsonify({'error': 'Ticket number is required'}), 400

    article = db.session.execute(
        sa.select(KnowledgeBase)
        .options(
            sa.orm.joinedload(KnowledgeBase.article_type),
            sa.orm.joinedload(KnowledgeBase.category)
        )  # Efficiently loads related data
        .where(KnowledgeBase.ticket_number == ticket_number)
    ).scalars().first()

    if not article:
        return jsonify({'error': 'Article not found'}), 404

    response = {
        'article-type': article.article_type.article_type,
        'article-category': article.category.name,
        'article-details': article.details,
        'short-desc': article.short_desc,
        'ticket-number': article.ticket_number,
        'title': article.title,
    }

    return jsonify(response)


def handle_knowledge_params(stmt, params):
    """
    Handles filtering for Ticket model based on 'params'.
    """
    p_name = params['name']
    p_name = p_name.replace('\n', ' ')

    # p_status = params['status']
    p_filter = params['filter']

    knowledge_types = [
        kba_type.article_type for kba_type in
        db.session.execute(
            sa.select(KBATypesLookup)
        ).scalars().all()
    ]

    knowledge_usefulness = ['useful', 'useless']

    statuses = [
        status.status for status in
        db.session.execute(
            sa.select(StatusLookup)
        ).scalars()
    ]

    ticket_numbers = [
        str(ticket.ticket_number) for ticket in
        db.session.execute(
            sa.select(KnowledgeBase)
            .where(sa.and_(KnowledgeBase.status != 'archived', KnowledgeBase.times_viewed > 0))
        ).scalars()
    ]

    # if p_status in statuses:
    #     stmt = stmt.where(KnowledgeBase.status == p_status)

    if p_filter in knowledge_types:
        stmt = stmt.where(KnowledgeBase.article_type.has(KBATypesLookup.article_type == p_filter))

    if p_name in knowledge_types:
        return stmt.where(
            KnowledgeBase.article_type.has(KBATypesLookup.article_type == p_name)), f"KBA of type '{p_name}'"

    elif p_name in knowledge_usefulness:
        return stmt.where(KnowledgeBase.times_useful > 0), f"KBA with useful feedback"

    elif p_name in statuses:
        return stmt.where(KnowledgeBase.status == p_name), f"KBA with status '{p_name}'"

    elif p_name in ticket_numbers:
        return stmt.where(KnowledgeBase.ticket_number == int(p_name)), f"KBA with ticket number '{p_name}'"

    else:
        return stmt, 'No filtering applied'


@api_bp.post('/knowledge/get-useful-knowledge/')
@login_required
def get_useful_knowledge():
    return KnowledgeBase.get_useful_count()


@api_bp.post('/knowledge/get-top-viewed-knowledge-count/')
@login_required
def get_top_viewed_knowledge():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    result = KnowledgeBase.get_top_viewed_count()
    return result


@api_bp.post('/knowledge/search_published_knowledge/')
@login_required
def search_knowledge():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    search_text = data.get('search_text')

    if search_text is None:
        return jsonify({'error': 'Search text is required'}), 400

    try:
        results = KnowledgeBase.search_published_knowledge_articles(search_text)

        response = [
            {
                'ticket_number': result.ticket_number or 'N/A',
                'short_desc': result.short_desc or 'N/A',
                'title': result.title or 'N/A',
            }
            for result in results
        ]

        return jsonify(response if response else []), 200

    except SQLAlchemyError as e:
        log_exception(f'{e}')
        return jsonify({'error': 'An error occurred during the search'}), 500


@api_bp.get('/get-knowledge-ticket/')
@login_required
def get_knowledge_ticket():
    ticket_number = request.args.get('ticket-number')
    knowledge = db.session.execute(
        sa.select(KnowledgeBase)
        .where(KnowledgeBase.ticket_number == ticket_number)
    ).scalar_one_or_none()

    if not knowledge:
        return jsonify({'error': 'Knowledge Ticket not found'})

        # Helper function to format date-time fields

    def format_datetime(dt):
        return dt.strftime('%Y-%m-%dT%H:%M') if dt else ''

    result = {
        'article-type': knowledge.get_article_type(),
        'author-id': knowledge.get_author_name(),
        'category-id': knowledge.category.name if knowledge.category else '',
        'created_at': knowledge.created_at,
        'created-by': knowledge.get_creator_name(),
        'details': knowledge.details,
        'expires-at': format_datetime(knowledge.expires_at),
        'last-updated': knowledge.last_updated_at,
        'needs-improvement': knowledge.needs_improvement,
        'published-at': format_datetime(knowledge.published_at),
        'review-at': format_datetime(knowledge.review_at),
        'short-desc': knowledge.short_desc,
        'status-select': knowledge.status,
        'ticket-number': knowledge.ticket_number,
        'title': knowledge.title,
        'ticket-type': knowledge.ticket_type,
        'updated_at': format_datetime(knowledge.last_updated_at) or format_datetime(knowledge.created_at),
    }

    return jsonify(result)


@api_bp.post('/knowledge-ticket-info/')
@login_required
def knowledge_ticket_info():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    ticket_number = data['ticket_number']
    knowledge = db.session.execute(
        sa.select(KnowledgeBase)
        .where(KnowledgeBase.ticket_number == ticket_number)
    ).scalar_one_or_none()

    if not knowledge:
        return jsonify({'error': 'Knowledge Ticket not found'})

    result = {
        'category': knowledge.category.name if knowledge.category else '',
        'created': knowledge.created_at.strftime('%H:%M on %b %d %Y '),
        'last-updated': knowledge.last_updated_at,
        'published': knowledge.published_at.strftime('%H:%M on %b %d %Y ') if knowledge.published_at else 'TBD',
        'reviewed': knowledge.review_at.strftime('%H:%M on %b %d %Y ') if knowledge.review_at else 'TBD',
        'useful': knowledge.times_useful,
        'viewed': knowledge.times_viewed
    }

    return jsonify(result)


@api_bp.post('/knowledge/post-kba-improvement/')
@login_required
def post_kba_improvement():
    # Validate and parse request data
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    try:
        # Extract ticket details
        ticket_data = {
            "category_id": db.session.execute(
                sa.select(Category.id)
                .where(Category.name == "Interactions and Requests")
            ).scalars().one_or_none(),
            "details": data["details"],
            "requester_id": data["requester_id"],
            "short_desc": data["short_desc"],
            "source_id": db.session.execute(
                sa.select(Source.id)
                .where(Source.source == "System or API")
            ).scalars().one_or_none(),
            "subcategory_id": db.session.execute(
                sa.select(Subcategory.id)
                .where(Subcategory.name == "Feedback and Suggestions")
            ).scalars().one_or_none(),
            "support_team_id": db.session.execute(
                sa.select(Team.id)
                .where(Team.name == "Service Desk")
            ).scalars().one_or_none(),
            "ticket_type": "Request",
        }

        # Initialize the ticket
        ticket = Ticket(**ticket_data)
        ticket.created_at = datetime.now(timezone.utc)
        ticket.priority_impact = "Low"
        ticket.priority = "P5"
        ticket.priority_urgency = "Low"
        ticket.ticket_number = get_highest_ticket_number(Ticket) + 1
        ticket.status = "new"

        # Calculate SLA times
        ticket.sla_resolve_by, ticket.sla_respond_by = calculate_sla_times(
            ticket.created_at, ticket.priority
        )

        # Save to the database
        db.session.add(ticket)
        db.session.commit()
        return jsonify({"message": "Ticket created successfully", "ticket_id": ticket.id}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except KeyError as e:
        return jsonify({"error": str(e)}), 400
    except SQLAlchemyError as e:
        db.session.rollback()  # Ensure database consistency
        return jsonify({"error": f"An internal server error occurred {e}"}), 500


@api_bp.get('/knowledge/increment-knowledge-useful-count/')
@login_required
def increment_knowledge_useful_count():
    ticket_number = request.args.get('ticket_number')

    if not ticket_number:
        return jsonify({'error': 'Ticket number required'}), 400

    article = db.session.execute(
        sa.select(KnowledgeBase)
        .where(KnowledgeBase.ticket_number == ticket_number)
    ).scalar_one_or_none()

    if not article:
        return jsonify({'error': 'Record not found'}), 400
    article.times_useful += 1

    try:
        db.session.commit()
        return jsonify({'success': 'Times useful incremented'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()  # Ensure database consistency
        return jsonify({"error": f"An internal server error occurred {e}"}), 500


@api_bp.get('/knowledge/increment-knowledge-viewed-count/')
@login_required
def increment_knowledge_viewed_count():
    ticket_number = request.args.get('ticket_number')

    if not ticket_number:
        return jsonify({'error': 'Ticket number required'}), 400

    article = db.session.execute(
        sa.select(KnowledgeBase)
        .where(KnowledgeBase.ticket_number == ticket_number)
    ).scalar_one_or_none()

    if not article:
        return jsonify({'error': 'Record not found'}), 400

    article.times_viewed += 1

    try:
        db.session.commit()
        return jsonify({'success': 'Times useful incremented'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()  # Ensure database consistency
        return jsonify({"error": f"An internal server error occurred {e}"}), 500