from datetime import date, datetime, timezone
from flask import g, json, jsonify, redirect, flash, render_template
from collections import OrderedDict
from flask_security import current_user
from jinja2.filters import Markup

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

from wtforms import (
    BooleanField,
    DateTimeField,
    DateTimeLocalField,
    RadioField,
    SelectField,
    SelectMultipleField
)

from ..common.common_utils import get_highest_ticket_number, my_teams, send_notification
from ..common.exception_handler import log_exception
from ..common.forms import MultipleCheckboxField
from ..model import db
from ..model.lookup_tables import BenefitsLookup, Compliance, ImpactLookup, ResolutionLookup, VendorLookup
from ..model.model_change import Change
from ..model.model_cmdb import CmdbConfigurationItem, CmdbHardware, CmdbService, CmdbSoftware
from ..model.model_idea import Idea
from ..model.model_knowledge import KnowledgeBase
from ..model.model_notes import Notes
from ..model.model_problem import Problem
from ..model.model_release import Release
from ..model.model_interaction import Ticket
from ..model.relationship_tables import change_followers
from ..model.model_user import Department, User
from ..api.api_people_functions import get_support_agents
from ..views.admin.form import AdminUserForm


def add_journal_notes(ticket, note_content, is_system):
    note = Notes(
        note=Markup(note_content),
        noted_by=current_user.full_name,
        note_date=datetime.now(timezone.utc),  # Use UTC for consistency
        ticket_type=ticket.ticket_type,
        ticket_number=ticket.ticket_number,
        is_system=is_system,
    )

    ticket.notes.append(note)  # ✅ Safely sets the relationship

    ticket.last_updated_at = datetime.now(timezone.utc)  # Update the last_updated_at in UTC

    try:
        db.session.add(note)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        log_exception(f'Failed to add journal note: {e}')



def format_time(time_field, user_timezone):
    '''
    Helper function to format time fields.
    '''
    return time_field.astimezone(user_timezone).strftime(g.datetime_format) if time_field else None


def datetime_to_string(dt):
    if not type(dt) == datetime and not dt:
        return ''  # Ensure it returns a string
    return dt.strftime(g.datetime_format)


def date_to_string(d):
    if not type(d) == date and not d:
        return ''  # Ensure it returns a string
    return d.strftime(g.date_format)


# Helper functions for ticket POST operations
def get_ticket(model, ticket_number):
    if ticket_number:
        return db.session.execute(
            sa.select(model)
            .where(model.ticket_number == ticket_number)
        ).scalar_one_or_none()
    else:
        return model()


def get_child_tickets(model, ticket_number):
    '''
    Returns all children of a parent ticket
    :param model: should be Ticket, Problem, or Change
    :param ticket_number: Parent ticket number
    :return: child tickets
    '''
    # get id of parent ticket (current ticket, it is parent of it's children).
    # Search for child tickets that have this id as parent_id
    parent = db.session.execute(
        sa.select(model)
        .where(model.ticket_number == ticket_number)
    ).scalars().first()

    match parent.ticket_type:
        case 'Incident' | 'Request':
            return db.session.execute(
                sa.select(Ticket)
                .where(Ticket.parent_id == parent.id)
            ).scalars().all()

        case 'Problem' | 'Known Error' | 'Workaround':
            return db.session.execute(
                sa.select(Ticket).where(Ticket.problem_id == parent.id)
            ).scalars().all()

        case 'Change':
            return db.session.execute(
                sa.select(Problem)
                .where(Problem.change_id == parent.id)
            ).scalars().all()
    return None


def handle_existing_ticket(model, ticket_number, form):
    ticket = db.session.execute(
        sa.select(model)
        .where(model.ticket_number == ticket_number)
    ).scalar_one_or_none()

    if not ticket:
        return None

    populate_fields_from_ticket(form, ticket)
    populate_requester_details(form, ticket)

    if model not in (Idea, KnowledgeBase, CmdbConfigurationItem, CmdbHardware, CmdbSoftware, CmdbService):
        form.supporter_id.choices = get_support_agents(ticket.support_team_id)

    return ticket


