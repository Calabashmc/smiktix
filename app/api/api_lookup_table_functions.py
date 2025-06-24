from datetime import time

from flask import jsonify, request
from flask_security import login_required

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from . import api_bp
from ..model import db
from ..model.lookup_tables import AppDefaults, ModelLookup, StatusLookup
from ..model.model_category import Category
from ..common.common_utils import get_model
from ..common.exception_handler import log_exception
from ..model.relationship_tables import category_model, status_model


def get_categories_by_ticket_type(stmt, value):
    stmt = (
        stmt
        .join(category_model)  # Join the association table
        .join(ModelLookup)  # Join the ModelLookup table
        .where(ModelLookup.name == value)  # Filter for the desired name
    )
    return stmt


@api_bp.post('/get-lookup-records/')
@login_required
def get_lookup_records():
    """
    Endpoint for getting the table of lookup records for any lookup table.
    :return: JSON of lookup records
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    model_name = data.get('model')
    if not model_name:
        return jsonify({'error': 'Model name is required'}), 400

    model = get_model(model_name)
    if not model:
        return jsonify({'error': f"Model '{model_name}' not found"}), 404

    filter_by = data.get('filter_by')  # Expected format: {'field': 'value'}
    stmt = (sa.select(model)
            .order_by(model.id)
            )

    if filter_by:
        field_filter, filter_value = filter_by.get('field'), filter_by.get('value')
        if not field_filter or filter_value is None:
            return jsonify({'error': 'Both "field" and "value" are required in "filter_by"'}), 400

        if model == Category:
            # Handle the special case for Category due to many-to-many relationship
            stmt = get_categories_by_ticket_type(stmt, filter_value)
        else:
            # Handle direct column filter
            column = getattr(model, field_filter, None)
            if not column:
                return jsonify({'error': f"Field '{field_filter}' not found in '{model_name}'"}), 400
            stmt = stmt.where(column == filter_value)

    results = db.session.execute(stmt).scalars().all()

    # need this to convert time objects to strings as time objects are not JSON serialisable
    def serialize_value(value):
        if isinstance(value, time):
            return value.strftime("%H:%M:%S")  # Convert the time object to string
        return value

    result_list = [
        {key: serialize_value(value) for key, value in vars(record).items() if not key.startswith('_')}
        for record in results
    ]

    return jsonify({'data': result_list})


@api_bp.post('/lookup/get_status_lookup/')
@login_required
def get_status_lookup():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    statuses_with_models = db.session.execute(
        sa.select(StatusLookup)
        .options(joinedload(StatusLookup.models))
    ).unique().scalars().all()

    # Now we can access each status and its related models
    tabulator_data = []
    for status in statuses_with_models:
        if not status.models:  # If no models, still include the status but should never happen
            tabulator_data.append({
                "id": status.id,
                "status": status.status,
                "name": "(No models)",  # Placeholder for empty models
                "comment": status.comment
            })
        else:
            # For each model in this status, create a row
            for model in status.models:
                tabulator_data.append({
                    "id": status.id,
                    "status": status.status,
                    "name": model.name,
                    "model_id": model.id,
                })

    return jsonify(data=tabulator_data)


@api_bp.post('/lookup/set-table-row/')
@login_required
def set_table_row():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    model = get_model(data['model'])

    # Fetch the record otherwise create a new model instance
    if 'id' in data:
        record = db.session.execute(
            sa.select(model)
            .where(sa.and_(model.id == data['id']))
        ).scalars().one_or_none()
    elif 'name' in data:
        record = db.session.execute(
            sa.select(model)
            .where(sa.and_(model.name == data['name']))
        ).scalars().one_or_none()
    else:
        return jsonify({'error': 'Invalid JSON data'}), 400

    if record is None:
        record = model()  # Create a new instance if no id is provided
    # Loop through the fields in the data and set them dynamically
    for field_name, value in data.items():
        if hasattr(record, field_name) and field_name not in {'id', 'model'}:
            current_value = getattr(record, field_name)
            if current_value != value:  # Only update if the value has changed
                setattr(record, field_name, value)
    try:
        # Add the record to the session only if it's new
        db.session.merge(record)
        db.session.commit()
        return jsonify({'success': 'Record updated successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500


@api_bp.post('/lookup/add-status/')
@login_required
def add_status():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    status_id = int(data.get('status-id'))
    model_id = int(data.get('model-id'))

    if not status_id or not model_id:
        return jsonify({'error': 'Status ID and Model ID are required'}), 400

    status = db.session.execute(
        sa.select(StatusLookup)
        .where(StatusLookup.id == status_id)
    ).scalar()  # Get status by ID

    model = db.session.execute(
        sa.select(ModelLookup)
        .where(ModelLookup.id == model_id)
    ).scalar()  # Get model by ID

    if not status or not model:
        return jsonify({'error': 'Status or model not found'}), 404

    # Check if the model is already in this status
    exists = db.session.execute(
        sa.select(status_model)
        .where(sa.and_(status_model.c.status_id == status_id, status_model.c.model_id == model_id))
    ).fetchone()

    if exists:
        return jsonify({'error': 'Model already exists in this status'}), 400
    # Add the model to the status
    status.models.append(model)

    try:
        db.session.commit()
        return jsonify({'success': 'Status added successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        log_exception(f'Database error: {e}')
        return jsonify({'error': 'Database error: ' + str(e)}), 500


@api_bp.get('/lookup/get-app-defaults/')
@login_required
def get_app_defaults():
    result = AppDefaults.get_app_defaults()
    if not result:
        return jsonify({'error': 'App defaults not found'}), 404

    return jsonify({'service_desk_phone': result.servicedesk_phone,
                    'service_desk_email': result.servicedesk_email,
                    'service_desk_open_hour': result.servicedesk_open_hour,
                    'service_desk_close_hour': result.servicedesk_close_hour,
                    'service_desk_timezone': result.servicedesk_timezone,
                    'incident_default_priority': result.incident_default_priority,
                    'incident_default_impact': result.incident_default_impact,
                    'incident_default_urgency': result.incident_default_urgency,
                    'problem_default_priority': result.problem_default_priority,
                    'change_default_risk': result.change_default_risk
                    }), 200


@api_bp.post('/lookup/set-app-defaults/')
@login_required
def set_app_defaults():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON data or incorrect Content-Type header'}), 400

    AppDefaults.set_app_defaults(data)
    return jsonify({'success': 'Defaults updated successfully'}), 200

