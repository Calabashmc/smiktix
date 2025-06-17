from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:  # only used for type hinting so no circular import issues
    from lookup_tables import KBATypesLookup
    from model_category import Category
    from model_notes import Notes
    from model_user import User

from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, expression
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy.event import listens_for
from . import db
from .common_methods import get_status_counts
from .lookup_tables import KBATypesLookup


class KnowledgeBase(db.Model):
    __tablename__ = 'knowledgebase'
    id: Mapped[int] = mapped_column(sa.Identity(), primary_key=True)
    ticket_number: Mapped[int] = mapped_column(
        db.Integer,
        sa.Identity(start=1000, increment=1),  # Auto-incrementing identity column
        unique=True,
        nullable=False
    )
    search_vector: Mapped[TSVectorType] = mapped_column(TSVectorType('title', 'short_desc', 'details'))
    archived_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)  # the body of the article
    expires_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    last_updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    hashtags: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)  # need this?
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True),
                                                            nullable=True)  # keep audit of all reviews?
    rating: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    review_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    service: Mapped[Optional[str]] = mapped_column(db.String(30), nullable=True)  # IMPROVEMENT: what service does the article belong to
    short_desc: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(db.String(30), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(db.String(150), nullable=True)
    ticket_type: Mapped[Optional[str]] = mapped_column(db.String(15), nullable=True)

    # relationships
    approver_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approver: Mapped['User'] = relationship(
        'User',
        foreign_keys=[approver_id],
        back_populates='articles_approved',
    )

    article_type_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('kba_types_lookup.id'))
    article_type: Mapped['KBATypesLookup'] = relationship(
        'KBATypesLookup',
        back_populates='knowledge_articles',
    )

    author_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    author: Mapped['User'] = relationship(
        'User',
        foreign_keys=[author_id],
        back_populates='articles_authored',
    )

    category_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    category: Mapped['Category'] = relationship(
        'Category',
        back_populates='knowledge_category',
    )

    created_by_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by: Mapped['User'] = relationship(
        'User',
        foreign_keys=[created_by_id],
        back_populates='articles_created',
    )

    notes: Mapped[list['Notes']] = relationship(
        'Notes',
        back_populates='knowledgebase',
        cascade='all, delete-orphan, delete',
    )

    # fields with default values
    needs_improvement: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=expression.false(), default=False)
    times_useful: Mapped[Optional[int]] = mapped_column(db.Integer, server_default='0', default=0)
    times_viewed: Mapped[Optional[int]] = mapped_column(db.Integer, server_default='0', default=0)

    def get_author_name(self):
        if self.author:
            return self.author.full_name
        else:
            return None

    def get_creator_name(self):
        if self.created_by:
            return self.created_by.full_name
        else:
            return None

    def get_title(self):
        if self.title:
            return self.title
        else:
            return None

    def get_article_type(self):
        if self.article_type:
            return self.article_type.article_type
        else:
            return None

    def get_times_viewed(self):
        if self.times_viewed:
            return self.times_viewed
        else:
            return 0

    def get_times_useful(self):
        if self.times_useful:
            return self.times_useful
        else:
            return 0

    @classmethod
    def article_type_count(cls, scope='all'):
        from .lookup_tables import KBATypesLookup

        # Determine base filter condition
        if scope == 'portal' or scope == 'published':
            base_filter = cls.status == 'published'
            count_stmt = sa.select(func.count()).select_from(cls).where(base_filter)

            stmt_counts = (
                sa.select(KBATypesLookup.id, func.count())
                .select_from(cls)
                .join(KBATypesLookup)
                .where(base_filter)
                .group_by(KBATypesLookup.id)
            )

        elif scope == 'top':
            # Get top N most-viewed published articles
            top_articles_subq = (
                sa.select(cls.id)
                .where(cls.status == 'published')
                .where(cls.times_viewed > 0)
                .order_by(cls.times_viewed.desc())
                .limit(10)  # hardcoded to 10 as this is typical. Todo make variable in config?
                .subquery()
            )

            count_stmt = sa.select(func.count()).select_from(top_articles_subq)

            article_alias = sa.orm.aliased(cls)
            stmt_counts = (
                sa.select(KBATypesLookup.id, func.count())
                .select_from(article_alias)
                .join(KBATypesLookup)
                .where(article_alias.id.in_(sa.select(top_articles_subq.c.id)))
                .group_by(KBATypesLookup.id)
            )

        else:
            # scope == 'all'
            base_filter = cls.status != 'archived'
            count_stmt = sa.select(func.count()).select_from(cls).where(base_filter)

            stmt_counts = (
                sa.select(KBATypesLookup.id, func.count())
                .select_from(cls)
                .join(KBATypesLookup)
                .where(base_filter)
                .group_by(KBATypesLookup.id)
            )

        # Execute total count
        counts_dict = {'All': db.session.execute(count_stmt).scalar()}

        # Execute grouped counts
        article_type_counts = db.session.execute(stmt_counts).all()
        for article_type_id, count in article_type_counts:
            kba_type = db.session.execute(
                sa.select(KBATypesLookup.article_type)
                .where(KBATypesLookup.id == article_type_id)
            ).scalar_one_or_none()
            counts_dict[kba_type] = count

        return counts_dict

    @classmethod
    def get_published_articles(cls):
        stmt = (
            sa.select(cls)
            .where(cls.status == 'published')
            .order_by(cls.created_at.desc())
        )

        return stmt

    @classmethod
    def get_top_useful_records(cls, limit):
        stmt = (
            sa.select(cls)
            .where(sa.and_(cls.status == 'published', cls.times_useful > 0))
            .order_by(cls.times_useful.desc())
            .limit(limit)
        )

        return stmt

    @classmethod
    def get_top_viewed_records(cls, limit=10):
        stmt = (
            sa.select(cls)
            .where(cls.status == 'published')
            .order_by(cls.times_viewed.desc())
            .limit(limit)
        )

        return stmt

    @classmethod
    def get_top_viewed_count(cls, limit=10):
        counts_dict = {}

        stmt = (
            sa.select(cls.ticket_number, cls.times_viewed.label("view_count"), cls.times_useful.label("useful_count"))
            .where(sa.and_(cls.status == 'published', cls.times_viewed > 0))
            .order_by(cls.times_viewed.desc())
            .limit(limit)
        )
        results = db.session.execute(stmt).all()
        for record_id, view_count, useful_count in results:
            counts_dict[record_id] = {'total': view_count, 'useful': useful_count}

        return counts_dict

    @classmethod
    def get_useful_count(cls):
        counts_dict = {}
        # Count the occurrences of times_useful, grouping by times_useful
        useful_kbas_count = (
            db.session.execute(
                sa.select(KBATypesLookup.article_type, sa.func.count())
                .select_from(cls)
                .join(KBATypesLookup, cls.article_type)  # Join the related table
                .where(sa.and_(cls.times_useful > 0, cls.status != 'archived'))
                .group_by(KBATypesLookup.article_type)  # Group by the related field
            ).all()
        )

        # Total count of entries not 'Archived'
        total_count = (
            db.session.execute(
                sa.select(func.count())
                .select_from(cls)
                .filter(cls.status != 'archived')
            ).scalar()
        )
        for useful_kbas_count, count in useful_kbas_count:
            counts_dict[useful_kbas_count] = count

        counts_dict['All'] = total_count
        return counts_dict

    @classmethod
    def search_published_knowledge_articles(cls, search_text, limit=20):
        # Create the search query directly
        search_query = sa.func.plainto_tsquery('english', search_text)

        stmt = (
            sa.select(cls)
            .where(cls.search_vector.op('@@')(search_query))  # Use op('@@') instead of match
            .where(cls.status == 'published')
            .order_by(sa.desc(sa.func.ts_rank(cls.search_vector, search_query)))
            .limit(limit)
        )

        return db.session.execute(stmt).scalars().all()

    @classmethod
    def ticket_status_counts(cls, scope):
        return get_status_counts(cls, scope)

    def update_search_vector(self):
        self.search_vector = sa.func.to_tsvector(
            'english',
            ' '.join(filter(None, [self.title, self.short_desc, self.details, self.hashtags]))
        )

# Update search_vector before insert or update this function outside the class
@listens_for(KnowledgeBase, 'before_insert')
@listens_for(KnowledgeBase, 'before_update')
def update_search_vector_before_insert_or_update(_, __, target):
    # _ and __ represent unused arguments mapper, connection
    target.update_search_vector()
