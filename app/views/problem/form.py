from markupsafe import Markup
from flask_security import UserMixin
from jinja2.filters import Markup
from flask_wtf import FlaskForm
from wtforms.fields.choices import RadioField
from wtforms.fields.simple import StringField
from sqlalchemy import and_, or_, select
from wtforms import SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional, InputRequired
from ...common.forms import BaseMixin, RequesterMixin, SupportTeamMixin, UserDetailsMixin
from ...model import db
from ...model.lookup_tables import ModelLookup, ResolutionLookup
from ...model.model_category import Category
from ...model.model_cmdb import CmdbConfigurationItem
from ...model.model_interaction import Ticket
from ...model.model_user import Team
from ...model.relationship_tables import category_model


class ProblemForm(SupportTeamMixin, RequesterMixin, UserDetailsMixin, BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get all items
        items = db.session.execute(select(CmdbConfigurationItem)).scalars().all()
        # Find the maximum name length
        max_name_length = max((len(item.name) for item in items), default=0)
        self.cmdb_id.choices = [("", "")] + [
            (el.id, Markup(f'{el.name.ljust(max_name_length).replace(" ", "&nbsp;")} | {el.importance.importance}'))
            for el in items
        ]

        self.category_id.choices = [("", "")] + [
            (el.id, el.name)
            for el in db.session.execute(
                select(Category)
                .join(category_model)  # Join the association table
                .join(ModelLookup)  # Join the ModelLookup table
                .where(ModelLookup.name == "Problem")  # Filter for the desired name
            ).scalars().all()
        ]

        self.child_select.choices = [("", "")] + [
            (el.id, f"{el.ticket_number} | {el.ticket_type} | {el.short_desc}")
            for el in db.session.execute(
                select(Ticket).where(
                    and_(
                        Ticket.is_parent.is_(not True),
                        Ticket.problem_id.is_(None),
                        or_(
                            Ticket.status != "closed",
                            Ticket.status != "resolved"
                        )
                    )
                ).order_by(Ticket.ticket_number.asc())
            ).scalars().all()
        ]

        self.resolution_code_id.choices = [("", "")] + [
            (el.id, el.resolution)
            for el in
            db.session.execute(
                select(ResolutionLookup)
                .where(ResolutionLookup.model == 'Problem')
                .order_by(ResolutionLookup.resolution.asc())
            ).scalars().all()
        ]

    analysis_method = RadioField(
        id="analysis-method",
        label="Analysis Method",
        validate_choice=False,
        choices=[('generic', 'Generic'), ('five_whys', '5 Whys'), ('kepner_tregoe', 'Kepner Tregoe')],
        default='analysis_generic',
        render_kw={"class": "custom-radio"},
    )

    child_select = SelectField(
        id='child-select',
        label='',
        choices=[],
        validate_choice=False,
        render_kw={'class': 'custom-select', }
    )

    cmdb_id = SelectField(
        id="affected-ci",
        label="Primary Affected CI",
        validate_choice=False,
        choices=[],
        render_kw={"class": "custom-select dirty"},
        validators=[Optional()],
    )

    generic_rca_notes = TextAreaField(
        id="generic-rca-notes",
        label="RCA Reasoning Notes",
        validators=[Optional()],
        render_kw={"class": "editor minimum-editor"},
    )

    generic_root_cause = TextAreaField(
        id="generic-root-cause",
        label="Probable Root Cause",
        validators=[Optional()],
        render_kw={"class": "editor minimum-editor"}, )

    priority = StringField(render_kw={"readonly": True, "class": "no-border h1"}, )

    # class KepnerTregoeForm(FlaskForm):
    what_is_happening = TextAreaField(
        label='What IS happening?',
        id='what-is-happening',
        render_kw={'class': 'editor minimum-editor'}
    )

    what_should_be_happening = TextAreaField(
        label='What SHOULD be happening?',
        id='what-should-be-happening',
        render_kw={'class': 'editor minimum-editor'}
    )

    # Problem Specification
    where_is = TextAreaField(
        label=Markup('<strong>WHERE <span class="text-danger bold">IS</span></strong> the problem occurring?'),
        id='where-is',
        render_kw={'class': 'editor minimum-editor'}
    )

    where_is_not = TextAreaField(
        label=Markup('<span class="text-danger bold">WHERE</span> could it occur but does <span class="text-danger bold">NOT</span>?'),
        id='where-is-not',
        render_kw={'class': 'editor minimum-editor'}
    )

    where_distinction = TextAreaField(
        label=Markup('<span class="text-warning">WHERE Distinction</span>'),
        id='where-distinction',
        render_kw={'class': 'editor minimum-editor'}
    )

    when_is = TextAreaField(
        label=Markup('<strong>WHEN <span class="text-danger bold">IS</span></strong> the problem occurring?'),
        id='when-is',
        render_kw={'class': 'editor minimum-editor'}
    )

    when_is_not = TextAreaField(
        label=Markup('<strong>WHEN</strong> could it occur but does <span class="text-danger bold">NOT</span>?'),
        id='when-is-not',
        render_kw={'class': 'editor minimum-editor'}
    )

    when_distinction = TextAreaField(
        label=Markup('<span class="text-warning">WHEN Distinction</span>'),
        id='when-distinction',
        render_kw={'class': 'editor minimum-editor'}
    )

    what_extent_is = TextAreaField(
        label=Markup('<strong>WHAT <span class="text-danger bold">IS</span></strong> the extent/magnitude?'),
        id='what-extent-is',
        render_kw={'class': 'editor minimum-editor'}
    )

    what_extent_is_not = TextAreaField(
        label=Markup('<strong>WHAT</strong> could be the extent but is <span class="text-danger bold">NOT</span>?'),
        id='what-extent-is-not',
        render_kw={'class': 'editor minimum-editor'}
    )

    what_extent_distinction = TextAreaField(
        label=Markup('<span class="text-warning">WHAT Distinction</span>'),
        id='what-extent-distinction',
        render_kw={'class': 'editor minimum-editor'}
    )

    # Analysis
    distinctions = TextAreaField(
        label=Markup(
            'Can you identify any patterns from the <strong>distinctions</strong>?'),
        id='distinctions',
        render_kw={'class': 'editor minimum-editor'}
    )

    changes = TextAreaField(
        label=Markup('What <span class="text-danger bold">changes</span> have occurred?'),
        id='changes',
        render_kw={'class': 'editor minimum-editor'}
    )

    possible_causes = TextAreaField(
        label='Possible Causes',
        id='possible-causes',
        render_kw={'class': 'editor minimum-editor'}
    )

    most_probable_cause = TextAreaField(
        label='Most Probable Cause',
        id='most-probable-cause',
        render_kw={'class': 'editor minimum-editor'}
    )

    test_results = TextAreaField(
        label='Test Results',
        id='test-results',
        render_kw={'class': 'editor minimum-editor'}
    )

    kt_root_cause = TextAreaField(
        label='Root Cause',
        id='kt-root-cause',
        render_kw={'class': 'editor minimum-editor'}
    )

    # class FiveWhysForm(FlaskForm):
    why_1_question = TextAreaField(
        label='Why #1 Question',
        id='why-1-question',
        render_kw={'class': 'editor minimum-editor'}
    )

    why_1_answer = TextAreaField(
        label='Why #1 Answer',
        id='why-1-answer',
        render_kw={'class': 'editor minimum-editor'}
    )

    why_2_question = TextAreaField(
        label='Why #2 Question',
        id='why-2-question',
        render_kw={'class': 'editor minimum-editor'}
    )

    why_2_answer = TextAreaField(
        label='Why #2 Answer',
        id='why-2-answer',
        render_kw={'class': 'editor minimum-editor'}
    )

    why_3_question = TextAreaField(
        label='Why #3 Question',
        id='why-3-question',
        render_kw={'class': 'editor minimum-editor'}
    )

    why_3_answer = TextAreaField(
        label='Why #3 Answer',
        id='why-3-answer',
        render_kw={'class': 'editor minimum-editor'}
    )

    why_4_question = TextAreaField(
        label='Why #4 Question',
        id='why-4-question',
        render_kw={'class': 'editor minimum-editor'}
    )

    why_4_answer = TextAreaField(
        label='Why #4 Answer',
        id='why-4-answer',
        render_kw={'class': 'editor minimum-editor'}
    )

    why_5_question = TextAreaField(
        label='Why #5 Question',
        id='why-5-question',
        render_kw={'class': 'editor minimum-editor'}
    )

    why_5_answer = TextAreaField(
        label='Why #5 Answer',
        id='why-5-answer',
        render_kw={'class': 'editor minimum-editor'}
    )

    why_root_cause = TextAreaField(
        label='Root Cause Identified',
        id='why-root-cause',
        render_kw={'class': 'editor minimum-editor'}
    )

    corrective_actions = TextAreaField(
        label='Corrective Actions',
        id='corrective-actions',
        render_kw={'class': 'editor minimum-editor'}
    )

    preventive_actions = TextAreaField(
        label='Preventive Actions',
        id='preventive-actions',
        render_kw={'class': 'editor minimum-editor'}
    )
