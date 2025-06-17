from flask_wtf import FlaskForm
import sqlalchemy as sa
from wtforms import StringField, BooleanField, SelectField, SelectMultipleField, PasswordField, TimeField, TelField, \
    EmailField
from wtforms.fields.datetime import DateTimeLocalField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import InputRequired, NumberRange, EqualTo, Optional

from ..change.form import ChangeForm
from ..cmdb.form import CmdbForm, CmdbSoftwareForm, CmdbHardwareForm, CmdbServiceForm
from ..idea.form import IdeasForm
from ..interaction.form import InteractionForm
from ..knowledge.form import KnowledgeForm
from ..release.form import ReleaseForm
from ...common.forms import BaseMixin, UserDetailsMixin
from ...model import db
from ...model.lookup_tables import StatusLookup, ModelLookup
from ...model.model_user import Department, Team, Role, User
from ...model.relationship_tables import user_roles, status_model


class AdminUserForm(UserDetailsMixin, FlaskForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.department_id.choices = [(0, '')] + [
            (el.id, el.name)
            for el in db.session.execute(
                sa.select(Department)
                .order_by(Department.name.asc())
            ).scalars().all()
        ]
        self.team_id.choices = [('', '')] + [
            (el.id, el.name)
            for el in db.session.execute(
                sa.select(Team)
                .order_by(Team.name.asc())
            ).scalars().all()
        ]
        self.role_id.choices = [(0, '')] + [
            (el.id, el.name)
            for el in db.session.execute(
                sa.select(Role)
                .order_by(Role.name.asc())
            ).scalars().all()
        ]

        self.manager_id.choices = [('', '')] + [
            (el.id, el.full_name)
            for el in db.session.execute(
                sa.select(User)
                .join(user_roles, User.id == user_roles.c.user_id)
                .join(Role, Role.id == user_roles.c.role_id)
                .where(Role.name == 'manager')
                .order_by(User.full_name.asc())
            ).scalars().all()
        ]

    active = BooleanField(label='Active', id='active', default=True)

    department_id = SelectField(label='Department',
                                id='department',
                                coerce=int,
                                render_kw={'class': 'custom-select'},
                                validators=[InputRequired(message='Department is required')]
                                )

    email = StringField(label='Email',
                        id='email',
                        validators=[InputRequired(message='Email is required')]
                        )

    first_name = StringField(label='First Name',
                             id='first-name',
                             validators=[InputRequired(message='First name is required')]
                             )

    full_name = StringField(label='Full Name',
                            id='full-name',
                            validators=[InputRequired(message='Full name is required')]
                            )

    last_name = StringField(label='Last Name',
                            id='last-name',
                            validators=[InputRequired(message='Last name is required')]
                            )

    manager_id = SelectField(label='Manager', id='manager', render_kw={'class': 'custom-select'})

    occupation = StringField(label='Occupation',
                             id='occupation',
                             validators=[InputRequired(message='Occupation is required')]
                             )

    password = PasswordField(
        label='Password',
        id='password',
        validators=[Optional()]
    )

    confirm_password = PasswordField(
        label='Confirm Password',
        id='confirm-password',
        validators=[Optional(), EqualTo('password')]
    )

    phone = StringField(
        label='Phone',
        id='phone',
    )

    role_id = SelectMultipleField(
        label='Role(s)',
        id='role',
        coerce=int,
        render_kw={'class': 'custom-multi-select'}
    )

    short_desc = None

    team_id = SelectField(
        label='Team',
        id='team',
        render_kw={'class': 'custom-select'},
        validators=[InputRequired(message='Team is required')]
    )

    username = StringField(
        label='Username',
        id='username',
        validators=[InputRequired(message='Username is required')]
    )


class AdminAppDefaultsForm(UserDetailsMixin, BaseMixin):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.model.choices = [('', '')] + [
            (el.id, el.name)
            for el in db.session.execute(
                sa.select(ModelLookup)
            ).scalars().all()
        ]

        self.status.choices = [('', '')] + [
            (el.id, el.status)
            for el in db.session.execute(
                sa.select(StatusLookup)
                .order_by(StatusLookup.status.asc())
            ).scalars().all()
        ]

        self.support_team_default_id.choices = [(0, '')] + [
            (el.id, el.name)
            for el in db.session.execute(
                sa.select(Team)
                .order_by(Team.name.asc())
            ).scalars().all()
        ]

    address = StringField(
        label='Address',
        id='address',
        validators=[InputRequired(message='Address is required')]
    )

    change_default_risk = SelectField(
        label='Change Default Risk',
        id='change-default-risk',
        choices=[('CR1', 'CR1'), ('CR2', 'CR2'), ('CR3', 'CR3'), ('CR4', 'CR4'),
                 ('CR5', 'CR5')],
        render_kw={'class': 'custom-select'},
        validators=[InputRequired(message='Change Default Risk is required')]
    )

    change_resolution_code = StringField(
        label='Resolution Code',
        id='change-resolution-code',
    )

    change_resolution_comment = StringField(
        label='Resolution Description',
        id='change-resolution-comment',
    )

    change_window_day = SelectField(
        label='Day',
        id='change-window-day',
        choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
                 ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'),
                 ('Sunday', 'Sunday')],
        render_kw={'class': 'custom-select'},
        validators=[InputRequired(message='Change Window Day is required')]
    )

    change_window_start = TimeField(
        label='Start',
        id='change-window-start',
        validators=[InputRequired(message='Change Window Start is required')]
    )

    change_window_duration = IntegerField(
        label='Duration',
        id='change-window-duration',
        validators=[InputRequired(message='Change Window Duration is required')]
    )

    close_day = SelectField(
        label='Close Day',
        id='close-day',
        choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
                 ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'),
                 ('Sunday', 'Sunday')],
        render_kw={'class': 'custom-select'},
        validators=[InputRequired(message='Close Day is required')]
    )

    close_hour = TimeField(
        label='Close Hour',
        id='close-hour',
        validators=[InputRequired(message='Close Hour is required')]
    )

    country_name = StringField(
        label='Country',
        id='country-name',
        validators=[InputRequired(message='Country Name is required')]
    )

    idea_resolution_code = StringField(
        label='Resolution Code',
        id='idea-resolution-code',
    )

    idea_resolution_comment = StringField(
        label='Resolution Description',
        id='idea-resolution-comment',
    )

    incident_default_impact = SelectField(
        label='Incident Default Impact',
        id='incident-default-impact',
        choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')],
        render_kw={'class': 'custom-select'},
        validators=[InputRequired(message='Incident Default Impact is required')]
    )

    incident_default_priority = StringField(
        label='Incident Default Priority',
        id='incident-default-priority',
        render_kw={'class': 'readonly'},
        validators=[InputRequired(message='Incident Default Priority is required')]
    )

    incident_default_urgency = SelectField(
        label='Incident Default Urgency',
        id='incident-default-urgency',
        choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')],
        render_kw={'class': 'custom-select'},
        validators=[InputRequired(message='Incident Default Urgency is required')]
    )

    kba_type = StringField(
        label='Knowledge Type',
        id='kba-type',
    )

    location = StringField(
        label='Location',
        id='location',
        validators=[InputRequired(message='Location is required')]
    )

    model = SelectField(
        label='Model',
        id='model',
        choices=[],
        render_kw={'class': 'custom-select'},
    )

    open_hour = TimeField(
        label='Open Hour',
        id='open-hour',
        validators=[InputRequired(message='Open Hour is required')]
    )

    office_timezone = StringField(
        label='Timezone',
        id='office-timezone',
        validators=[InputRequired(message='Timezone is required')]
    )

    problem_default_priority = SelectField(
        label='Problem Default Priority',
        id='problem-default-priority',
        choices=[('P1', 'P1'), ('P2', 'P2'), ('P3', 'P3'), ('P4', 'P4'),
                 ('P5', 'P5')],
        render_kw={'class': 'custom-select'},
        validators=[InputRequired(message='Problem Default Priority is required')]
    )

    problem_resolution_code = StringField(
        label='Resolution Code',
        id='problem-resolution-code',
    )

    problem_resolution_comment = StringField(
        label='Resolution Description',
        id='problem-resolution-comment',
    )

    priority = StringField(
        label='Priority',
        id='priority',
        validators=[InputRequired(message='Priority is required')]
    )

    province = StringField(
        label='Province',
        id='province',
        validators=[InputRequired(message='Province is required')]
    )

    resolution_code = StringField(
        label='Resolution Code',
        id='resolution-code',
    )

    resolution_comment = StringField(
        label='Resolution Description',
        id='resolution-comment',
    )

    respond_by = IntegerField(
        label='Respond By',
        id='respond-by')  # response time in minutes e.g. created time + this many minutes

    resolve_by = IntegerField(
        label='Resolve By',
        id='resolve-by')

    servicedesk_email = EmailField(
        label='Service Desk Email',
        id='servicedesk-email',
        validators=[InputRequired(message='Service Desk Email is required')]
    )

    servicedesk_phone = TelField(
        label='Service Desk Phone',
        id='servicedesk-phone',
        validators=[InputRequired(message='Service Desk Phone is required')],
        render_kw={'class': 'dirty'}
    )

    source = StringField(
        label='Source',
        id='source',
    )

    state = StringField(
        label='State',
        id='state',
    )

    status = SelectField(
        label='Status',
        id='status',
        choices=[],
        render_kw={'class': 'custom-select'},
    )

    support_team_default_id = SelectField(
        label='Support Team',
        id='support-team-default-id',
        choices=[],
        coerce=int,
        render_kw={'class': 'custom-select'},
        validators=[InputRequired(message='A default Support Team is required')]
    )

    timezone = StringField(
        label='Timezone',
        id='timezone',
        validators=[InputRequired(message='Timezone is required')]
    )

    twentyfour_seven = BooleanField(
        label='24/7?',
        id='twentyfour-seven'
    )


