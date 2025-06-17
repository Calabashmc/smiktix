from datetime import datetime
from flask import request, jsonify
from flask_security import login_required
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

from ..common.exception_handler import log_exception
from ..model import db
from ..model.model_category import Category
from ..model.model_cmdb import CmdbConfigurationItem, ChangeFreeze
from ..model.lookup_tables import Compliance, Importance
from ..common.ticket_utils import datetime_to_string, date_to_string
from . import api_bp


def handle_cmdb_params(stmt, params):
    """
    Handles filtering for Ticket model based on 'params'.
    """
    p_name = params['name']
    p_name = p_name.replace('\n', ' ')

    cmdb = db.session.execute(
            sa.select(CmdbConfigurationItem)
            .where(CmdbConfigurationItem.status != 'disposed')
        ).scalars()

    ci_categories = [ticket.category.name for ticket in cmdb]
    importance = [ticket.importance for ticket in db.session.execute(sa.select(Importance)).scalars()]
    statuses = [ticket.status for ticket in cmdb]
    ticket_types = [ticket.ticket_type for ticket in cmdb]

    if p_name in ci_categories:
        return stmt.where(
            CmdbConfigurationItem.category.has(Category.name == p_name)), f'CI with category "{p_name}"'
    elif p_name in statuses:
        return stmt.where(CmdbConfigurationItem.status == p_name), f"Change with status '{p_name}'"
    elif p_name in ticket_types:
        return stmt.where(CmdbConfigurationItem.ticket_type == p_name), f"Change with ticket type '{p_name}'"
    elif p_name in importance:
        return stmt.where(CmdbConfigurationItem.importance.has(Importance.importance == p_name)), f"Change with metallic '{p_name}'"
    else:
        return stmt, 'No filtering applied'


@api_bp.post('/get-cmdb-cis-by-category/')
@login_required
def get_cmdb_cis_by_category():
    """
    For graphing by cis category
    """
    return CmdbConfigurationItem.category_counts()


@api_bp.post('/get-cmdb-cis-by-importance/')
@login_required
def get_cmdb_cis_by_importance():
    """
    For graphing by cis importance
    """
    return CmdbConfigurationItem.importance_counts()


@api_bp.post('/get-cmdb-cis-by-ticket-type/')
@login_required
def get_cmdb_cis_by_ticket_type():
    """
    For graphing by cis type
    """
    return CmdbConfigurationItem.ticket_type_counts()


@api_bp.get('/get-cmdb-ticket/')
@login_required
def get_cmdb_ticket():
    ticket_number = request.args.get('ticket-number')
    cmdb = (db.session.execute(
        sa.select(CmdbConfigurationItem)
        .options(
            sa.orm.joinedload(CmdbConfigurationItem.category),
            sa.orm.joinedload(CmdbConfigurationItem.owner)
        )
        .where(CmdbConfigurationItem.ticket_number == ticket_number))
            .scalars().one_or_none())

    if cmdb:
        result = {
            'asset-tag': getattr(cmdb, 'asset_tag', ''),
            'brand': cmdb.brand,
            'category-id': cmdb.category.name if cmdb.category_id else '',
            'created_at': datetime_to_string(cmdb.created_at),
            'created-by': cmdb.created_by.full_name,
            'details': cmdb.details,
            'disposed-date': date_to_string(cmdb.disposed_date),
            'importance': cmdb.importance.importance if cmdb.importance else '',
            'install-date': date_to_string(cmdb.install_date),
            'name': cmdb.name,
            'model': getattr(cmdb, 'model', ''),
            'obtained-date': date_to_string(cmdb.obtained_date),
            'ticket-number': cmdb.ticket_number,
            'ticket-type': cmdb.ticket_type,
            'replacement-date': date_to_string(cmdb.replacement_date),
            'replaced-with': getattr(cmdb, 'replaced_with_id', ''),
            'owner': cmdb.owner.full_name,
            'retired-date': date_to_string(cmdb.retirement_date),
            'serial-number': getattr(cmdb, 'serial_number', ''),
            'status-select': cmdb.status,
            'support-team': cmdb.support_team.name if cmdb.support_team else '',
        }
    else:
        result = {}
    return jsonify(result)