def hardware_dependencies(form, ticket):
    '''
    Populate relationship select inputs and selections, removing selected and current ticket from the select options
    for upstream and downstream dependencies
    '''
    current_downstream_choices = []
    current_upstream_choices = []

    if hasattr(ticket, 'downstream'):
        downstream_list = ticket.get_downstream()
        form.downstream_list.choices = [(node.id, f'{node.ticket_number} | {node.name}') for node in downstream_list]
        current_downstream_choices = form.downstream_list.choices

    if hasattr(ticket, 'upstream'):
        upstream_list = ticket.get_upstream()
        form.upstream_list.choices = [(node.id, f'{node.ticket_number} | {node.name}') for node in upstream_list]
        current_upstream_choices = form.upstream_list.choices

    current_ticket = (ticket.id, f'{ticket.ticket_number} | {ticket.name}')
    combined_up_down_choices = current_downstream_choices + current_upstream_choices + [current_ticket]

    # remove selected options from upstream and downstream select inputs
    if hasattr(form, 'downstream_node'):
        form.downstream_node.choices = [(value, label) for value, label in form.downstream_node.choices if
                                        (value, label) not in combined_up_down_choices]

    form.upstream_node.choices = [(value, label) for value, label in form.upstream_node.choices if
                                  (value, label) not in combined_up_down_choices]


# Helper functions for ticket GET operations
def populate_fields_from_ticket(form, ticket):
    for field in form:
        field_name = field.name
        # Get the value from the ticket (database record)
        value = getattr(ticket, field_name, None)
        if value is not None:
            if isinstance(field, BooleanField):
                field.data = bool(value)

            elif isinstance(field, (SelectMultipleField, MultipleCheckboxField)):  # Handle multi-select fields
                if isinstance(value, (list, sa.orm.collections.InstrumentedList)):
                    field.data = [str(item.id) for item in value]  # Convert to strings
                elif isinstance(value, list):
                    field.data = [str(v) for v in value]  # Convert to strings
                else:
                    field.data = []

            elif isinstance(field, (SelectField, RadioField)):  # Handle single-select fields
                if field.coerce == int:
                    field.data = int(value)
                elif field.coerce == str:
                    field.data = str(value)
                else:
                    if isinstance(field, DateTimeLocalField) and isinstance(value, datetime):
                        # Convert to naive datetime (strip timezone)
                        field.data = value.astimezone(
                            datetime.now().astimezone().tzinfo
                        ).replace(tzinfo=None).strftime('%Y-%m-%dT%H:%M')

            else:
                field.data = value


def populate_related_model_fields(form, model_instance):
    """
    Generic function to populate form fields from a related model instance
    Args:
        form: The WTForm instance
        model_instance: The SQLAlchemy model instance
    """
    for field in form:
        field_name = field.name

        # Get the value from the related model instance
        value = getattr(model_instance, field_name, None)

        if value is not None:
            if isinstance(field, BooleanField):
                field.data = bool(value)

            elif isinstance(field, (SelectMultipleField, MultipleCheckboxField)):
                if isinstance(value, (list, sa.orm.collections.InstrumentedList)):
                    field.data = [str(item.id) for item in value]
                elif isinstance(value, list):
                    field.data = [str(v) for v in value]
                else:
                    field.data = []

            elif isinstance(field, (SelectField, RadioField)):
                if field.coerce == int:
                    field.data = int(value)
                elif field.coerce == str:
                    field.data = str(value)
                else:
                    if isinstance(field, DateTimeLocalField) and isinstance(value, datetime):
                        # Convert to naive local datetime and format as string
                        field.data = value.astimezone(
                            datetime.now().astimezone().tzinfo
                        ).replace(tzinfo=None).strftime('%Y-%m-%dT%H:%M')
            else:
                field.data = value


