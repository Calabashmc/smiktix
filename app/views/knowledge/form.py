from datetime import datetime, timedelta, timezone
from flask_wtf import FlaskForm
from sqlalchemy import select
from wtforms.fields.numeric import IntegerField
from wtforms import (
    BooleanField,
    DateTimeField,
    DateTimeLocalField,
    SelectField,
    StringField,
)
from wtforms.fields.simple import TextAreaField
from wtforms.validators import InputRequired, Optional
from ...common.forms import UserDetailsMixin, BaseMixin
from ...model import db
from ...model.model_category import Category
from ...model.lookup_tables import KBATypesLookup, ModelLookup
from ...model.model_user import User
from ...model.relationship_tables import category_model


class KnowledgeForm(UserDetailsMixin, BaseMixin):
    def __init__(self, *args, **kwargs):
        super(KnowledgeForm, self).__init__(*args, **kwargs)

        self.article_type_id.choices = [('', '')] + [
            (el.id, el.article_type)
            for el in
            db.session.execute(
                select(KBATypesLookup)
                .order_by(KBATypesLookup.article_type.asc())
            ).scalars().all()
        ]

        self.author_id.choices = [('', '')] + [
            (el.id, el.full_name)
            for el in
            db.session.execute(
                select(User)
                .where(User.active == True)
                .order_by(User.username.asc())
            ).scalars().all()
        ]

        self.category_id.choices = [('', '')] + [
            (el.id, el.name)
            for el in db.session.execute(
                select(Category)
                .join(category_model)  # Join the association table
                .join(ModelLookup)  # Join the ModelLookup table
                .where(ModelLookup.name == 'Knowledge')  # Filter for the desired name
            ).scalars().all()
        ]

    archived_at = DateTimeField(
        id='archived-at',
        label='Archived',
        format='%Y-%m-%dT%H:%M',
        validators=[Optional()],
        render_kw={'class': 'no-border'}
    )

    article_type_id = SelectField(
        id='article-type',
        label='Article Type',
        validators=[InputRequired()],
        render_kw={'class': 'dirty custom-select'},
    )

    author_id = SelectField(
        id='author-id',
        label='Author',
        choices=[],
        validate_choice=False,
        validators=[InputRequired()],
        render_kw={'class': 'custom-select owner dirty'}
    )

    expires_at = DateTimeLocalField(
        id='expires-at',
        label='Expires',
        default=lambda: datetime.now(timezone.utc) + timedelta(days=365),
        format='%Y-%m-%d %H:%M',
        render_kw={'class': 'picker-datetime dirty'}
    )

    hashtags = TextAreaField(
        id='hashtags',
        label='Hashtags (comma seperated)',
        render_kw={'class': 'dirty'}
    )

    needs_improvement = BooleanField(
        id='needs-improvement',
        label='Needs Improvement',
        render_kw={'class': 'dirty'},
    )


    review_at = DateTimeLocalField(
        id='review-at',
        label='Review Due',
        default=lambda: datetime.now(timezone.utc) + timedelta(days=180),
        format='%Y-%m-%d %H:%M',
        render_kw={'class': 'picker-datetime dirty'}
    )

    reviewed_at = DateTimeLocalField(
        id='reviewed-at',
        label='Reviewed',
        format='%Y-%m-%dT%H:%M',
        validators=[Optional()],
        render_kw={'class': 'no-border'}
    )

    times_useful = IntegerField(
        id='times-useful',
        default=0,
        render_kw={'readonly': True, 'class': 'no-border'}
    )

    times_viewed = IntegerField(
        id='times-viewed',
        default=0,
        render_kw={'readonly': True, 'class': 'no-border'}
    )

    published_at = DateTimeLocalField(
        id='published-at',
        label='Published',
        format='%Y-%m-%dT%H:%M',
        render_kw={'class': 'no-border'}
    )

    title = StringField(
        id='title',
        label='Title',
        validators=[InputRequired()],
        render_kw={'class': 'dirty'},
    )
