import sqlalchemy as sa
from wtforms.fields.choices import SelectField, SelectMultipleField, RadioField
from wtforms.fields.datetime import DateTimeLocalField, DateTimeField
from wtforms.fields.simple import StringField, BooleanField, TextAreaField
from wtforms.validators import Optional, DataRequired

from ...common.forms import SupportTeamMixin, RequesterMixin, UserDetailsMixin, BaseMixin
from ...model import db
from ...model.lookup_tables import ModelLookup, ResolutionLookup
from ...model.model_category import Category
from ...model.model_change import Change
from ...model.model_cmdb import CmdbConfigurationItem
from ...model.model_release import ReleaseTypesLookup
from ...model.model_user import Team, User, Role
from ...model.relationship_tables import category_model


class ReleaseForm(SupportTeamMixin, RequesterMixin, UserDetailsMixin, BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.build_leader_id.choices = [('', '')] + [
            (el.id, el.full_name)
            for el in
            db.session.execute(
                sa.select(User)
                .where(sa.and_(User.active == True, User.roles.any(Role.name == 'Release/Deploy')))
                .order_by(User.username.asc())
            ).scalars().all()
        ]

        self.category_id.choices = [('', '')] + [
            (el.id, el.name)
            for el in db.session.execute(
                sa.select(Category)
                .join(category_model)  # Join the association table
                .join(ModelLookup)  # Join the ModelLookup table
                .where(ModelLookup.name == 'Release')  # Filter for the desired name
            ).scalars().all()
        ]

        self.change_id.choices = [('', '')] + [
            (el.id, f'{el.ticket_number} | {el.short_desc}') for el in
            db.session.execute(
                sa.select(Change)
                .where(sa.and_(
                    Change.status != 'closed',
                    Change.change_type == 'Normal')
                )
                .order_by(Change.ticket_number.asc())
            ).scalars().all()
        ]

        self.deployment_leader_id.choices = [('', '')] + [
            (el.id, el.full_name)
            for el in
            db.session.execute(
                sa.select(User)
                .where(
                    sa.and_(
                        User.active == True,
                        User.roles.any(Role.name == 'Release/Deploy')
                    )
                )
                .order_by(User.username.asc())
            ).scalars().all()
        ]

        self.product_owner_id.choices = [('', '')] + [
            (el.id, el.full_name)
            for el in db.session.execute(
                sa.select(User)
                .where(
                    sa.and_(
                        User.active == True,
                        User.roles.any(Role.name == 'Product Owner')
                    )
                )
                .order_by(User.username.asc())
            ).scalars().all()
        ]

        self.release_type_id.choices = [('', '')] + [
            (el.id, el.release_type) for el in
            db.session.execute(
                sa.select(ReleaseTypesLookup)
                .order_by(ReleaseTypesLookup.release_type.asc())
            ).scalars().all()
        ]

        self.resolution_code_id.choices = [('', '')] + [
            (el.id, el.resolution)
            for el in
            db.session.execute(
                sa.select(ResolutionLookup)
                .where(ResolutionLookup.model == 'Release')
                .order_by(ResolutionLookup.resolution.asc()))
            .scalars().all()
        ]

        self.support_team_id.choices = [('', '')] + [
            (el.id, el.name) for el in
            db.session.execute(
                sa.select(Team)
                .order_by(Team.name.asc())
            ).scalars().all()
        ]

        self.test_leader_id.choices = [('', '')] + [
            (el.id, el.full_name)
            for el in
            db.session.execute(
                sa.select(User)
                .where(sa.and_(User.active == True, User.roles.any(Role.name == 'Tester')))
                .order_by(User.username.asc())
            ).scalars().all()
        ]

    affected_cis = SelectMultipleField(
        id='affected-cis',
        label='CIs Used for Build',
        choices=[],
        validate_choice=False,
        render_kw={'class': 'dirty'}
    )

    approved = BooleanField(
        id='approved',
        label='Approved?',
        render_kw={'class': 'dirty'}
    )

    approval_by = RadioField(
        id='approval-by',
        label='Approval By?',
        choices=[('Product Owner', 'Product Owner'), ('CAB', 'CAB')],
        default='Product Owner',
        render_kw={'class': 'dirty'}
    )

    approval_notes = TextAreaField(
        id='approval-notes',
        label='Approval Notes',
        render_kw={'class': 'editor dirty', },
    )

    build_date = DateTimeField(
        id='build-date/time',
        label='Build Date',
        format='%Y-%m-%d %H:%M',
        validators=[Optional()],
        render_kw={'class': 'picker-datetime', 'placeholder': 'Select a date...'},
    )

    build_leader_id = SelectField(
        id='build-leader',
        label='Build Leader',
        choices=[],
        render_kw={'class': 'custom-select dirty'}
    )

    build_plan = TextAreaField(
        id='build-plan',
        label='Build Plan',
        render_kw={'class': 'editor dirty', },
    )

    change_id = SelectField(
        id='change-id',
        label='Change ID',
        choices=[],
        render_kw={'class': 'custom-select dirty'}
    )

    cis_selection = SelectField(
        id='cis-selection',
        label='Select Required CIs',
        choices=[],
        validate_choice=False,
        render_kw={'class': 'custom-select dirty'}
    )

    deployment_date = DateTimeField(
        id='deployment-date',
        label='Deployment Date',
        format='%Y-%m-%d %H:%M',
        validators=[Optional()],
        render_kw={'class': 'picker-datetime', 'readonly': True},
    )

    deployment_leader_id = SelectField(
        id='deployment-leader',
        label='Deployment Leader',
        choices=[],
        render_kw={'class': 'custom-select dirty'}
    )

    deployment_notes = TextAreaField(
        id='deployment-notes',
        label='Deployment Notes',
        render_kw={'class': 'editor dirty', },
    )

    deployment_risks = TextAreaField(
        id='deployment-risks',
        label='Deployment Risks',
        render_kw={'class': 'editor dirty', },
    )

    deployment_successful = BooleanField(
        id='deployment-successful',
        label='Deployment Successful?',
        render_kw={'class': 'dirty'}
    )

    deployment_summary = TextAreaField(
        id='deployment-summary',
        label='Deployment Summary',
        render_kw={'class': 'editor dirty', },
    )

    product_owner_id = SelectField(
        id='product-owner',
        label='Product Owner',
        choices=[],
        render_kw={'class': 'custom-select dirty'}
    )

    release_date = DateTimeField(
        id='release-date',
        label='Release Date',
        format='%Y-%m-%d %H:%M',
        validators=[Optional()],
        render_kw={'class': 'picker-datetime', 'placeholder': 'Select a date/time...'},
    )

    release_dependencies = TextAreaField(
        id='release-dependencies',
        label='Release Dependencies',
        render_kw={'class': 'editor dirty', },
    )

    release_method = SelectField(
        id='release-method',
        label='Release Method',
        choices=[('Manual', 'Manual'), ('Scheduled', 'Scheduled')],
        render_kw={'class': 'custom-select dirty'}
    )

    release_name = StringField(
        id='release-name',
        label='Release Name',
        validators=[DataRequired()],
        render_kw={'class': 'dirty'}
    )

    release_risks = TextAreaField(
        id='release-risks',
        label='Release Risks',
        render_kw={'class': 'editor dirty', },
    )

    release_stage = StringField(
        id='release-stage',
        label='Release Stage',
        validators=[Optional()],
        render_kw={'class': 'dirty'}
    )

    release_successful = BooleanField(
        id='release-successful',
        label='Release Successful',
        render_kw={'class': 'dirty'}
    )

    release_type_id = SelectField(
        id='release-type',
        label='Release Type',
        choices=[],
        validators=[DataRequired()],
        render_kw={'class': 'custom-select dirty', }
    )

    release_version = StringField(
        id='release-version',
        label='Release Version',
        validators=[Optional()],
        render_kw={'class': 'dirty'}
    )

    review_notes = TextAreaField(
        id='review-notes',
        label='Review Notes / Lessons Learnt',
        render_kw={'class': 'editor dirty', },
    )

    scheduled_date = DateTimeLocalField(
        id='scheduled-date',
        label='Scheduled Date',
        render_kw={'class': 'dirty'}
    )

    support_team_id = SelectField(
        id='support-team',
        label='Support Team',
        choices=[],
        validate_choice=False,
        validators=[DataRequired()],
        render_kw={'class': 'custom-select dirty', }
    )

    test_leader_id = SelectField(
        id='test-leader',
        label='Test Leader',
        choices=[],
        validate_choice=False,
        render_kw={'class': 'custom-select dirty'}
    )

    test_successful = BooleanField(
        id='test-successful',
        label='Testing Successful',
        render_kw={'class': 'dirty'}
    )

    test_plan = TextAreaField(
        label='Test Plan',
        id='test-plan',
        render_kw={'class': 'editor dirty', },
    )
