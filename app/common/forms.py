import os
from datetime import datetime, timezone

from flask import current_app, url_for
from flask_wtf import FlaskForm
import sqlalchemy as sa
from wtforms import (
    DateField,
    DateTimeField,
    StringField,
    SelectField,
    DateTimeLocalField,
    SelectMultipleField,
    TextAreaField,
    TimeField,
    widgets,
)

from wtforms.fields.numeric import IntegerField
from wtforms.validators import Optional, InputRequired, DataRequired
from wtforms.widgets import TextInput

from ..model import db
from ..model.model_user import User, Team


# custom fields for MultipleCheckboxField and Textinput for air-datetime picker
class MultipleCheckboxField(SelectMultipleField):
    def __init__(self, *args, **kwargs):
        super(MultipleCheckboxField, self).__init__(*args, **kwargs)

    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class DateTimeTextField(DateTimeField):
    widget = TextInput()


class DateTextField(DateField):
    widget = TextInput()


class TimeTextField(TimeField):
    widget = TextInput()


class BaseMixin(FlaskForm):
    """
    Base mixin with fields used on all forms
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.created_by_id.choices = [("", "")] + [
            (el.id, el.full_name)
            for el in
            db.session.execute(
                sa.select(User)
                .where(User.active == True)
                .order_by(User.username.asc())
            ).scalars().all()
        ]

    category_id = SelectField(
        id='category-id',
        label='Category',
        choices=[],
        validate_choice=True,
        validators=[DataRequired()],
        render_kw={'class': 'custom-select dirty', 'placeholder': 'Select...'},
    )

    created_at = DateTimeLocalField(
        id='created-at',
        label='Created',
        default=lambda: datetime.now(timezone.utc),
        format='%Y-%m-%dT%H:%M',  # Define the ISO 8601 format
        render_kw={'class': 'no-border form-control-plaintext', 'readonly': True},
    )

    created_by_id = SelectField(
        id="created-by",
        label="Created by",
        choices=[],
        validate_choice=False,
        render_kw={"class": "custom-select owner dirty", "readonly": True},
    )

    closed_at = DateTimeLocalField(
        id='closed-at',
        label='Closed at',
        validators=[Optional()],
        render_kw={'readonly': True},
        format='%H:%M on %d/%m/%Y',
    )

    comms_email_addresses = StringField(
        id='comms-email',
        label='To: ',
        render_kw={'readonly': True}
    )

    comms_journal = TextAreaField(
        id='comms-journal',
        render_kw={'class': 'editor'}
    )

    details = TextAreaField(
        label='Details',
        id='details',
        render_kw={'hidden': False, 'class': 'editor dirty', },
    )

    email_subject = StringField(
        id='email-subject',
        label='Subject',
        render_kw={'placeholder': 'A message from the IT Service Desk...'},
    )

    # input for timeline
    journal = TextAreaField(
        id='journal',
        render_kw={'hidden': True},
    )

    last_updated_at = DateTimeLocalField(
        id='last-updated-at',
        label='Last updated:',
        validators=[Optional()],
        render_kw={'readonly': True},
        format='%Y-%m-%dT%H:%M',  # Define the ISO 8601 format,
    )
    resolution_code_id = SelectField(
        id='resolution-code-id',
        label='Resolution Code',
        choices=[],
        validators=[Optional()],
        validate_choice=False,
    )

    resolution_code_text = StringField(id="resolution-code-text")

    resolution_notes = TextAreaField(
        id="resolution-notes",
        render_kw={"class": "editor"}
    )

    resolution_journal = TextAreaField(
        id="resolution-journal",
        render_kw={"class": "editor journal-editor"}
    )

    resolved_at = DateTimeLocalField(
        id="resolved-at",
        label="Resolved at",
        validators=[Optional()],
        render_kw={"readonly": True},
    )

    short_desc = StringField(
        label="Short Description",
        id="short-desc",
        validators=[InputRequired()],
        render_kw={"class": "dirty"}
    )

    # used on most forms to display the set status
    status: StringField = StringField(
        id="status",
        label="status",
        default="new",
        render_kw={"hidden": True, "class": "dirty", "form": "form"}
    )

    ticket_number = IntegerField(
        label="ticket #",
        id="ticket-number",
        validators=[Optional()],  # because set at db level
        render_kw={"readonly": True, "class": "number-no-border", "form": "form"},
    )

    ticket_type = StringField(
        label="Type",
        id="ticket-type",
        render_kw={"readonly": True, "class": "type-no-border", "form": "form"},
    )

    # input for editor
    worklog = TextAreaField(
        render_kw={"class": "editor"}
    )


class UserDetailsMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def select_icon():
            icons_folder = 'users'
            # Get the path to the static folder using Flask's app context
            static_folder = current_app.static_folder
            icons_folder_path = os.path.join(static_folder, 'images', icons_folder)

            icon_files = os.listdir(icons_folder_path)
            # Construct URLs for each image file
            image_urls = [url_for('static', filename=f'images/{icons_folder}/{file}') for file in icon_files]

            # Create tuples with (full URL, filename) for choices
            choices = [(url, os.path.basename(url)) for url in image_urls]
            # Sort choices alphabetically by the filename
            choices.sort(key=lambda x: x[1])
            return choices

        self.avatar.choices = [('', '')] + select_icon()

    avatar = SelectField(
        id='avatar',
        choices=[],
        render_kw={'class': 'dirty custom-select', 'form': 'form'}
    )

    department = StringField(
        label="Department",
        default="Department unknown",
        render_kw={"readonly": True, "class": "no-border"},
    )

    email = StringField(
        label="Email",
        default="Email unknown",
        render_kw={"readonly": True, "class": "no-border"},
    )

    occupation = StringField(
        label="Occupation",
        default="Occupation unknown",
        render_kw={"readonly": True, "class": "no-border"},
    )

    phone = StringField(
        label="Phone",
        default="Phone unknown",
        render_kw={"readonly": True, "class": "no-border"},
    )


class RequesterMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.requester_id.choices = [("", "")] + [
            (el.id, el.full_name)
            for el in
            db.session.execute(
                sa.select(User)
                .where(User.active == True)
                .order_by(User.username.asc())
            ).scalars().all()
        ]

    requester_id = SelectField(
        id="requested-by",
        label="Requested by",
        choices=[],
        validate_choice=False,
        validators=[InputRequired()],
        render_kw={"class": "custom-select owner dirty", "placeholder": "Select..."},
    )


class SupportTeamMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.support_team_id.choices = [("", "")] + [
            (el.id, el.name) for el in
            db.session.execute(
                sa.select(Team)
                .order_by(Team.name.asc())
            ).scalars().all()
        ]

    support_team_id = SelectField(id="support-team",
                                  label="Support Team",
                                  choices=[],
                                  validate_choice=False,
                                  validators=[DataRequired()],
                                  render_kw={"class": "custom-select dirty", }
                                  )

    supporter_id = SelectField(
        id="support-agent",
        label="Support Agent",
        choices=[],
        validate_choice=False,
        validators=[Optional()],
        render_kw={"class": "custom-select dirty"}
    )
