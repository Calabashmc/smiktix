from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DecimalRangeField,
    SelectField,
    SelectMultipleField,
    StringField,
    TextAreaField,
    widgets
)
from wtforms.fields.choices import RadioField
from wtforms.validators import Optional
from sqlalchemy import select

from ...common.forms import BaseMixin, MultipleCheckboxField, RequesterMixin, SupportTeamMixin, UserDetailsMixin
from ...model import db
from ...model.lookup_tables import BenefitsLookup, BudgetBucketsLookup, ImpactLookup, ModelLookup, ResolutionLookup
from ...model.model_category import Category
from ...model.model_user import User
from ...model.relationship_tables import category_model



class IdeasForm(RequesterMixin, UserDetailsMixin, SupportTeamMixin, BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.benefits.choices = [
            (str(el.id), f'{el.benefit} - {el.comment}')
            for el in db.session.execute(
                select(BenefitsLookup)
                .order_by(BenefitsLookup.benefit.asc())
            ).scalars().all()
        ]
        self.benefits.data = self.benefits.data or []

        self.category_id.choices = [('', '')] + [
            (el.id, el.name)
            for el in db.session.execute(
                select(Category)
                .join(category_model)  # Join the association table
                .join(ModelLookup)  # Join the ModelLookup table
                .where(ModelLookup.name == "Idea")  # Filter for the desired name
            ).scalars().all()
        ]

        self.estimated_cost.choices = [
            (el.budget_bucket, el.budget_bucket)
            for el in db.session.execute(
                select(BudgetBucketsLookup)
            ).scalars().all()
        ]
        # Set default value for estimated_cost
        if not self.estimated_cost.data and self.estimated_cost.choices:
            self.estimated_cost.data = self.estimated_cost.choices[0][0]

        self.impact.choices = [
            (str(el.id), f'{el.impact} - {el.comment}')
            for el in db.session.execute(
                select(ImpactLookup)
                .order_by(ImpactLookup.impact.asc())
            ).scalars().all()
        ]
        self.impact.data = self.impact.data or []

        self.resolution_code_id.choices = [("", "")] + [
            (el.id, el.resolution)
            for el in
            db.session.execute(
                select(ResolutionLookup)
                .where(ResolutionLookup.model == 'Idea')
                .order_by(ResolutionLookup.resolution.asc())
            ).scalars().all()
        ]

    current_issue = TextAreaField(
        label="Current Issue",
        id="current-issue",
        render_kw={"class": "editor"}
    )

    benefits = MultipleCheckboxField(
        label="Benefit",
        id="benefit",
        # coerce=int,
        render_kw={"class": "dirty"},
    )

    business_goal_alignment = TextAreaField(
        label="Business Goal Alignment",
        id="business-goal-alignment",
        render_kw={"class": "editor"}
    )

    dependencies = TextAreaField(
        label="Dependencies",
        id="dependencies",
        render_kw={"class": "editor"}
    )

    estimated_effort = RadioField(
        id="estimated-effort",
        label='Estimated Effort',
        choices=[
            ('Low', 'Low'),
            ('Medium', 'Medium'),
            ('High', 'High'),
        ],
        default="Low",
        render_kw={"class": "dirty custom-radio"}
    )

    estimated_cost = RadioField(
        id="estimated-cost",
        label='Budget Requirement',
        choices=[],
        render_kw={"class": "dirty custom-radio"}
    )

    impact = MultipleCheckboxField(
        label="Impact",
        id="impact",
        # coerce=int,
        render_kw={"class": "dirty"}
    )

    likelihood = StringField(
        label="Likelihood",
        default="TBD",
        render_kw={"class": "type-no-border text-center", "readonly": True})

    risks_challenges = TextAreaField(
        label="Risks & Challenges",
        id="risks-challenges",
        render_kw={"class": "editor"}
    )

    vote_count = StringField(
        id="vote-count",
        default=0,
        render_kw={"class": "vote vote-count", "readonly": True},
    )

    vote_score = StringField(
        id="vote-score",
        default=0,
        render_kw={"class": "vote vote-score", "readonly": True},
    )
