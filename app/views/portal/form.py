from flask import current_app
from flask_login import current_user
from sqlalchemy import select
from wtforms.fields.simple import TextAreaField

from ...views.idea.form import IdeasForm
from ...views.interaction.form import InteractionForm
from ...views.knowledge.form import KnowledgeForm
from wtforms import StringField, DecimalField, TelField, SelectField
from wtforms.validators import Optional

from ...model import db
from ...model.model_category import Category
from ...model.model_interaction import Ticket
from ...model.model_portal import ServiceCatalogue
from ...model.model_user import Team


class PortalForm(InteractionForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service.choices = [(0, 'Select...')] + [
            (el.id, el.name) for el in
            db.session.execute(
                select(Category)
                .order_by(Category.name.asc())
            ).scalars().all()
        ]

        self.service_name = [
            (el.id, el.service) for el in
            db.session.execute(
                select(ServiceCatalogue)
                .where(ServiceCatalogue.active == True)
                .order_by(ServiceCatalogue.service.asc())
            ).scalars().all()
        ]

    open_sla_resolve_breach = DecimalField(
        label='Resolve SLA Breached',
        render_kw={'disabled': True, 'class': 'number-no-border'},
        places=0,
        default=lambda: Ticket.query.filter(
            Ticket.status != 'closed').filter(Ticket.sla_resolve_breach).count()
    )

    requested_by = StringField(
        label="Suggested By:",
        render_kw={"class": "no-border", "readonly": True}
    )

    staff = StringField(label="Support Agent")

    knowledgebase_search = StringField()

    service_name = SelectField(
        id="service-name",
        label="Service",
        choices=[],
        validators=[Optional()]
    )

    service_desk_phone = TelField(render_kw={"class": "no-border", "readonly": True}, )
    service_desk_email = StringField(render_kw={"class": "no-border", "readonly": True}, )

    service = SelectField(
        label="Service",
        choices=[],
        validate_choice=False,
        coerce=int,
    )


class PortalIdeasForm(IdeasForm):
    def __init__(self):
        super().__init__()

    offcanvas_current_issue = TextAreaField(
        label="Current Issue",
        id="offcanvas-current-issue",
        render_kw={"class": "timeline-editor"}
    )

    offcanvas_dependencies = TextAreaField(
        label="Dependencies",
        id="offcanvas-dependencies",
        render_kw={"class": "timeline-editor"}
    )

    offcanvas_details = TextAreaField(
        label="Idea Details",
        id="offcanvas-details",
        render_kw={"class": "timeline-editor"}
    )

    offcanvas_risks = TextAreaField(
        label="Risks",
        id="offcanvas-risks",
        render_kw={"class": "timeline-editor"}
    )


class PortalKnowledgeForm(KnowledgeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass


class PortalTicketForm(InteractionForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    priority_user_set = StringField(
        label="User Priority",
        id="priority-user-set",
        render_kw={"hidden": "true"}
    )

    requested_by = StringField(
        label="Requested By",
        default=lambda: current_user.username,
        render_kw={"hidden": "true"}
    )

    support_team_id = StringField(
        id="support-team-id",
        label="Support Team",
        default=lambda: Team.query
        .filter_by(name=current_app.config.get("DEFAULT_TEAM")).first().id,
        render_kw={"hidden": "true"}
    )
