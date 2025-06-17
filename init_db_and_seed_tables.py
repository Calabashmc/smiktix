import time
from flask_migrate import upgrade
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app import create_app
from app.model import db
from seed import seed_data

app = create_app('production')
with app.app_context():
    print("Upgrading database with Alembic ...")
    upgrade()  # This is equivalent to `flask db upgrade`
    print("✅ Database upgraded!")
    print("Seeding database ...")
    seed_data()
    print("✅ Database seeded!")