def populate_relationship_select_choices(form, ticket, model):
    if hasattr(form, 'change_freeze_list'):
        nbsp = '\u00A0'
        form.change_freeze_list.choices = [
            (node.id,
             f"{node.title[:15].ljust(15, nbsp)} {node.reason[:22].ljust(22, nbsp)} {node.start_date} to {node.end_date}")
            for node in
            ticket.get_change_freeze_list()
        ]

    if hasattr(form, 'cis_selection'):
        affected_cis = [ci[0] for ci in form.affected_cis.choices]  # ci will be a tuple of (id, name) so [0] is the id
        form.cis_selection.choices = [('', '')] + [
            (el.id, f'{el.ticket_number} | {el.name}') for el in
            db.session.execute(
                sa.select(CmdbConfigurationItem)
                .where(CmdbConfigurationItem.id.notin_(affected_cis))
                .order_by(CmdbConfigurationItem.ticket_number.asc())
            ).scalars().all()
        ]

    if hasattr(form, 'compliance_list'):
        # remove the already selected compliance option from the compliance_select so it can't be added more than once
        compliance_list = [comp_id[0] for comp_id in form.compliance_list.choices]

        compliance_items = db.session.execute(
            sa.select(Compliance)
            .where(Compliance.id.notin_(compliance_list))
            .order_by(Compliance.compliance_standard.asc())
        ).scalars().all()

        if compliance_items:
            max_standard_length = max(len(el.compliance_standard) for el in compliance_items)
        # Create formatted choices
        nbsp = '\u00A0'
        form.compliance_select.choices = [('', '')] + [
            (el.id, f"{el.compliance_standard.ljust(max_standard_length).replace(' ', nbsp)} | {el.comment}")
            for el in compliance_items
        ]

    if hasattr(form, 'upstream_list'):
        upstream_list = [up_id[0] for up_id in form.upstream_list.choices]
    else:
        upstream_list = []

    if hasattr(form, 'downstream_list'):
        downstream_list = [down_id[0] for down_id in form.downstream_list.choices]
    else:
        downstream_list = []

    if ticket.ticket_type == 'Service':
        filter_type = ['cmdb_software', 'cmdb_hardware']
    else:
        filter_type = ['cmdb_hardware']

    choices = [('', '')] + [
        (str(el.id), f'{el.ticket_number} | {el.name}')
        for el in db.session.execute(
            sa.select(CmdbConfigurationItem)
            .where(
                sa.and_(
                    CmdbConfigurationItem.type.in_(filter_type),
                    CmdbConfigurationItem.id.notin_(upstream_list),
                    CmdbConfigurationItem.id.notin_(downstream_list)
                )
            )
            .order_by(CmdbConfigurationItem.ticket_number.asc())
        ).scalars().all()
    ]

    if hasattr(form, 'upstream_node'):
        form.upstream_node.choices = choices

    if hasattr(form, 'downstream_node'):
        form.downstream_node.choices = choices


def populate_requester_details(form, model) -> None:
    '''
    Used by various forms to populate additional information about the Requester
    '''
    if hasattr(model, 'requester_id') and model.requester_id:
        requester = db.session.execute(
            sa.select(User)
            .where(User.id == model.requester_id)
        ).scalar_one_or_none()
    elif hasattr(model, 'owner_id') and model.owner_id:
        requester = db.session.execute(
            sa.select(User)
            .where(User.id == model.owner_id)
        ).scalar_one_or_none()
    else:
        requester = None

    if requester:
        form.phone.data = requester.phone if requester.phone else 'None listed'
        form.email.data = requester.email if requester.email else 'None listed'
        form.occupation.data = requester.occupation if requester.occupation else 'None listed'
        if form.department:
            department = requester.department
            if department:
                form.department.data = department.name if department.name else 'None listed'


