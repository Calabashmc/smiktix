import uuid
from sqlalchemy import select

from ..model import db
from ..model.model_user import User  # Replace with your actual User model import

def backfill_fs_uniquifier():
    """
    Backfills the fs_uniquifier field in the User model with a unique UUID
    for each user. This is used to prevent users from being created with the
    same username.
    This is run after bulk importing users.
    """
    users_without_uniquifier = db.session.execute(
        select(User).where(User.fs_uniquifier.is_(None))
    ).scalars().all()

    for user in users_without_uniquifier:
        user.fs_uniquifier = str(uuid.uuid4())  # Generate a unique UUID for each user

    db.session.commit()

if __name__ == '__main__':
    backfill_fs_uniquifier()
