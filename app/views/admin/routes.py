from flask import render_template
from flask_login import login_required
from sqlalchemy import select

from . import admin_bp
from .form import AdminInteractionForm, AdminUserForm, AdminAppDefaultsForm, AdminChangeForm, AdminKnowledgeForm, \
    AdminIdeasForm, AdminCmdbForm, AdminCmdbServiceForm, AdminCmdbHardwareForm, AdminCmdbSoftwareForm, AdminReleaseForm

from ...model import db
from ...model.lookup_tables import AppDefaults

@admin_bp.route("/admin/")
@login_required
def admin_index():
    form = AdminUserForm()
    return render_template("admin/index.html",
                           form=form
                           )


@admin_bp.get("/admin/app-defaults/")
@login_required
def app_defaults():
    form = AdminAppDefaultsForm()
    defaults = db.session.execute(
        select(AppDefaults)
    ).scalars().first()

    if defaults:
        form.change_default_risk.data = defaults.change_default_risk
        form.close_hour.data = defaults.servicedesk_close_hour
        form.incident_default_impact.data = defaults.incident_default_impact
        form.incident_default_priority.data = defaults.incident_default_priority
        form.incident_default_urgency.data = defaults.incident_default_urgency
        form.open_hour.data = defaults.servicedesk_open_hour
        form.problem_default_priority.data = defaults.problem_default_priority
        form.servicedesk_email.data = defaults.servicedesk_email
        form.servicedesk_phone.data = defaults.servicedesk_phone
        form.support_team_default_id.data = defaults.support_team_default_id
        form.timezone.data = defaults.servicedesk_timezone

    return render_template("admin/app-defaults.html",
                           form=form,
                           admin_title="App Defaults"
                           )


@admin_bp.get("/admin/users/")
@login_required
def user_admin():
    form = AdminUserForm()
    return render_template("admin/users.html",
                           form=form,
                           model="people",
                           admin_title="User Related"
                           )


@admin_bp.get("/admin/incidents/")
@login_required
def interaction_admin():
    form = AdminInteractionForm()
    return render_template("admin/incidents.html",
                           form=form,
                           model="interaction",
                           admin_title="Incidents"
                           )


@admin_bp.get("/admin/problems/")
@login_required
def problem_admin():
    form = AdminInteractionForm()
    return render_template("admin/problems.html",
                           form=form,
                           admin_title="Problems"
                           )

@admin_bp.get("/admin/changes/")
@login_required
def change_admin():
    form = AdminChangeForm()
    return render_template("admin/changes.html",
                           form=form,
                           admin_title="Changes"
                           )

@admin_bp.get("/admin/releases/")
@login_required
def release_admin():
    form = AdminReleaseForm()
    return render_template("admin/releases.html",
                           form=form,
                           admin_title="Releases"
                           )

@admin_bp.get("/admin/knowledge/")
@login_required
def knowledge_admin():
    form = AdminKnowledgeForm()
    return render_template("admin/knowledge.html",
                           form=form,
                           admin_title="Knowledge"
                           )


@admin_bp.get("/admin/ideas/")
@login_required
def idea_admin():
    form = AdminIdeasForm()
    return render_template("admin/ideas.html",
                           form=form,
                           admin_title="Ideas"
                           )


@admin_bp.get("/admin/cmdb/")
@login_required
def cmdb_admin():
    form = AdminCmdbForm()
    hardware_form = AdminCmdbHardwareForm()
    service_form = AdminCmdbServiceForm()
    software_form = AdminCmdbSoftwareForm()

    return render_template("admin/cmdb.html",
                           form=form,
                           hardware_form=hardware_form,
                           service_form=service_form,
                           software_form=software_form,
                           )