def populate_vendor_details(form):
    vendor_fields = [
        ('vendor_sales_id', 'vendor_sales_contact', 'vendor_sales_phone', 'vendor_sales_email'),
        ('vendor_support_id', 'vendor_support_contact', 'vendor_support_phone', 'vendor_support_email'),
        ('vendor_warranty_id', 'vendor_warranty_contact', 'vendor_warranty_phone', 'vendor_warranty_email'),
    ]

    for vendor_id_field, contact_field, phone_field, email_field in vendor_fields:
        if hasattr(form, vendor_id_field):
            vendor_id = getattr(form, vendor_id_field).data
            vendor = db.session.execute(
                sa.select(VendorLookup)
                .where(VendorLookup.id == vendor_id)
            ).scalar_one_or_none()

            if vendor:
                getattr(form, contact_field).data = vendor.contact_name
                getattr(form, phone_field).data = vendor.contact_phone
                getattr(form, email_field).data = vendor.contact_email


def render_ticket_dashboard(model):
    highest_number = get_highest_ticket_number(model) - 1
    form = AdminUserForm()

    args = {
        Ticket: {
            'template': '/interaction/dashboard.html',
            'title': 'Incident and Request Management',
            'model': 'Ticket',
        },
        Problem: {
            'template': '/problem/dashboard.html',
            'title': 'Problem Management',
            'model': 'Problem',
        },
        Change: {
            'template': '/change/dashboard.html',
            'title': 'Change Enablement',
            'model': 'Change',
        },
        Release: {
            'template': '/release/dashboard.html',
            'title': 'Release/Deployment Management',
            'model': 'Release',
        },
        KnowledgeBase: {
            'template': '/knowledge/dashboard.html',
            'title': 'Knowledge Management',
            'model': 'Knowledge',
        },
        Idea: {
            'template': '/idea/dashboard.html',
            'title': 'Continuous Improvement (Ideas)',
            'model': 'Idea',
        },
        CmdbConfigurationItem: {
            'template': '/cmdb/dashboard.html',
            'title': 'Configuration Management (CMDB)',
            'model': 'CI',
        },
    }

    return render_template(
        args[model]['template'],
        title=args[model]['title'],
        highest_number=highest_number,
        model=args[model]['model'],
        form=form
    )


def generate_unique_ticket_number(model, session):  # Not Use
    '''
    Generates a unique ticket number using the sequence, handling race conditions.
    This should only be called when creating a new ticket where there is a UniqueViolationError.
    Which should never happen if starting from a fresh database sans manullay added data.

    Args:
        model (db.Model): The model class containing the ticket_number.
        session (db.Session): The SQLAlchemy database session.
    Returns:
        int: A unique ticket number.
    '''
    while True:
        # Get next value from the sequence
        next_val_result = session.execute(
            sa.text(f"SELECT nextval('{model.ticket_number.default.name}')")
        ).scalar()

        if next_val_result is None:
            raise Exception('Unable to get next sequence value')
            log_exception('Unable to get next sequence value')

        # Check if the ticket number exists
        existing_record = session.execute(
            sa.select(model)
            .where(model.ticket_number == next_val_result)
        ).scalar_one_or_none()
        if not existing_record:
            return next_val_result


def save_ticket(ticket, exists):
    '''
    Save the ticket to the database.
    '''
    try:
        ticket.last_updated_at = datetime.now(timezone.utc)

        if not exists:
            ticket.created_by_id = current_user.id
            ticket.created_at = datetime.now(timezone.utc)
            message = f'New {ticket.ticket_type} Ticket has been created!'

            # No need to set ticket_number manually; Identity() handles it
            db.session.add(ticket)
        else:
            message = f'{ticket.ticket_type} Ticket has been updated!'
        db.session.commit()

    except sa.exc.IntegrityError as e:
        db.session.rollback()
        log_exception(f'Integrity error: {e}')
        flash('Error saving the ticket due to integrity issues.', 'danger')
        return False

    except sa.exc.SQLAlchemyError as e:
        db.session.rollback()
        log_exception(f'Database error: {e}')
        flash(f'Error saving the ticket {e}', 'danger')
        return False

    # Add journal notes and flash message
    add_journal_notes(ticket, message, is_system=True)
    flash(f'{message} - Ticket number is {ticket.ticket_number}', 'success')

    return True