class AdminInteractionForm(InteractionForm):  # order matters,  must be first
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.status_select.choices = [('', '')] + [
            (el.status, el.status)
            for el in db.session.execute(
                sa.select(StatusLookup)
                .join(status_model)
                .join(ModelLookup)
                .where(ModelLookup.name == "Interaction")
                .order_by(StatusLookup.status.asc())
            ).scalars().all()
        ]

    respond_by = DateTimeLocalField(
        label='Respond By',
        id='respond-by',
    )

    resolve_by = DateTimeLocalField(
        label='Resolve By',
        id='resolve-by',
        render_kw={'class': 'readonly'},
    )

    # used on admin form to present a select input to be able to change the set status
    status_select = SelectField(
        id='status-select',
        label='Status',
        choices=[],
        render_kw={'class': 'custom-select dirty'}
    )

    is_major = BooleanField(label='Is Major?', id='is-major')


class AdminChangeForm(ChangeForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.status_select.choices = [('', '')] + [
            (el.status, el.status)
            for el in db.session.execute(
                sa.select(StatusLookup)
                .join(status_model)
                .join(ModelLookup)
                .where(ModelLookup.name == "Change")
                .order_by(StatusLookup.status.asc())
            ).scalars().all()
        ]

    risk_calc = StringField(
        label='Risk Calc',
        id='risk-calc',
        render_kw={'class': 'readonly'}
    )

    status_select = SelectField(
        id='status-select',
        label='Status',
        choices=[],
        render_kw={'class': 'custom-select dirty'}
    )


class AdminReleaseForm(ReleaseForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.status_select.choices = [('', '')] + [
            (el.status, el.status)
            for el in db.session.execute(
                sa.select(StatusLookup)
                .join(status_model)
                .join(ModelLookup)
                .where(ModelLookup.name == "Release")
                .order_by(StatusLookup.status.asc())
            ).scalars().all()
        ]

    status_select = SelectField(
        id='status-select',
        label='Status',
        choices=[],
        render_kw={'class': 'custom-select dirty'}
    )

class AdminKnowledgeForm(KnowledgeForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.status_select.choices = [('', '')] + [
            (el.status, el.status)
            for el in db.session.execute(
                sa.select(StatusLookup)
                .join(status_model)
                .join(ModelLookup)
                .where(ModelLookup.name == "Knowledge")
                .order_by(StatusLookup.status.asc())
            ).scalars().all()
        ]

    status_select = SelectField(
        id='status-select',
        label='Status',
        choices=[],
        render_kw={'class': 'custom-select dirty'}
    )

    times_useful = IntegerField(
        id='times-useful',
        default=0,
        validators=[NumberRange(min=0)],
        render_kw={'class': 'dirty', 'style': 'width: 50px;'},
    )

    times_viewed = IntegerField(
        id='times-viewed',
        default=0,
        validators=[NumberRange(min=0)],
        render_kw={'class': 'dirty', 'style': 'width: 50px;'},
    )


class AdminIdeasForm(IdeasForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.status_select.choices = [('', '')] + [
            (el.status, el.status)
            for el in db.session.execute(
                sa.select(StatusLookup)
                .join(status_model)
                .join(ModelLookup)
                .where(ModelLookup.name == "Idea")
                .order_by(StatusLookup.status.asc())
            ).scalars().all()
        ]

    status_select = SelectField(
        id='status-select',
        label='Status',
        choices=[],
        render_kw={'class': 'custom-select dirty'}
    )


class AdminCmdbForm(CmdbForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.status_select.choices = [('', '')] + [
            (el.status, el.status)
            for el in db.session.execute(
                sa.select(StatusLookup)
                .join(status_model)
                .join(ModelLookup)
                .where(ModelLookup.name == "Cmdb")
                .order_by(StatusLookup.status.asc())
            ).scalars().all()
        ]

    status_select = SelectField(
        id='status-select',
        label='Status',
        choices=[],
        render_kw={'class': 'custom-select dirty'}
    )


class AdminCmdbHardwareForm(CmdbHardwareForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.status_select.choices = [('', '')] + [
            (el.status, el.status)
            for el in db.session.execute(
                sa.select(StatusLookup)
                .join(status_model)
                .join(ModelLookup)
                .where(ModelLookup.name == "CmdbHardware")
                .order_by(StatusLookup.status.asc())
            ).scalars().all()
        ]

    status_select = SelectField(
        id='status-select',
        label='Status',
        choices=[],
        render_kw={'class': 'custom-select dirty'}
    )


class AdminCmdbServiceForm(CmdbServiceForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.status_select.choices = [('', '')] + [
            (el.status, el.status)
            for el in db.session.execute(
                sa.select(StatusLookup)
                .join(status_model)
                .join(ModelLookup)
                .where(ModelLookup.name == "CmdbService")
                .order_by(StatusLookup.status.asc())
            ).scalars().all()
        ]

    status_select = SelectField(
        id='status-select',
        label='Status',
        choices=[],
        render_kw={'class': 'custom-select dirty'}
    )

class AdminCmdbSoftwareForm(CmdbSoftwareForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.status_select.choices = [('', '')] + [
            (el.status, el.status)
            for el in db.session.execute(
                sa.select(StatusLookup)
                .join(status_model)
                .join(ModelLookup)
                .where(ModelLookup.name == "CmdbSoftware")
                .order_by(StatusLookup.status.asc())
            ).scalars().all()
        ]

    status_select = SelectField(
        id='status-select',
        label='Status',
        choices=[],
        render_kw={'class': 'custom-select dirty'}
    )