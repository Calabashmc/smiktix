from datetime import datetime, timezone
from flask import flash, redirect, render_template, request, jsonify, g
from flask_security import current_user, login_required
import sqlalchemy as sa
import logging
from markupsafe import Markup
from . import change_bp
from ...views.change.form import EmergenceyChangeForm, StandardChangeForm, NormalChangeForm
from ...model import db
from ...model.model_change import Change
from ...model.relationship_tables import ChangeApprover
from ...model.model_user import Role, User
from ...common.common_utils import get_highest_ticket_number
from ...common.ticket_utils import (
    get_ticket,
    handle_existing_ticket,
    render_ticket_dashboard,
    save_ticket,
    validate_and_update_ticket
)


@change_bp.get('/ui/change/ticket/normal/')
@login_required
def normal_change_get():
    ticket_number = request.args.get('ticket')
    exists = bool(ticket_number)
    form = NormalChangeForm()
    form.change_type.data = 'Normal'

    if exists:
        ticket = handle_existing_ticket(Change, ticket_number, form)

        if not ticket:
            flash('invalid change number in URL - defaulting to new Change', 'danger')
            return redirect(f'/ui/change/ticket/normal/')

        # Ensure ticket.departments_impacted is a list of Department objects
        if ticket.departments_impacted:
            # Retrieve the ids of the associated departments
            departments_selected = [department.id for department in ticket.departments_impacted]
            form.departments_impacted.data = departments_selected
        else:
            form.departments_impacted.data = []

        # populate approved multiselect with all approvers that have approved or are pending
        approvers = db.session.execute(
            sa.select(User, ChangeApprover.approved, ChangeApprover.approval_date)
            .join(ChangeApprover, sa.and_(
                ChangeApprover.user_id == User.id,
                ChangeApprover.change_id == ticket.id
            ))).fetchall()

        max_name_length = max((len(item[0].full_name) for item in approvers), default=0)
        approver_dict = {}
        for user, approved, approval_date in approvers:
            if approval_date:
                if approved:
                    approver_dict[user.id] = Markup(
                        f'{user.full_name.ljust(max_name_length).replace(" ", "&nbsp;")} : Approved on {str(approval_date.strftime(g.datetime_format))}')
                else:
                    approver_dict[user.id] = Markup(
                        f'{user.full_name.ljust(max_name_length).replace(" ", "&nbsp;")} : Denied on {str(approval_date.strftime(g.datetime_format))}')
            else:
                approver_dict[user.id] = Markup(
                    f'{user.full_name.ljust(max_name_length).replace(" ", "&nbsp;")} : Pending Approval')

        form.approvers_selection.choices = [
            (key, value) for key, value in approver_dict.items()
        ]

        # list of all users in the above two multiselects for excluding from the Approval Stakeholders Select
        # Needed so an Approver isn't added more than once
        excluded_user_ids = set(
            [user_id for user_id, _ in form.approvers_selection.choices] +
            [user_id for user_id, _ in form.approved_selection.choices]
        )

        # populate approval_stakeholders select with Users with Role 'approver' that aren't in the above multiselects
        form.approval_stakeholders.choices = [(0, "Select Stakeholder")] + [
            (el.id, el.full_name)
            for el in db.session.execute(
                sa.select(User)
                .where(User.roles.any(Role.name == 'approver'))
                .where(User.id.not_in(excluded_user_ids))
                .order_by(User.full_name.asc())
            ).scalars().all()
        ]

        form.start_time.data = ticket.start_time.strftime('%H:%M')
        id = form.cmdb_id.data

    else:
        form.change_type.data = 'Normal'
        form.risk_set.data = "CR3"
        form.risk_calc.data = "CR3"
        form.created_at.data = datetime.now(timezone.utc)
        form.created_by_id.data = current_user.id
        form.ticket_number.data = get_highest_ticket_number(Change)
        form.ticket_type.data = "Change"
        id = None  # No CI Selected so pass None

    return render_template("change/normal-change.html",
                           exists=exists,
                           highest_number=get_highest_ticket_number(Change) - 1,
                           id=id,  # Used for javascript in _header-common.html to identify the CI
                           form=form,
                           model="Change",
                           )