def validate_and_update_ticket(form, ticket, exists=False):
    readonly_fields = set()
    if exists:  # Only make ticket_type read-only on updates
        readonly_fields.add('ticket_type')

    if not form.validate_on_submit():
        flash(f'Form validation failed: {form.errors}', 'danger')
        return False

    for field in form:
        if not hasattr(ticket, field.name):
            continue
        try:
            # Skip some fields
            if field.name == 'comms_journal':
                continue

            elif field.name in readonly_fields:
                continue

            elif field.name == 'affected_cis':
                if form.affected_cis.data:
                    ci_ids = map(int, form.affected_cis.data)
                    ticket.affected_cis = db.session.execute(
                        sa.select(CmdbConfigurationItem).where(CmdbConfigurationItem.id.in_(ci_ids))
                    ).scalars().all()
                else:
                    ticket.affected_cis = []

            elif field.name == 'child_ticket':
                if field.data:
                    ticket.child_ticket = db.session.execute(
                        sa.select(Ticket)
                        .where(Ticket.id == field.data)
                    ).scalar_one_or_none()

            elif field.name == 'departments_impacted':
                if form.departments_impacted.data:
                    department_ids = map(int, form.departments_impacted.data)
                    ticket.departments_impacted = db.session.execute(
                        sa.select(Department).where(Department.id.in_(department_ids))
                    ).scalars().all()
                else:
                    ticket.departments_impacted = []

            elif field.name == 'ecab_approver':
                if form.ecab_approver.data:
                    # Fetch the user by the selected ID
                    ecab_approver = db.session.execute(
                        sa.select(User).where(User.id == form.ecab_approver.data)
                    ).scalars().first()  # Use .first() since ecab_approver is a single User
                    if ecab_approver:  # Check if the user is found
                        ticket.ecab_approver = ecab_approver
                    else:
                        ticket.ecab_approver = None  # Handle the case where the user is not found
                else:
                    ticket.ecab_approver = None


            elif field.name == 'benefits':
                if form.benefits.data:
                    benefit_ids = [int(id_str) for id_str in form.benefits.data]  # Convert string IDs to integers
                    # Query the actual BenefitsLookup objects
                    benefit_objects = db.session.execute(
                        sa.select(BenefitsLookup)
                        .where(BenefitsLookup.id.in_(benefit_ids))
                    ).scalars().all()
                    # Assign the objects to the relationship
                    ticket.benefits = benefit_objects
                else:
                    ticket.benefits = []

            elif field.name == 'impact':
                if form.impact.data:
                    impact_ids = [int(id_str) for id_str in form.impact.data]  # Convert string IDs to integers
                    ticket.impact = db.session.execute(
                        sa.select(ImpactLookup)
                        .where(ImpactLookup.id.in_(impact_ids))
                    ).scalars().all()
                else:
                    ticket.impact = []
            else:
                # Get the model field
                model_field = getattr(ticket.__class__, field.name, None)
                # Check if the Field is a Database Column and convert data to the column's Python type
                if isinstance(model_field, db.Column):
                    column_type = model_field.type.python_type  # Gets Python type associated with the column (str, int, bool, etc.)
                    value = field.data if field.data is not None else None
                    setattr(ticket, field.name, column_type(value))
                else:
                    # Handle SelectField with empty string
                    if isinstance(field, SelectField) and field.data == '':
                        continue
                    # Handle BooleanField with None Value
                    if isinstance(field, BooleanField) and field.data is None:
                        setattr(ticket, field.name, False)
                    else:
                        setattr(ticket, field.name, field.data)

        except Exception as e:
            log_exception(f'Error setting attribute {field.name}: {e}')
            flash(f'An error occurred while setting the attribute {field.name}: {e}', 'danger')
            return False
    return True