@api_bp.post('/cmdb/save_ci_relationship/')
@login_required
def save_ci_relationship():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    action = data['action']  # either add or remove
    related_node = data['node']  # in the format 1001 | Server01
    related_node_id = related_node['node_id']

    direction = data['direction']  # either upstream or downstream

    ci = db.session.execute(
        sa.select(CmdbConfigurationItem)
        .where(CmdbConfigurationItem.ticket_number == data['ticket_number'])
    ).scalar_one_or_none()

    node = db.session.execute(
        sa.select(CmdbConfigurationItem)
        .where(CmdbConfigurationItem.id == related_node_id)
    ).scalar_one_or_none()

    if ci and node:
        if direction == 'upstream':
            ci.upstream.append(node) if action == 'add' else ci.upstream.remove(node)

        if direction == 'downstream':
            ci.downstream.append(node) if action == 'add' else ci.downstream.remove(node)

        try:
            db.session.commit()
            return jsonify({'success': 'Relationship saved'}), 200
        except SQLAlchemyError as e:
            log_exception(f'Database error: {e}')
            return jsonify({'error': 'Database error: ' + str(e)}), 500

    return jsonify({'error': 'No ci or node'}), 400


@api_bp.post('/cmdb/save_service_relationships/')
@login_required
def save_service_relationships():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    action = data['action']  # either add or remove
    related_node = data.get('node')  # in the format 1001 | Server01

    ticket_number = data.get('ticket_number')

    if not ticket_number:
        return jsonify({'error': 'Ticket number is required'}), 400

    if related_node is None:
        return jsonify({'error': 'Node is required'}), 400

    related_node_ticket_number = related_node['node_text'].split('|')[0]

    ci = db.session.execute(
        sa.select(CmdbConfigurationItem)
        .where(CmdbConfigurationItem.ticket_number == ticket_number)
    ).scalar_one_or_none()

    node = db.session.execute(
        sa.select(CmdbConfigurationItem)
        .where(CmdbConfigurationItem.ticket_number == related_node_ticket_number)
    ).scalar_one_or_none()

    if ci and node:
        if action == 'add':
            if ci not in node.services:
                node.services.append(ci)
        elif action == 'remove':
            if ci in node.services:
                node.services.remove(ci)

        try:
            db.session.commit()
            return jsonify('success', 'Relationship saved'), 200
        except SQLAlchemyError as e:
            log_exception(f'Database error: {e}')
            return jsonify({'error': 'Database error: ' + str(e)}), 500

    return jsonify({'error': 'No such service or node'}), 400


@api_bp.get('/get_cmdb_categories/')
@login_required
def get_cmdb_categories():
    """
    Populate choices for CMDB categories
    """
    options = [(0, 'All')]
    cmdb_categories = db.session.execute(
        sa.select(Category)
        .where(Category.cmdb.is_(True))
    ).scalars().all()

    for ci in cmdb_categories:
        options.append((ci.id, ci.name))
    options.sort()
    return jsonify({'categories': options})


@api_bp.get('/get_ci_id/')
@login_required
def get_ci_id():
    name = request.args.get('name')
    # Name might not be unique. ot ideal but this is the only way I can think
    # to get an id to then use the next api function to get an icon
    response = db.session.execute(
        sa.select(CmdbConfigurationItem)
        .where(CmdbConfigurationItem.name == name)
    ).scalar_one_or_none()

    return jsonify({'id': response.id})


@api_bp.get('/get_ci_ticket_number/')
@login_required
def get_ci_ticket_number():
    """
    Returns the ticket_number of a configuration item for a give id
    used for double click vis.js on network item
    """
    id = request.args.get('id')
    response = db.session.execute(
        sa.select(CmdbConfigurationItem)
        .where(CmdbConfigurationItem.id == id)
    ).scalar_one_or_none()

    url = f'/ui/cmdb/ticket/{response.ticket_type.lower()}/?ticket={response.ticket_number}'

    if response:
        return jsonify({'url': url})
    else:
        return jsonify({'url': None})