@change_bp.post('/ui/change/ticket/normal/')
@change_bp.post('/ui/change/ticket/standard/')
@change_bp.post('/ui/change/ticket/emergency/')
@login_required
def change_post():
    ticket_number = request.args.get('ticket')
    exists = bool(ticket_number)
    ticket = get_ticket(Change, ticket_number)

    # Determine the ticket type from the path
    if 'normal' in request.path:
        form = NormalChangeForm()
        form.change_type.data = 'Normal'
    elif 'standard' in request.path:
        form = StandardChangeForm()
        form.change_type.data = 'Standard'
    elif 'emergency' in request.path:
        form = EmergenceyChangeForm()
        form.change_type.data = 'Emergency'
    else:
        return redirect(f"/ui/change/tickets/")

    if not validate_and_update_ticket(form, ticket, exists):
        return redirect(f"/ui/change/tickets")

    if save_ticket(ticket, exists):
        return redirect(f"/ui/change/ticket/{ticket.change_type.lower()}/?ticket={ticket.ticket_number}")

    return redirect(f"/ui/change/tickets/")


@change_bp.get('/ui/change/')
@change_bp.get('/ui/change/tickets/')
@login_required
def ticket_table():
    """
    Dashboard showing work owned by current user
    :return: renders a template with javascript which fetches json from api
    """
    return render_ticket_dashboard(Change)


def get_approval_details(ticket_number, user_id):
    approver = db.session.execute(
        sa.select(User).where(User.id == user_id)
    ).scalars().one_or_none()

    if not approver:
        return None, None, None, {'error': 'User not found'}, 404

    change = db.session.execute(
        sa.select(Change).where(Change.ticket_number == ticket_number)
    ).scalars().one_or_none()

    approval = db.session.execute(
        sa.select(ChangeApprover).where(
            sa.and_(ChangeApprover.change_id == change.id, ChangeApprover.user_id == user_id)
        )
    ).scalars().one_or_none()

    return approver, change, approval, None, None


def approval_exists(approval, approver, ticket_number, change_owner):
    approval_response = "Approved" if approval.approved else "Denied"

    return render_template(
        "approval/already-acknowledged.html",
        approver=approver.full_name,
        ticket_number=ticket_number,
        approval_date=approval.approval_date.strftime(g.datetime_format),
        approval_response=approval_response,
        change_owner=change_owner
    )


# todo point these to an approval page in the portal?
@change_bp.get('/ui/change/change-approve/')
@login_required
def change_approve():
    ticket_number = request.args.get("ticket")
    user_id = request.args.get("user")

    if not ticket_number or not user_id:
        logging.error("Missing ticket number or user")
        return jsonify({'error': 'Missing ticket number or user'}), 400

    approver, change, approval, error, status_code = get_approval_details(ticket_number, user_id)

    if error:
        return jsonify(error), status_code

    if not approval:
        return render_template(
            "approval/not-required.html",
            approver=approver.full_name,
            ticket_number=ticket_number,
            approval_response='Not Required',
            change_owner=change.created_by
        )

    if approval.approver_acknowledged:
        approval_exists(approval, approver, ticket_number, change.created_by)

    approval.approver_acknowledged = True
    approval.approver_rejected = False
    approval.approved = True
    approval.approval_date = datetime.now(timezone.utc)

    db.session.commit()

    return render_template(
        "approval/approve.html",
        approver=approver.full_name,
        ticket_number=ticket_number,
        approval_response="Approved",
        change_owner=change.created_by
    )


