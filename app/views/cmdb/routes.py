import os
from datetime import datetime, timezone
from flask import flash, redirect, render_template, request, url_for
from flask_sqlalchemy.model import Model
from jinja2.filters import Markup
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from flask_security import current_user, login_required
from wtforms import BooleanField

from . import cmdb_bp
from .form import CmdbHardwareForm, CmdbSoftwareForm, CmdbServiceForm
from ...model.lookup_tables import AppDefaults, Compliance
from ...views.cmdb.form import CmdbForm
from ...model import db
from ...model.model_cmdb import CmdbConfigurationItem, CmdbHardware, CmdbSoftware, CmdbService
from ...model.model_notes import Notes
from ...common.common_utils import get_highest_ticket_number
from ...common.ticket_utils import (
    add_journal_notes,
    get_ticket,
    handle_existing_ticket,
    hardware_dependencies,
    populate_relationship_select_choices,
    populate_vendor_details,
    render_ticket_dashboard,
    save_ticket,
    validate_and_update_ticket
)


@cmdb_bp.get("/ui/cmdb/ticket/service/")
@cmdb_bp.get("/ui/cmdb/ticket/software/")
@cmdb_bp.get("/ui/cmdb/ticket/hardware/")
@login_required
def cmdb_get():
    ticket_number = request.args.get("ticket")
    exists = bool(ticket_number)
    path_parts = request.path.strip("/").split("/")
    ci_type = path_parts[-1]  # Assuming the last part of the path is the ci_type (service, software, hardware)

    form = CmdbForm()
    template = "/cmdb/hardware.html"
    ci_type_mappings = {
        "hardware": {
            "form_class": CmdbHardwareForm,
            "model": CmdbHardware,
            "ticket_type": "Hardware",
            "template": "/cmdb/hardware.html",
        },
        "software": {
            "form_class": CmdbSoftwareForm,
            "model": CmdbSoftware,
            "ticket_type": "Software",
            "template": "/cmdb/software.html",
        },
        "service": {
            "form_class": CmdbServiceForm,
            "model": CmdbService,
            "ticket_type": "Service",
            "template": "/cmdb/service.html",
        },
    }

    mapping = ci_type_mappings.get(ci_type)

    if mapping:
        form = mapping["form_class"]()
        model = mapping["model"]
        form.ticket_type.data = mapping["ticket_type"]
        template = mapping["template"]
    else:
        # Handle unknown ci_type
        raise ValueError(f"Unknown ci_type: {ci_type}")
        log_exception(f'Unknown ci_type: {ci_type}')

    if exists:  # existing cmdb ticket
        ticket = handle_existing_ticket(model, ticket_number, form)
        form.icons.data = url_for('static', filename=f'images/vis-network/{ticket.icon}')

        if model != CmdbService:
            # populate upstream node list if any
            if hasattr(ticket, 'upstream'):
                upstream_nodes = model.get_upstream(ticket)
                form.upstream_list.choices = [(node.id, f'{node.ticket_number} | {node.name}') for node in upstream_nodes]

            # populate downstream node list if any
            if hasattr(ticket, 'downstream'):
                downstream_nodes = model.get_downstream(ticket)
                form.downstream_list.choices = [(node.id, f'{node.ticket_number} | {node.name}') for node in
                                                downstream_nodes]

        else:
            compliance_list = ticket.get_compliances()
            form.compliance_list.choices = [(node.id, f'{node.compliance_standard} | {node.comment}') for node in
                                            compliance_list]
            # populate downstream node list if any
            related_nodes = model.get_related_cis(ticket)
            form.downstream_list.choices = [(node.id, f'{node.ticket_number} | {node.name}') for node in
                                            related_nodes]



        if not ticket:
            flash("Invalid ticket number in URL - returning to dashboard", "danger")
            return redirect(f"/ui/cmdb/tickets/")

        # this block of code first adds nodes to the upstream & downstream multi-selection input.
        # Then removes these and the current ticket from the downstream and upstream select input
        if ci_type == "hardware" or ci_type == "software":
            hardware_dependencies(form, ticket)
            populate_vendor_details(form)

        id = ticket.id

        # populate relationship select inputs (ticket_utils.py)
        populate_relationship_select_choices(form, ticket, model)

    else:
        icon_name = db.session.execute(
            select(AppDefaults.cmdb_default_icon)
        ).scalars().first()

        form.icons.data = url_for('static', filename=f'images/vis-network/{icon_name}')
        form.created_at.data = datetime.now(timezone.utc)
        form.ticket_number.data = get_highest_ticket_number(CmdbConfigurationItem)
        id = None  # No CI Selected so pass None

    return render_template(
        template,
        form=form,
        highest_number=get_highest_ticket_number(CmdbConfigurationItem) - 1,
        exists=exists,
        id=id,  # Used for javascript in _header-common.html to identify the CI
        model="cmdbconfigurationitem",
        # ticket_type=ci_type
    )


@cmdb_bp.post("/ui/cmdb/ticket/service/")
@cmdb_bp.post("/ui/cmdb/ticket/software/")
@cmdb_bp.post("/ui/cmdb/ticket/hardware/")
@login_required
def cmdb_post():
    ticket_number = request.args.get("ticket")
    exists = bool(ticket_number)

    path_parts = request.path.strip("/").split("/")
    ci_type = path_parts[-1]  # Assuming the last part of the path is the ci_type (service, software, hardware)

    form = CmdbHardwareForm()
    ticket = []

    ci_type_mappings = {
        "hardware": {
            "form_class": CmdbHardwareForm,
            "ticket": get_ticket(CmdbHardware, ticket_number),
        },
        "software": {
            "form_class": CmdbSoftwareForm,
            "ticket": get_ticket(CmdbSoftware, ticket_number),
        },
        "service": {
            "form_class": CmdbServiceForm,
            "ticket": get_ticket(CmdbService, ticket_number),
        },
    }

    mapping = ci_type_mappings.get(ci_type)

    if mapping:
        form = mapping["form_class"]()
        ticket = mapping["ticket"]
    else:
        # Handle unknown ci_type
        raise ValueError(f"Unknown ci_type: {ci_type}")

    if not form.icons.data:
        form.icons.data = db.session.execute(
            select(AppDefaults.cmdb_default_icon)
        ).scalars().first()

    ticket.icon = os.path.basename(form.icons.data)  # just get the filename, remove /static/image/vis-network/
    if not validate_and_update_ticket(form, ticket, exists):
        return redirect(f"/ui/cmdb/tickets/")

    if save_ticket(ticket, exists):
        return redirect(
            f"/ui/cmdb/ticket/{ticket.ticket_type.lower()}/?ci_type={ci_type}&ticket={ticket.ticket_number}")

    return redirect(f"/ui/cmdb/tickets/")


@cmdb_bp.get("/ui/cmdb/")
@cmdb_bp.get("/ui/cmdb/tickets/")
@login_required
def ticket_table():
    """
    :return: renders template with table of all problem tickets owned by logged-in user
    """
    return render_ticket_dashboard(CmdbConfigurationItem)