@api_bp.post('/cmdb/add-change-freeze/')
@login_required
def add_change_freeze():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    # Validate ticket number
    ticket_number = data.get('ticket_number')
    if not ticket_number:
        return jsonify({'error': 'Ticket number is required'}), 400

    # Find the associated CMDB record
    cmdb = db.session.execute(
        sa.select(CmdbConfigurationItem)
        .where(CmdbConfigurationItem.ticket_number == ticket_number)
    ).scalars().one_or_none()

    if not cmdb:
        return jsonify({'error': f'Configuration item with ticket number {ticket_number} not found'}), 404

    # Validate and extract other fields
    try:
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-D for start_date and end_date'}), 400

    title = data.get('title')
    reason = data.get('reason')

    if not title or not reason:
        return jsonify({'error': 'Both title and reason are required'}), 400

    # Create a new ChangeFreeze record
    freeze = ChangeFreeze()
    freeze.title = title,
    freeze.start_date = start_date,
    freeze.end_date = end_date,
    freeze.reason = reason,
    freeze.ci_id = cmdb.id
    # Save the new record
    try:
        db.session.add(freeze)
        db.session.commit()
        response = {
            'id': freeze.id,
            'title': title,
            'start_date': start_date,
            'end_date': end_date,
            'reason': reason
        }

        return jsonify({'response': response}), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500


@api_bp.post('/cmdb/remove-change-freeze/')
@login_required
def remove_change_freeze():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    freeze_id = data.get('freeze')

    cmdb = db.session.execute(
        sa.select(ChangeFreeze)
        .where(ChangeFreeze.id == int(freeze_id))
    ).scalar_one_or_none()

    if not cmdb:
        return jsonify({'error': f'Change freeze with id {freeze_id} not found'}), 404

    try:
        db.session.delete(cmdb)
        db.session.commit()
        return jsonify({'success': f'Change freeze with id {freeze_id} deleted'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500


@api_bp.post('/cmdb/add-compliance/')
@login_required
def add_compliance():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400
    # Validate ticket number
    ticket_number = data.get('ticket_number')
    if not ticket_number:
        return jsonify({'error': 'Ticket number is required'}), 400

    # Find the associated CMDB record
    cmdb = db.session.execute(
        sa.select(CmdbConfigurationItem)
        .where(CmdbConfigurationItem.ticket_number == ticket_number)
    ).scalars().one_or_none()

    if not cmdb:
        return jsonify({'error': f'Configuration item with ticket number {ticket_number} not found'}), 404

    # Validate compliance data
    compliance_id = data.get('compliance_id', int)
    if not compliance_id:
        return jsonify({'error': 'Compliance id is required'}), 400

    # Check if the compliance record already exists
    compliance = db.session.execute(
        sa.select(Compliance)
        .where(Compliance.id == int(compliance_id))
    ).scalars().one_or_none()

    # Associate the compliance with the CMDB record if not already associated
    if compliance.id not in cmdb.compliances:
        cmdb.compliances.append(compliance)

    # Commit the changes to the database
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log_exception(f'{e}')
        return jsonify({'error': f'An error occurred while adding compliance: {str(e)}'}), 500

    return jsonify({
        "message": f"Compliance '{compliance.compliance_standard}' successfully added to configuration item '{ticket_number}'"
    }), 200


@api_bp.delete('/cmdb/remove-compliance/')
@login_required
def remove_compliance():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    ticket_number = data.get('ticket_number')
    if not ticket_number:
        return jsonify({'error': 'Ticket number is required'}), 400

    # Find the associated CMDB record
    cmdb = db.session.execute(
        sa.select(CmdbConfigurationItem)
        .where(CmdbConfigurationItem.ticket_number == ticket_number)
    ).scalars().one_or_none()

    if not cmdb:
        return jsonify({'error': f'Configuration item with ticket number {ticket_number} not found'}), 404

    compliance_id = data.get('compliance_id')
    if not compliance_id:
        return jsonify({'error': 'Compliance id is required'}), 400

    compliance = db.session.execute(
        sa.select(Compliance)
        .where(Compliance.id == compliance_id)
    ).scalars().one_or_none()

    if not compliance:
        return jsonify({'error': f'Compliance with id {compliance_id} not found'}), 404

    if compliance in cmdb.compliances:  # model has to have __equ__ function for this to work
        cmdb.compliances.remove(compliance)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log_exception(f'{e}')
        return jsonify({'error': f'An error occurred while removing compliance: {str(e)}'}), 500

    return jsonify({
        'message': f"Compliance '{compliance.compliance_standard}' successfully removed from configuration item '{ticket_number}'"
    }), 200