@change_bp.get('/ui/change/change-reject/')
@login_required
def change_reject():
    ticket_number = request.args.get("ticket")
    user_id = request.args.get("user")

    if not ticket_number or not user_id:
        logging.error("Missing ticket number or user")
        return jsonify({'error': 'Missing ticket number or user'}), 400

    approver, change, approval, error, status_code = get_approval_details(ticket_number, user_id)
    if error:
        return jsonify(error), status_code

    if not approval:
        return render_template(
            "approval/not-required.html",
            approver=approver.full_name,
            ticket_number=ticket_number,
            approval_response='Not Required',
            change_owner=change.created_by
        )

    if approval.approver_acknowledged:
        approval_exists(approval, approver, ticket_number, change.created_by)

    approval.approver_acknowledged = True
    approval.approver_rejected = True
    approval.approved = False
    approval.approval_date = datetime.now(timezone.utc)

    db.session.commit()

    return render_template(
        "approval/reject.html",
        approver=approver.full_name,
        ticket_number=ticket_number,
        approval_response="Denied"
    )


@change_bp.get('/ui/change/ticket/standard/')
@login_required
def standard_change_get():
    ticket_number = request.args.get('ticket')
    exists = bool(ticket_number)
    form = StandardChangeForm()
    form.change_type.data = 'Standard'

    if exists:
        ticket = handle_existing_ticket(Change, ticket_number, form)

        if not ticket:
            flash('invalid change number in URL - defaulting to new Normal Change', 'danger')
            return redirect(f'/ui/change/ticket/normal/')

        # Ensure ticket.departments_impacted is a list of Department objects
        if ticket.departments_impacted:
            # Retrieve the ids of the associated departments
            departments_selected = [department.id for department in ticket.departments_impacted]
            form.departments_impacted.data = departments_selected
        else:
            form.departments_impacted.data = []

        form.start_time.data = ticket.start_time.strftime('%H:%M')
        id = form.cmdb_id.data

    else:
        form.risk_set.data = "CR4"
        form.created_at.data = datetime.now(timezone.utc)
        form.created_by_id.data = current_user.id
        form.ticket_number.data = get_highest_ticket_number(Change)
        form.ticket_type.data = "Change"
        id = None  # No CI Selected so pass None

    return render_template("change/standard-change.html",
                           exists=exists,
                           highest_number=get_highest_ticket_number(Change) - 1,
                           id=id,  # Used for javascript in _header-common.html to identify the CI
                           form=form,
                           model="Change",
                           )


@change_bp.get('/ui/change/ticket/emergency/')
@login_required
def emergency_change_get():
    ticket_number = request.args.get('ticket')
    exists = bool(ticket_number)
    form = EmergenceyChangeForm()
    form.change_type.data = 'Emergency'

    if exists:
        ticket = handle_existing_ticket(Change, ticket_number, form)

        if not ticket:
            flash('invalid change number in URL - defaulting to new Normal Change', 'danger')
            return redirect(f'/ui/change/ticket/emergency/')

        # Set the child_ticket_id data to the selected ticket's child_ticket_id
        # ticket.child_ticket.id is an int so need to cast to str to field displays it
        if ticket.child_ticket:
            form.child_ticket_id.data = str(ticket.child_ticket.id)
        # Ensure ticket.departments_impacted is a list of Department objects
        if ticket.departments_impacted:
            # Retrieve the ids of the associated departments
            departments_selected = [department.id for department in ticket.departments_impacted]
            form.departments_impacted.data = departments_selected
        else:
            form.departments_impacted.data = []

        form.start_time.data = ticket.start_time.strftime('%H:%M')
        id = form.cmdb_id.data

    else:
        form.risk_set.data = "CR1"
        form.created_at.data = datetime.now(timezone.utc)
        form.created_by_id.data = current_user.id
        form.ticket_number.data = get_highest_ticket_number(Change)
        form.ticket_type.data = "Change"
        id = None  # No CI Selected so pass None

    return render_template("change/emergency-change.html",
                           exists=exists,
                           highest_number=get_highest_ticket_number(Change) - 1,
                           id=id,  # Used for javascript in _header-common.html to identify the CI
                           form=form,
                           model="Change",
                           )
