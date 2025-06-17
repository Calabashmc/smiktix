import sqlalchemy as sa
from flask_wtf import FlaskForm
from jinja2.filters import Markup

from wtforms import (
    BooleanField,
    DateField,
    DateTimeField,
    DateTimeLocalField,
    DecimalRangeField,
    RadioField,
    SelectField,
    SelectMultipleField,
    StringField,
    TextAreaField,
    TimeField
)
from wtforms.validators import Optional, InputRequired
from wtforms.widgets import TextInput
from ...common.forms import (
    SupportTeamMixin,
    RequesterMixin,
    UserDetailsMixin,
    BaseMixin,
    DateTimeTextField,
    DateTextField,
    TimeTextField
)
from ...model import db
from ...model.lookup_tables import ChangeWindowLookup, ModelLookup, ResolutionLookup
from ...model.model_user import Department, Role, Team, User
from ...model.model_change import ChangeReasons, ChangeTemplates
from ...model.model_category import Category
from ...model.model_cmdb import CmdbConfigurationItem
from ...model.model_interaction import Ticket
from ...model.model_problem import Problem
from ...model.model_release import Release
from ...model.relationship_tables import category_model


class ChangeForm(SupportTeamMixin, RequesterMixin, UserDetailsMixin, BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.category_id.choices = [('', '')] + [
            (el.id, el.name)
            for el in db.session.execute(
                sa.select(Category)
                .join(category_model)  # Join the association table
                .join(ModelLookup)  # Join the ModelLookup table
                .where(ModelLookup.name == 'Change')  # Filter for the desired name
            ).scalars().all()
        ]

        self.change_reason.choices = [('', '')] + [
            (el.id, el.reason) for el in
            db.session.execute(
                sa.select(ChangeReasons)
                .order_by(ChangeReasons.reason.asc())
            ).scalars().all()
        ]

        self.child_select.choices = [('', '')] + [
            (el.id, f'{el.ticket_number} | {el.ticket_type} | {el.short_desc}')
            for el in db.session.execute(
                sa.select(Ticket).where(
                    sa.and_(
                        Ticket.is_parent.is_(not True),
                        Ticket.problem_id.is_(None),
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

        self.departments_impacted.choices = [(0, '')] + [
            (el.id, el.name) for el in
            db.session.execute(
                sa.select(Department)
                .order_by(Department.name.asc())
            ).scalars().all()
        ]

        self.resolution_code_id.choices = [('', '')] + [
            (el.id, el.resolution)
            for el in
            db.session.execute(
                sa.select(ResolutionLookup)
                .where(ResolutionLookup.model == 'Change')
                .order_by(ResolutionLookup.resolution.asc()))
            .scalars().all()
        ]

    change_cancelled = BooleanField(id='change-cancelled',
                                    label='Cancelled/Denied',
                                    render_kw={'class': 'dirty', 'as_switch': True},
                                    )

    # main page
    change_reason = SelectField(
        id='change-reason',
        label='Reason for Change',
        choices=[],
        render_kw={'class': 'custom-select dirty'},
        validators=[InputRequired()],
    )

    # on resolution tab
    change_successful = BooleanField(
        id='change-successful',
        name='change-successful-radio',
        label='Change Succesful?',
        render_kw={'class': 'dirty'},
    )

    change_template = SelectField(
        id='change-template',
        label='Change Template',
        choices=[],
        validators=[Optional()],
        render_kw={'class': 'dirty'},
    )

    # main page
    change_type = SelectField(
        id='change-type',
        label='Change Type',
        choices=['Standard', 'Normal', 'Emergency'],
        render_kw={'class': 'hidden'},
    )

    child_select = SelectField(
        id='child-select',
        label='',
        choices=[],
        validate_choice=False,
        render_kw={'class': 'custom-select', }
    )

    # main page
    cmdb_id = SelectField(
        id='cmdb-id',
        label='Primary CI Impacted ',
        choices=[],
        validate_choice=False,
        render_kw={'class': 'custom-select dirty'},
    )

    # Not used
    completed_at = DateTimeField(
        id='completed-at',
        label='Resolved at',
        format='%H:%M on %d/%m/%Y',
        validators=[Optional()],
        render_kw={'class': 'dirty picker-datetime', 'placeholder': 'Select Date/Time'},
    )

    comms_plan = TextAreaField(
        id='comms-plan',
        label='Comms Plan',
        render_kw={'hidden': False, 'class': 'editor dirty', },
    )

    # main page
    departments_impacted = SelectMultipleField(
        id='departments-impacted',
        label='Departments Impacted',
        choices=[],
        coerce=int,
        validate_choice=False,
        render_kw={'class': 'custom-multi-select dirty'},
    )

    end_date = DateField(
        id='end-date',
        label='End Date',
        validators=[InputRequired()],
        render_kw={'class': 'dirty picker-date', 'placeholder': 'Select Date'},
    )

    end_time = TimeField(
        id='end-time',
        validators=[InputRequired()],
        render_kw={'class': 'dirty picker-only-time', 'placeholder': 'Select Time'},
    )

    # details tab
    expected_duration = DecimalRangeField(
        id='change-duration',
        label='Expected Duration (hours)',
        validators=[Optional()],
        render_kw={'type': 'range',
                   'value': '0.5',
                   'min': '0.5',
                   'max': '12',
                   'step': '0.5',
                   'style': '--min: 0.5; --max: 12; --val: 0.5',
                   'class': 'dirty'},
    )

    # resolution tab
    extended_outage = BooleanField(
        id='extended-outage',
        label='Taking too long?',
        render_kw={'class': 'dirty', 'as_switch': True},
    )

    implement_plan = TextAreaField(
        id='implement-plan',
        label='Implement Plan',
        render_kw={'hidden': False, 'class': 'editor dirty', },
    )

    # resolution tab
    other_fail_reason = StringField(
        id='other-fail-reason',
        label='Other Reason',
    )

    review_notes = TextAreaField(
        id='review-notes',
        label='Change Result',
        render_kw={'hidden': False, 'class': 'editor dirty', },
    )

    risk_set = StringField(
        id='priority',
        label='Set Risk',
        render_kw={'class': 'dirty no-border h1 p-2 text-center', 'style': 'width: 50%',
                   'readonly': True},
    )

    # resolution tab
    rollback_required = BooleanField(
        id='rollback-required',
        label='Rollback required?',
        render_kw={'class': 'dirty', 'as_switch': True},
    )

    start_date = DateField(
        id='start-date',
        label='Start Date',
        validators=[InputRequired()],
        render_kw={'class': 'dirty picker-date', 'placeholder': 'Select date'}
    )

    start_time = TimeField(
        id='start-time',
        validators=[InputRequired()],
        render_kw={'class': 'dirty picker-only-time', 'placeholder': 'Select time'}
    )
    # Resolution tab
    vendor_issue = BooleanField(
        id='vendor-issue',
        label='Vendor issue?',
        render_kw={'class': 'dirty', 'as_switch': True},
    )


class EmergenceyChangeForm(ChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ecab_approver_id.choices = [('', '')] + [
            (el.id, el.full_name) for el in
            db.session.execute(
                sa.select(User).where(
                    User.roles.any(Role.name == 'CAB member')  # Check if any related role matches
                )
            ).scalars().all()
        ]

        self.child_ticket_id.choices = [('', '')] + [
            (el.id, f'{el.ticket_number} - {el.short_desc}') for el in
            db.session.execute(
                sa.select(Ticket)
                .where(sa.or_(Ticket.priority == 'P1', Ticket.priority == 'P2'))
                .where(sa.and_(Ticket.status != 'closed', Ticket.parent_id == None))
                .order_by(Ticket.ticket_number.asc())
            ).scalars().all()
        ]

    ecab_approved = BooleanField(
        id='ecab-approved',
        label='eCAB approved?',
        render_kw={'class': 'dirty'},
    )

    ecab_approver_id = SelectField(
        id='ecab-approver',
        label='eCAB approver',
        choices=[],
        validators=[InputRequired()],
        render_kw={'class': 'custom-select dirty'},
    )

    child_ticket_id = SelectField(
        id='child-ticket',
        label='Related Major Incident',
        choices=[],
        validators=[Optional()],
        render_kw={'class': 'custom-select dirty'}
    )

class NormalChangeForm(ChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.change_windows.choices = [('', '')] + [
            (el.day, f'{el.day} {el.start_time} ({el.length}hrs) ') for el in
            db.session.execute(
                sa.select(ChangeWindowLookup)
                .where(ChangeWindowLookup.active == True)
            ).scalars().all()
        ]

        self.child_select.choices = (
                [
                    (el.id, str(el.ticket_number) + ' | ' + el.ticket_type + ' | ' + el.short_desc)
                    for el in
                    db.session.execute(
                        sa.select(Ticket)
                        .where(
                            sa.and_(Ticket.status != 'closed', Ticket.status != 'resolved', Ticket.parent_id == None))
                    ).scalars().all()
                ] +
                [
                    (el.id,
                     str(el.ticket_number) + ' | ' + el.ticket_type + ' | ' + el.short_desc)
                    for el in
                    db.session.execute(
                        sa.select(Problem)
                        .where(sa.and_(Problem.status != 'closed', Problem.status != 'resolved'))
                    ).scalars().all()
                ] +
                [
                    (el.id, str(el.ticket_number) + ' | ' + el.ticket_type + ' | ' + el.short_desc)
                    for el in
                    db.session.execute(
                        sa.select(Release)
                        .where(sa.and_(Release.status != 'closed', Release.status != 'resolved'))
                    ).scalars().all()
                ]
        )

        self.test_lead.choices = [('', '')] + [
            (el.id, el.full_name) for el in
            db.session.execute(
                sa.select(User)
                .where(User.roles.any(Role.name == 'Tester'))
                .order_by(User.full_name.asc())
            ).scalars().all()
        ]

    child_select = SelectField(
        id='child-select',
        label='',
        choices=[],
        validate_choice=False,
        render_kw={'class': 'custom-select', }
    )

    change_windows = SelectField(
        id='change-windows',
        label='Change Windows',
        choices=[],
        validate_choice=False,
        render_kw={'class': 'custom-select dirty'},
    )

    # on approvers tab
    approvers_selection = SelectMultipleField(
        id='approvers-selection',
        label='Approvers',
        validate_choice=False,
        choices=[],
        render_kw={'class': 'approvers-select'},
    )

    approved_selection = SelectMultipleField(
        id='approved-selection',
        label='Approvers',
        validate_choice=False,
        choices=[],
        render_kw={'class': 'approved-select'},
    )

    approval_stakeholders = SelectField(
        label='Stakeholders',
        id='approval-stakeholders',
        validate_choice=False,
        choices=[],
        render_kw={'class': 'custom-select'},
    )

    # on details tab
    build_date = DateField(
        label='Build Date',
        validators=[Optional()],
        render_kw={'class': 'dirty picker-date', 'placeholder': 'Select Build Date...'},
    )

    # on plans tabe
    build_plan = TextAreaField(
        label='Build Plan',
        render_kw={'class': 'editor dirty', },
    )

    cab_date = DateTimeField(
        id='cab-date',
        label='CAB Date:',
        format='%Y-%m-%d %H:%M',
        validators=[Optional()],
        render_kw={'class': 'dirty picker-datetime', 'placeholder': 'Select CAB Date/Time...'},
    )

    cab_approval_status = StringField(
        id='cab-approval-status',
        default='pending',
        render_kw={'hidden': True, }
    )  # approval status on cab tab used to email change owner of CAB outcome

    cab_check_approver_consensus = BooleanField(label='Approver consensus')
    cab_check_category = BooleanField(label='Categorised correctly')
    cab_check_no_clash = BooleanField(label='No clash detected')
    cab_check_plan_build = BooleanField(label='Build plan is acceptable')
    cab_check_plan_comms = BooleanField(label='Comms plan is acceptable')
    cab_check_plan_implement = BooleanField(label='Implementation plan is acceptable')
    cab_check_plan_impact = BooleanField(label='Impact plan is acceptable')
    cab_check_plan_rollback = BooleanField(label='Rollback plan is acceptable')
    cab_check_plan_test = BooleanField(label='Test plan is acceptable')
    cab_check_reason = BooleanField(label='Reason for Change is correct')
    cab_check_security = BooleanField(label='Security approves')
    cab_check_timing = BooleanField(label='Timing is suitable')

    cab_notes = TextAreaField(id='cab-notes',
                              render_kw={'hidden': False, 'class': 'editor dirty'},
                              )

    cab_ready = BooleanField(
        id='cab-ready',
        label='Ready for Cab',
    )

    # details tab
    downtime = DecimalRangeField(
        id='change-downtime',
        label='Outage/Downtime (hours)',
        render_kw={'value': '0',
                   'min': '0',
                   'max': '12',
                   'step': '0.5',
                   'style': '--min: 0; --max: 12; --val: 0',
                   },
        validators=[Optional()],
    )

    # plans tab
    effects_plan = TextAreaField(
        id='effects-plan',
        label='Additional Impact',
        render_kw={'hidden': False, 'class': 'editor dirty', },
    )

    # details tab
    people_impact = SelectField(
        id='people-impact',
        choices=(
            (0, '0%'),
            (2, '1% - 5%'),
            (4, '5% - 10%'),
            (6, '10% - 25%'),
            (12, '25% - 50%'),
            (18, '50% - 100%')
        ),
        coerce=int,
        default=0,
        render_kw={'class': 'dirty'}
    )

    # Details tab
    # id has to be in camel case due to risk.js needing it that way. I've been a bit anal about setting IDs
    # in kebab case due to reading somewhere that it is best practice for html fields and flask-wtf defaults to camel
    # case. I have no idea why. I've wasted a lot of time setting up trivial things like this rather than just use the
    # default. So the fields below I didn't need to specify an id at all but still did to be consistent. OCD much?
    risk_continuity = BooleanField(
        id='risk_continuity',
        label='',
        render_kw={'class': 'dirty',
                   'as_switch': True,
                   'data-bs-target': '#collapseContinuity'
                   },
    )

    risk_continuity_impact = RadioField(
        id='risk_continuity_impact',
        label='Impact',
        choices=[('Low', 'Low'), ('Medium', 'Medium'),
                 ('High', 'High')],
        default='Low',
        render_kw={'class': 'dirty'},
    )

    risk_continuity_likelihood = RadioField(
        id='risk_continuity_likelihood',
        label='Likelihood',
        choices=[('Low', 'Low'), ('Medium', 'Medium'),
                 ('High', 'High')],
        default='Low',
        render_kw={'class': 'dirty'},
    )

    risk_calc = StringField(
        id='risk-calc',
        label='Calculated Risk',
        render_kw={'class': 'no-border h1 p-2 text-center', 'style': 'width: 50%',
                   'readonly': True},
    )

    # details tab
    risk_customer = BooleanField(
        id='risk_customer',  # has to be camel case
        label='',
        render_kw={'class': 'dirty',
                   'as_switch': True,
                   'data-bs-target': '#collapseCustomer'
                   },
    )

    risk_customer_impact = RadioField(
        id='risk_customer_impact',
        label='Impact',
        choices=[('Low', 'Low'), ('Medium', 'Medium'),
                 ('High', 'High')],
        default='Low',
        render_kw={'class': 'dirty'},
    )

    risk_customer_likelihood = RadioField(
        id='risk_customer_likelihood',  # has to be camel case
        label='Likelihood',
        choices=[('Low', 'Low'), ('Medium', 'Medium'),
                 ('High', 'High')],
        default='Low',
        render_kw={'class': 'dirty'},
    )

    risk_data = BooleanField(
        id='risk_data',  # has to be camel case
        label='',
        render_kw={'class': 'dirty',
                   'as_switch': True,
                   'data-bs-target': '#collapseData'
                   },
    )

    risk_data_impact = RadioField(
        id='risk_data_impact',  # has to be camel case
        label='Impact',
        choices=[('Low', 'Low'), ('Medium', 'Medium'),
                 ('High', 'High')],
        default='Low',
        render_kw={'class': 'dirty'},
    )

    risk_data_likelihood = RadioField(
        id='risk_data_likelihood',  # has to be camel case
        label='Likelihood',
        choices=[('Low', 'Low'), ('Medium', 'Medium'),
                 ('High', 'High')],
        default='Low',
        render_kw={'class': 'dirty'},
    )

    risk_financial = BooleanField(
        id='risk_financial',  # has to be camel case
        label='',
        render_kw={'class': 'dirty',
                   'as_switch': True,
                   'data-bs-target': '#collapseFinancial',
                   },
    )

    risk_financial_impact = RadioField(
        id='risk_financial_impact',  # has to be camel case
        label='Impact',
        choices=[('Low', 'Low'), ('Medium', 'Medium'),
                 ('High', 'High')],
        default='Low',
        render_kw={'class': 'dirty'},
    )

    risk_financial_likelihood = RadioField(
        id='risk_financial_likelihood',  # has to be camel case
        label='Likelihood',
        choices=[('Low', 'Low'), ('Medium', 'Medium'),
                 ('High', 'High')],
        default='Low',
        render_kw={'class': 'dirty'},
    )

    # main page
    risk_reputation = BooleanField(
        id='risk_reputation',  # has to be camel case
        label='',
        render_kw={'class': 'dirty',
                   'as_switch': True,
                   'data-bs-target': '#collapseReputation'
                   },
    )

    risk_reputation_impact = RadioField(
        id='risk_reputation_impact',  # has to be camel case
        label='Impact',
        choices=[('Low', 'Low'), ('Medium', 'Medium'),
                 ('High', 'High')],
        default='Low',
        render_kw={'class': 'dirty'},
    )

    risk_reputation_likelihood = RadioField(
        id='risk_reputation_likelihood',  # has to be camel case
        label='Likelihood',
        choices=[('Low', 'Low'), ('Medium', 'Medium'),
                 ('High', 'High')],
        default='Low',
        render_kw={'class': 'dirty'},
    )

    # details tab
    risk_security = BooleanField(
        id='risk_security',  # has to be camel case
        label='',
        render_kw={'class': 'dirty',
                   'as_switch': True,
                   'data-bs-target': '#collapseSecurity'
                   },
    )

    risk_security_impact = RadioField(
        id='risk_security_impact',  # has to be camel case
        label='Impact',
        choices=[('Low', 'Low'), ('Medium', 'Medium'),
                 ('High', 'High')],
        default='Low',
        render_kw={'class': 'dirty'},
    )

    risk_security_likelihood = RadioField(
        id='risk_security_likelihood',  # has to be camel case
        label='Likelihood',
        choices=[('Low', 'Low'), ('Medium', 'Medium'),
                 ('High', 'High')],
        default='Low',
        render_kw={'class': 'dirty'},
    )

    # plans tab
    rollback_plan = TextAreaField(
        id='rollback-plan',
        label='Rollback Plan',
        render_kw={'hidden': False, 'class': 'editor dirty', },
    )

    # main page
    scale = SelectField(
        id='change-scale',
        label='Scale/Scope',
        choices=['Minor', 'Medium', 'Major'],
        default='Medium',
        validators=[Optional()],
        render_kw={'class': 'dirty'},
    )

    # test tab
    test_end_date = DateField(
        id='test-end-date',
        label='Test End Date',
        validators=[Optional()],
        render_kw={'class': 'dirty picker-date', 'placeholder': 'Select date'}
    )

    test_lead = SelectField(
        id='test-lead',
        label='Test Lead',
        choices=[],
        validators=[Optional()],
        render_kw={'class': 'custom-select dirty'},
    )

    test_plan = TextAreaField(
        id='test-plan',
        label='Test Plan',
        render_kw={'hidden': False, 'class': 'editor dirty', },
    )

    test_results = TextAreaField(
        id='test-results',
        label='Test Results',
        render_kw={'hidden': False, 'class': 'editor dirty', },
    )

    test_start_date = DateField(
        id='test-start-date',
        label='Test Start Date',
        validators=[Optional()],
        render_kw={'class': 'dirty picker-date', 'placeholder': 'Select date'}
    )

    test_successful = BooleanField(
        id='test-successful',
        label='Test successful?',
        render_kw={'class': 'dirty', },
    )


class StandardChangeForm(ChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.standard_template.choices = [('', '')] + [
            (el.id, f'{el.name} - {el.short_desc}') for el in
            db.session.execute(
                sa.select(ChangeTemplates)
                .order_by(ChangeTemplates.name.asc())
            ).scalars().all()
        ]

    standard_template = SelectField(
        id='standard-template',
        label='Standard Change',
        choices=[],
        validators=[Optional()],
        render_kw={'class': 'custom-select'},
    )
