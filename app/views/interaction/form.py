from flask_wtf import FlaskForm
from jinja2.filters import Markup
import sqlalchemy as sa
from wtforms import BooleanField, DateTimeLocalField, DateTimeField, SelectField, TextAreaField, StringField
from wtforms.validators import Optional
from app.common.forms import InputRequired, RequesterMixin, SupportTeamMixin, UserDetailsMixin, BaseMixin

from ...model import db
from ...model.lookup_tables import ModelLookup, PauseReasons, ResolutionLookup
from ...model.model_category import Category
from ...model.model_cmdb import CmdbConfigurationItem
from ...model.model_interaction import Source, Ticket, TicketTemplate
from ...model.model_problem import Problem
from ...model.model_user import Team
from ...model.relationship_tables import category_model

class InteractionForm(SupportTeamMixin, RequesterMixin, UserDetailsMixin, BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.category_id.choices = [('', '')] + [
            (el.id, el.name)
            for el in db.session.execute(
                sa.select(Category)
                .join(category_model)  # Join the association table
                .join(ModelLookup)  # Join the ModelLookup table
                .where(ModelLookup.name == 'Interaction')  # Filter for the desired name
            ).scalars().all()
        ]

        self.child_select.choices = [('', '')] + [
            (el.id, f'{el.ticket_number} | {el.ticket_type} | {el.short_desc}')
            for el in db.session.execute(
                sa.select(Ticket).where(
                    sa.and_(
                        Ticket.is_parent.is_(not True),
                        Ticket.parent_id.is_(None),
                        sa.or_(
                            Ticket.status != 'closed',
                            Ticket.status != 'resolved'
                        )
                    )
                ).order_by(Ticket.ticket_number.asc())
            ).scalars().all()
        ]

        # Get all items
        items = db.session.execute(
            sa.select(CmdbConfigurationItem)
        ).scalars().all()
        # Find the maximum name length
        max_name_length = max((len(item.name) for item in items), default=0)
        self.cmdb_id.choices = [('', '')] + [
            (el.id, Markup(f"{el.name.ljust(max_name_length).replace(' ', '&nbsp;')} | {el.importance.importance}"))
            for el in items
        ]

        from ...model.model_knowledge import KnowledgeBase
        self.knowledge_resolve.choices = [('', '')] + [
            (el.id, f'{el.ticket_number} | {el.title}') for el in
            db.session.execute(
                sa.select(KnowledgeBase)
                .order_by(KnowledgeBase.ticket_number.asc())
            ).scalars().all()
        ]

        self.rapid_resolve.choices = [('', '')] + [
            (el.id, el.template_name) for el in
            db.session.execute(
                sa.select(TicketTemplate)
                .order_by(TicketTemplate.template_name.asc())
            ).scalars().all()
        ]

        self.resolution_code_id.choices = [('', '')] + [
            (el.id, el.resolution)
            for el in db.session.execute(
                sa.select(ResolutionLookup)
                .where(ResolutionLookup.model == 'Interaction')
                .order_by(ResolutionLookup.resolution.asc())
            ).scalars().all()
        ]

        self.source_id.choices = [
            (el.id, el.source)
            for el in db.session.execute(
                sa.select(Source)
                .order_by(Source.source.asc())
            ).scalars().all()
        ]

        self.parent_id.choices = [('', 'None')] + [
            (el.id, str(el.ticket_number) + ' | ' + el.ticket_type + ' | ' + el.short_desc)
            for el in db.session.execute(
                sa.select(Ticket)
                .where(Ticket.is_parent.is_(True))
                .order_by(Ticket.ticket_number.asc())
            ).scalars().all()
        ]

        self.problem_id.choices = [('', '')] + [
            (el.id, f'{el.ticket_number} | {el.ticket_type} | {el.short_desc}')
            for el in db.session.execute(
                sa.select(Problem)
                .where(sa.or_(Problem.status != 'resolved', Problem.status != 'closed'))
                .order_by(Problem.ticket_number.asc())
            ).scalars().all()
        ]

        self.sla_pause_reason.choices = [('', '')] + [
            (el.id, el.reason) for el in db.session.execute(
                sa.select(PauseReasons)
                .order_by(PauseReasons.reason.asc())
            ).scalars().all()
        ]

    child_select = SelectField(
        id='child-select',
        label='',
        choices=[],
        validate_choice=False,
        render_kw={'class': 'custom-select', }
    )

    cmdb_id = SelectField(
        id='affected-ci',
        label='Primary Affected CI',
        validate_choice=False,
        choices=[],
        render_kw={'class': 'custom-select dirty'},
        validators=[Optional()],
    )

    is_major = BooleanField(label='Confirm as Major', id='is-major')

    is_parent = BooleanField(
        id='is-parent',
        label='Is Parent or Child',
        render_kw={'form': 'form'}
    )

    knowledge_resolve = SelectField(
        id='knowledge-resolve',
        label='Resolve from KBA',
        choices=[],
        validators=[Optional()],
        render_kw={'class': 'custom-select'}
    )

    outage = BooleanField(label='Outage?')

    outage_start = DateTimeField(
        id='outage-start',
        label='Outage Date',
        validators=[Optional()],
        format='%Y-%m-%d %H:%M',
        render_kw={'class': 'form-control text-center picker-datetime', 'disabled': True}
    )

    outage_end = DateTimeField(
        id='outage-end',
        label='Outage End:',
        validators=[Optional()],
        format='%Y-%m-%d %H:%M',
        render_kw={'class': 'form-control text-center picker-datetime', 'disabled': True}
    )

    outage_duration_sla = StringField(
        label='Outage - Busines Hours',
        id='outage-duration-sla',
        default='00:00',
        render_kw={'readonly': True, 'class': 'dirty'}
    )

    outage_duration_total = StringField(
        label='Outage 24 hour',
        id='outage-duration-total',
        default='00:00',
        render_kw={'readonly': True}
    )

    parent_id_label = Markup("<i class='bi bi-diagram-3-fill'></i>  Select a Parent Ticket")
    parent_id = SelectField(
        id='parent-id',
        label=parent_id_label,
        choices=[],
        validators=[Optional()],
        render_kw={'class': 'dirty'}
    )

    pause_reason = StringField(id='pause-reason')

    priority = StringField(render_kw={'readonly': True, 'class': 'no-border h1'}, )
    priority_impact = StringField(id='priority-impact', default='Medium', render_kw={'readonly': True}, )
    priority_urgency = StringField(id='priority-urgency', default='Medium', render_kw={'readonly': True}, )

    problem_id = SelectField(
        id='problem-id',
        label='Linked to Problem',
        choices=[],
        validate_choice=False,
        render_kw={'class': 'form-select custom-select dirty',
                   'data-bs-title': 'Delete entry to unlink from Problem. Or unlink in the Problem ticket',
                   'data-bs-toggle':'tooltip'},
    )

    rapid_resolve = SelectField(
        id='rapid-resolve',
        label='Rapid Resolve',
        choices=[],
        validators=[Optional()],
        render_kw={'class': 'custom-select'}
    )

    review_notes = TextAreaField(
        id='review-notes',
        label='Review Notes',
        render_kw={'class': 'editor dirty', 'data-id': 'review-notes'}
    )


    sla_paused = BooleanField(
        id='sla-paused',
        label='Pause',
        # render_kw={'class': 'btn-check'}
    )

    sla_paused_at = DateTimeField(
        id='sla-paused-at',
        label='Paused at:',
        format='%Y-%m-%d %H:%M',
        validators=[Optional()],
    )

    sla_pause_reason = SelectField(
        id='sla-pause-reason',
        label='Reason',
        choices=[],
        validators=[Optional()],
        render_kw={'class': 'custom-select dirty'}
    )

    sla_resolve_by = DateTimeField(
        id='sla-resolve-by',
        label='Resolve by:',
        render_kw={'class': 'no-border', 'readonly': True},
        format='%Y-%m-%dT%H:%M',
    )

    sla_resolve_breach = BooleanField(
        id='sla-resolve-breach',
        default=False,
        render_kw={'hidden': True, 'class': 'form-check-input'},
        false_values=('False', 'false', ''),
    )

    sla_resolved = BooleanField(
        id='sla-resolved',
        label='',
        default=False,
        render_kw={ 'class': 'hidden'},
        false_values=('False', 'false', ''),
    )

    sla_respond_by = DateTimeField(
        id='sla-respond-by',
        label='Respond by:',
        render_kw={'class': 'no-border', 'readonly': True},
        format='%Y-%m-%d %H:%M',
    )

    sla_response_breach = BooleanField(
        id='sla-response-breach',
        default=False,
        render_kw={'hidden': True, 'class': 'form-check-input'},
        false_values=('False', 'false', ''),
    )

    sla_responded = BooleanField(
        id='sla-responded',
        label='',
        default=False,
        render_kw={'class': 'hidden'},
        false_values=('False', 'false', ''),
    )

    sla_responded_at = DateTimeLocalField(
        id='sla-responded-at',
        label='Responded at:',
        render_kw={'class': 'no-border', 'readonly': True},
        # format='%Y-%m-%dT%H:%M',
        validators=[Optional()],
    )

    sla_resumed_at = DateTimeField(
        id='sla-resumed-at',
        label='Resumed at:',
        render_kw={'hidden': True},
        format='%Y-%m-%d %H:%M',
        validators=[Optional()],
    )

    sla_pause_journal = TextAreaField(
        id='sla-pause-journal',
        label='Pause Journal',
        render_kw={'hidden': True, 'oninput': 'update_pause_history()'},
    )

    source_id = SelectField(
        id='source-id',
        label='Source',
        choices=[],
        default='1',
        render_kw={'class': 'custom-select dirty'})

    subcategory_id = SelectField(
        id='subcategory-id',
        label='Subcategory',
        choices=[],
        validate_choice=False,
        validators=[InputRequired()],
        render_kw={'class': 'custom-select dirty'}
    )


